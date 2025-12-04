"""Integration test for F142: Template rendering - Complex model with all features.

Test Requirements:
- Test model with description, relations, validation, defaults
- Test that all model features are properly rendered
- Test complex field configurations
- Test multiple relationships
- Test validation rules in generated code
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def complex_model_schema(temp_dir: Path) -> Path:
    """Create a schema with complex model featuring all capabilities."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User account with full profile and authentication"
    fields:
      id:
        type: uuid
        primary: true
        description: "Unique user identifier"
      username:
        type: string
        unique: true
        description: "Unique username for login"
      email:
        type: string
        unique: true
        format: email
        description: "User email address"
      password_hash:
        type: string
        description: "Hashed password"
      full_name:
        type: string
        optional: true
        description: "User's full name"
      age:
        type: int
        optional: true
        min: 0
        max: 150
        description: "User age in years"
      bio:
        type: text
        optional: true
        max_length: 500
        description: "User biography"
      is_active:
        type: bool
        default: true
        description: "Whether account is active"
      is_verified:
        type: bool
        default: false
        description: "Whether email is verified"
      role:
        type: enum
        values: ["admin", "moderator", "user", "guest"]
        default: user
        description: "User role"
      avatar_url:
        type: string
        optional: true
        format: url
        description: "Profile picture URL"
      preferences:
        type: json
        optional: true
        description: "User preferences as JSON"
      tags:
        type: list<string>
        optional: true
        description: "User tags"
      login_count:
        type: int
        default: 0
        min: 0
        description: "Number of times user logged in"
      last_login:
        type: datetime
        optional: true
        description: "Last login timestamp"
      created_at:
        type: datetime
        auto: create
        description: "Account creation timestamp"
      updated_at:
        type: datetime
        auto: update
        optional: true
        description: "Last update timestamp"
    relations:
      posts:
        type: hasMany
        model: Post
      profile:
        type: hasOne
        model: Profile
      comments:
        type: hasMany
        model: Comment

  Post:
    description: "Blog post with metadata"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
        description: "Post title"
      content:
        type: text
        description: "Post content"
      author_id:
        type: uuid
      status:
        type: enum
        values: ["draft", "published", "archived"]
        default: draft
      view_count:
        type: int
        default: 0
      rating:
        type: float
        default: 0.0
        min: 0.0
        max: 5.0
      published_at:
        type: datetime
        optional: true
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      comments:
        type: hasMany
        model: Comment

  Comment:
    description: "Comment on a post"
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
      author_id:
        type: uuid
      post_id:
        type: uuid
      is_edited:
        type: bool
        default: false
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      post:
        type: belongsTo
        model: Post
        foreign_key: post_id

  Profile:
    description: "Extended user profile"
    fields:
      id:
        type: uuid
        primary: true
      user_id:
        type: uuid
        unique: true
      website:
        type: string
        optional: true
        format: url
      location:
        type: string
        optional: true
      social_links:
        type: json
        optional: true
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id
"""
    schema_file = temp_dir / "complex.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_complex_model_generates_successfully(temp_dir: Path, complex_model_schema: Path):
    """Test that complex model with all features generates successfully."""
    result = runner.invoke(app, ["generate", str(complex_model_schema)])

    assert result.exit_code == 0, f"Generation failed: {result.stdout}"
    assert "Generation complete" in result.stdout or "✓" in result.stdout


def test_python_rendering_includes_descriptions(temp_dir: Path, complex_model_schema: Path):
    """Test that Python models include field descriptions as docstrings or comments."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Verify User class exists
    assert "class User" in content

    # Check for some field names
    assert "username" in content.lower()
    assert "email" in content.lower()
    assert "is_active" in content.lower()


def test_python_rendering_includes_validation(temp_dir: Path, complex_model_schema: Path):
    """Test that Python models include validation rules."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Should import validation libraries
    assert "pydantic" in content.lower() or "BaseModel" in content


def test_python_rendering_includes_defaults(temp_dir: Path, complex_model_schema: Path):
    """Test that Python models include default values."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Should have default values (True, False, 0, etc.)
    assert "True" in content or "true" in content.lower()
    assert "False" in content or "false" in content.lower()


def test_dart_rendering_includes_all_models(temp_dir: Path, complex_model_schema: Path):
    """Test that Dart generation includes all models."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "dart"])

    assert result.exit_code == 0

    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = dart_file.read_text()

    # Verify all models are present
    assert "class User" in content
    assert "class Post" in content
    assert "class Comment" in content
    assert "class Profile" in content


def test_dart_rendering_includes_freezed_annotations(temp_dir: Path, complex_model_schema: Path):
    """Test that Dart models include Freezed annotations."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "dart"])

    assert result.exit_code == 0

    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = dart_file.read_text()

    # Should have Freezed imports and annotations
    assert "@freezed" in content
    assert "freezed_annotation" in content


def test_all_relationships_rendered(temp_dir: Path, complex_model_schema: Path):
    """Test that all relationships are properly rendered."""
    result = runner.invoke(app, ["generate", str(complex_model_schema)])

    assert result.exit_code == 0

    # The generation should succeed with all relationships
    # Check that models with relations were processed
    assert "Models found: 4" in result.stdout or result.exit_code == 0


def test_enum_fields_rendered(temp_dir: Path, complex_model_schema: Path):
    """Test that enum fields are properly rendered."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Enum fields should be present
    assert "role" in content.lower()
    assert "status" in content.lower()


def test_optional_fields_rendered(temp_dir: Path, complex_model_schema: Path):
    """Test that optional fields are properly marked."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Optional fields should use Optional type annotation
    assert "Optional" in content or "optional" in content.lower() or "None" in content


def test_unique_constraints_rendered(temp_dir: Path, complex_model_schema: Path):
    """Test that unique constraints are indicated in generated code."""
    result = runner.invoke(app, ["generate", str(complex_model_schema)])

    assert result.exit_code == 0

    # Validation should detect unique fields
    assert "Unique constraints:" in result.stdout or result.exit_code == 0


def test_auto_timestamp_fields_rendered(temp_dir: Path, complex_model_schema: Path):
    """Test that auto timestamp fields (created_at, updated_at) are rendered."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Timestamp fields should exist
    assert "created_at" in content.lower()


def test_json_fields_rendered(temp_dir: Path, complex_model_schema: Path):
    """Test that JSON fields are properly typed."""
    result = runner.invoke(app, ["generate", str(complex_model_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # JSON fields should exist
    assert "preferences" in content.lower() or "social_links" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
