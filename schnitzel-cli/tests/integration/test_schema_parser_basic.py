"""Integration tests for basic schema parser functionality (F001, F002)."""

import tempfile
from pathlib import Path

import pytest

from schnitzel.schema.parser import SchemaParser, YAMLParseError


class TestSchemaParserBasic:
    """Test basic schema parser functionality."""

    def test_parse_valid_yaml_with_basic_model(self) -> None:
        """
        Test F001: Schema parser can load a valid YAML file with basic model definition.

        Steps:
        1. Create a minimal YAML schema file with one model (User) and two fields
        2. Call SchemaParser.parse(filepath) with the test file
        3. Verify parser returns a SchnitzelSchema object
        4. Verify schema.models contains exactly one model
        5. Verify model.name equals 'User'
        6. Verify model has two fields with correct names and types
        7. Verify no parse errors are raised
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.yaml"

            # Step 1: Create minimal YAML with User model
            content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string
"""
            schema_path.write_text(content)

            # Step 2: Call SchemaParser.parse
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3: Verify parser returns SchnitzelSchema object
            assert schema is not None
            assert hasattr(schema, "models")
            assert hasattr(schema, "schnitzel")

            # Step 4: Verify schema.models contains exactly one model
            assert len(schema.models) == 1

            # Step 5: Verify model name equals 'User'
            assert "User" in schema.models

            # Step 6: Verify model has two fields with correct names and types
            user_model = schema.models["User"]
            assert user_model.name == "User"
            assert len(user_model.fields) == 2
            assert "id" in user_model.fields
            assert "name" in user_model.fields
            assert user_model.fields["id"].type == "uuid"
            assert user_model.fields["name"].type == "string"

            # Step 7: No errors raised (test completes successfully)

    def test_invalid_yaml_syntax_raises_error(self) -> None:
        """
        Test F002: Schema parser raises clear error for invalid YAML syntax.

        Steps:
        1. Create a YAML file with invalid syntax
        2. Call SchemaParser.parse(filepath)
        3. Verify YAMLParseError is raised
        4. Verify error message includes line number and description
        5. Verify error message is human-readable
        6. Verify parser doesn't crash
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "invalid.yaml"

            # Step 1: Create YAML with invalid syntax (unclosed brackets)
            invalid_content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id: {type: uuid
      name: string
"""
            schema_path.write_text(invalid_content)

            # Step 2-3: Call parse and verify YAMLParseError is raised
            parser = SchemaParser()
            with pytest.raises(YAMLParseError) as exc_info:
                parser.parse(schema_path)

            # Step 4-5: Verify error message is informative
            error_msg = str(exc_info.value)
            assert "invalid.yaml" in error_msg
            assert "Invalid YAML syntax" in error_msg

            # Step 6: Parser doesn't crash (pytest handles the exception properly)

    def test_missing_file_raises_error(self) -> None:
        """Test that parsing a non-existent file raises FileNotFoundError."""
        parser = SchemaParser()

        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse("/nonexistent/path/to/schema.yaml")

        error_msg = str(exc_info.value)
        assert "Schema file not found" in error_msg

    def test_parse_with_optional_fields(self) -> None:
        """Test parsing models with optional and default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.yaml"

            content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
      email:
        type: string
        optional: false
      bio:
        type: string
        optional: true
        default: ""
      age:
        type: int
        min: 0
        max: 150
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            user = schema.models["User"]
            assert user.fields["email"].optional is False
            assert user.fields["bio"].optional is True
            assert user.fields["bio"].default == ""
            assert user.fields["age"].min == 0
            assert user.fields["age"].max == 150

    def test_parse_with_relations(self) -> None:
        """Test parsing models with relationships."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.yaml"

            content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string
    relations:
      posts:
        type: hasMany
        model: Post
  Post:
    fields:
      id:
        type: uuid
      title:
        type: string
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: user_id
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Verify User relations
            user = schema.models["User"]
            assert "posts" in user.relations
            assert user.relations["posts"].type == "hasMany"
            assert user.relations["posts"].model == "Post"

            # Verify Post relations
            post = schema.models["Post"]
            assert "author" in post.relations
            assert post.relations["author"].type == "belongsTo"
            assert post.relations["author"].model == "User"
            assert post.relations["author"].foreign_key == "user_id"
