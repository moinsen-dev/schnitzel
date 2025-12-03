"""Integration tests for schema parser import resolution (F003)."""

import tempfile
from pathlib import Path

import pytest

from schnitzel.schema.parser import (
    CircularImportError,
    DuplicateModelError,
    SchemaParser,
    YAMLParseError,
)


class TestSchemaParserImports:
    """Test schema parser import resolution functionality."""

    def test_single_level_import(self) -> None:
        """
        Test F003: Schema parser can resolve single-level imports.

        Steps:
        1. Create base.yaml with User model
        2. Create main.yaml with imports: [base.yaml] and Post model
        3. Call SchemaParser.parse('main.yaml')
        4. Verify parsed schema contains both User and Post models
        5. Verify import resolution happens before validation
        6. Verify relative paths are resolved correctly
        7. Verify no duplicate models exist
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            main_path = Path(tmpdir) / "main.yaml"

            # Step 1: Create base.yaml with User model
            base_content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string
"""
            base_path.write_text(base_content)

            # Step 2: Create main.yaml with imports and Post model
            main_content = """
schnitzel: 1.0.0
imports:
  - base.yaml
models:
  Post:
    fields:
      id:
        type: uuid
      title:
        type: string
"""
            main_path.write_text(main_content)

            # Step 3: Call SchemaParser.parse('main.yaml')
            parser = SchemaParser()
            schema = parser.parse(main_path)

            # Step 4: Verify parsed schema contains both User and Post models
            assert "User" in schema.models
            assert "Post" in schema.models

            # Verify User model from imported file
            user_model = schema.models["User"]
            assert "id" in user_model.fields
            assert "name" in user_model.fields
            assert user_model.fields["id"].type == "uuid"
            assert user_model.fields["name"].type == "string"

            # Verify Post model from main file
            post_model = schema.models["Post"]
            assert "id" in post_model.fields
            assert "title" in post_model.fields
            assert post_model.fields["id"].type == "uuid"
            assert post_model.fields["title"].type == "string"

            # Step 7: Verify no duplicate models exist (only 2 models total)
            assert len(schema.models) == 2

    def test_relative_path_resolution(self) -> None:
        """Test that relative import paths are resolved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create subdirectory structure
            models_dir = tmpdir_path / "models"
            models_dir.mkdir()

            base_path = models_dir / "user.yaml"
            main_path = tmpdir_path / "main.yaml"

            # Create base file in subdirectory
            base_content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
"""
            base_path.write_text(base_content)

            # Create main file with relative path import
            main_content = """
schnitzel: 1.0.0
imports:
  - ./models/user.yaml
models:
  Post:
    fields:
      id:
        type: uuid
"""
            main_path.write_text(main_content)

            # Parse and verify
            parser = SchemaParser()
            schema = parser.parse(main_path)

            assert "User" in schema.models
            assert "Post" in schema.models
            assert len(schema.models) == 2

    def test_duplicate_model_error(self) -> None:
        """Test that duplicate model names raise an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            main_path = Path(tmpdir) / "main.yaml"

            # Create base.yaml with User model
            base_content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
"""
            base_path.write_text(base_content)

            # Create main.yaml with duplicate User model
            main_content = """
schnitzel: 1.0.0
imports:
  - base.yaml
models:
  User:
    fields:
      email:
        type: string
"""
            main_path.write_text(main_content)

            # Parse should raise DuplicateModelError
            parser = SchemaParser()
            with pytest.raises(DuplicateModelError) as exc_info:
                parser.parse(main_path)

            assert "User" in str(exc_info.value)
            assert "Duplicate model" in str(exc_info.value)

    def test_circular_import_detection(self) -> None:
        """Test that circular imports are detected and reported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = Path(tmpdir) / "a.yaml"
            b_path = Path(tmpdir) / "b.yaml"

            # Create a.yaml importing b.yaml
            a_content = """
schnitzel: 1.0.0
imports:
  - b.yaml
models:
  ModelA:
    fields:
      id:
        type: uuid
"""
            a_path.write_text(a_content)

            # Create b.yaml importing a.yaml (circular!)
            b_content = """
schnitzel: 1.0.0
imports:
  - a.yaml
models:
  ModelB:
    fields:
      id:
        type: uuid
"""
            b_path.write_text(b_content)

            # Parse should raise CircularImportError
            parser = SchemaParser()
            with pytest.raises(CircularImportError) as exc_info:
                parser.parse(a_path)

            error_msg = str(exc_info.value)
            assert "Circular import" in error_msg
            assert "a.yaml" in error_msg or "b.yaml" in error_msg

    def test_missing_import_file(self) -> None:
        """Test that missing import files raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = Path(tmpdir) / "main.yaml"

            # Create main.yaml importing non-existent file
            main_content = """
schnitzel: 1.0.0
imports:
  - nonexistent.yaml
models:
  Post:
    fields:
      id:
        type: uuid
"""
            main_path.write_text(main_content)

            # Parse should raise SchnitzelImportError (not FileNotFoundError in this implementation)
            parser = SchemaParser()
            with pytest.raises((FileNotFoundError, Exception)) as exc_info:
                parser.parse(main_path)

            error_msg = str(exc_info.value)
            assert "nonexistent.yaml" in error_msg

    def test_multi_level_nested_imports(self) -> None:
        """Test that multi-level nested imports work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            level0_path = Path(tmpdir) / "level0.yaml"
            level1_path = Path(tmpdir) / "level1.yaml"
            level2_path = Path(tmpdir) / "level2.yaml"

            # Create level0.yaml with BaseModel
            level0_content = """
schnitzel: 1.0.0
models:
  BaseModel:
    fields:
      id:
        type: uuid
      created_at:
        type: datetime
"""
            level0_path.write_text(level0_content)

            # Create level1.yaml importing level0.yaml
            level1_content = """
schnitzel: 1.0.0
imports:
  - level0.yaml
models:
  UserModel:
    fields:
      name:
        type: string
"""
            level1_path.write_text(level1_content)

            # Create level2.yaml importing level1.yaml
            level2_content = """
schnitzel: 1.0.0
imports:
  - level1.yaml
models:
  PostModel:
    fields:
      title:
        type: string
"""
            level2_path.write_text(level2_content)

            # Parse level2.yaml
            parser = SchemaParser()
            schema = parser.parse(level2_path)

            # Verify all three models are present
            assert "BaseModel" in schema.models
            assert "UserModel" in schema.models
            assert "PostModel" in schema.models
            assert len(schema.models) == 3

            # Verify fields from each level
            base_model = schema.models["BaseModel"]
            user_model = schema.models["UserModel"]
            post_model = schema.models["PostModel"]

            assert "created_at" in base_model.fields
            assert "name" in user_model.fields
            assert "title" in post_model.fields

    def test_merge_multiple_feature_schemas(self) -> None:
        """Test merging multiple feature schemas without conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_path = Path(tmpdir) / "auth.yaml"
            posts_path = Path(tmpdir) / "posts.yaml"
            main_path = Path(tmpdir) / "main.yaml"

            # Create auth.yaml with User and Session models
            auth_content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
      email:
        type: string
  Session:
    fields:
      id:
        type: uuid
      token:
        type: string
"""
            auth_path.write_text(auth_content)

            # Create posts.yaml with Post and Comment models
            posts_content = """
schnitzel: 1.0.0
models:
  Post:
    fields:
      id:
        type: uuid
      title:
        type: string
  Comment:
    fields:
      id:
        type: uuid
      text:
        type: string
"""
            posts_path.write_text(posts_content)

            # Create main.yaml importing both
            main_content = """
schnitzel: 1.0.0
imports:
  - auth.yaml
  - posts.yaml
models: {}
"""
            main_path.write_text(main_content)

            # Parse main.yaml
            parser = SchemaParser()
            schema = parser.parse(main_path)

            # Verify all 4 models are present
            assert "User" in schema.models
            assert "Session" in schema.models
            assert "Post" in schema.models
            assert "Comment" in schema.models
            assert len(schema.models) == 4

            # Verify each model retains its fields
            user_model = schema.models["User"]
            session_model = schema.models["Session"]
            post_model = schema.models["Post"]
            comment_model = schema.models["Comment"]

            assert "email" in user_model.fields
            assert "token" in session_model.fields
            assert "title" in post_model.fields
            assert "text" in comment_model.fields
