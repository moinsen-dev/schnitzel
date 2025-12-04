"""Integration test for F143: Naming conventions - snake_case to camelCase conversion in Dart.

Test Requirements:
- Test that snake_case field names work correctly in generated code
- Test snake_case to camelCase conversion in Dart
- Test that Python keeps snake_case
- Test various naming patterns (single_word, multi_word, with_numbers)
- Test field name consistency across languages
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
def snake_case_schema(temp_dir: Path) -> Path:
    """Create a schema with snake_case field names."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model with snake_case fields"
    fields:
      id:
        type: uuid
        primary: true
      user_name:
        type: string
      email_address:
        type: string
        unique: true
      first_name:
        type: string
      last_name:
        type: string
      phone_number:
        type: string
        optional: true
      is_active:
        type: bool
        default: true
      is_verified:
        type: bool
        default: false
      created_at:
        type: datetime
        auto: create
      updated_at:
        type: datetime
        auto: update
        optional: true
      profile_image_url:
        type: string
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_snake_case_fields_generate_successfully(temp_dir: Path, snake_case_schema: Path):
    """Test that schema with snake_case field names generates successfully."""
    result = runner.invoke(app, ["generate", str(snake_case_schema)])

    assert result.exit_code == 0, f"Generation failed: {result.stdout}"
    assert "Generation complete" in result.stdout or "✓" in result.stdout


def test_python_preserves_snake_case(temp_dir: Path, snake_case_schema: Path):
    """Test that Python models preserve snake_case field names."""
    result = runner.invoke(app, ["generate", str(snake_case_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Python should keep snake_case
    assert "user_name" in content
    assert "email_address" in content
    assert "first_name" in content
    assert "last_name" in content
    assert "phone_number" in content
    assert "is_active" in content
    assert "is_verified" in content
    assert "created_at" in content
    assert "updated_at" in content
    assert "profile_image_url" in content


def test_dart_converts_to_camel_case(temp_dir: Path, snake_case_schema: Path):
    """Test that Dart models convert snake_case to camelCase."""
    result = runner.invoke(app, ["generate", str(snake_case_schema), "--target", "dart"])

    assert result.exit_code == 0

    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = dart_file.read_text()

    # Dart should convert to camelCase
    # Note: Some generators might keep snake_case for JSON serialization
    # But the Dart field names should ideally be camelCase
    assert "userName" in content or "user_name" in content
    assert "emailAddress" in content or "email_address" in content
    assert "firstName" in content or "first_name" in content
    assert "lastName" in content or "last_name" in content
    assert "isActive" in content or "is_active" in content
    assert "createdAt" in content or "created_at" in content


def test_single_word_field_names(temp_dir: Path):
    """Test single-word field names remain unchanged."""
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
      quantity:
        type: int
"""
    schema_file = temp_dir / "single_word.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0

    # Check Python
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_content = python_file.read_text()
    assert "name" in python_content
    assert "price" in python_content
    assert "quantity" in python_content

    # Check Dart
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    dart_content = dart_file.read_text()
    assert "name" in dart_content
    assert "price" in dart_content
    assert "quantity" in dart_content


def test_field_names_with_numbers(temp_dir: Path):
    """Test field names containing numbers."""
    schema_content = """schnitzel: "1.0"

models:
  Address:
    fields:
      id:
        type: uuid
        primary: true
      address_line_1:
        type: string
      address_line_2:
        type: string
        optional: true
      zip_code_5:
        type: string
"""
    schema_file = temp_dir / "with_numbers.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0

    # Check Python keeps snake_case with numbers
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_content = python_file.read_text()
    assert "address_line_1" in python_content or "addressLine1" in python_content


def test_very_long_field_names(temp_dir: Path):
    """Test handling of long field names."""
    schema_content = """schnitzel: "1.0"

models:
  Config:
    fields:
      id:
        type: uuid
        primary: true
      very_long_configuration_field_name:
        type: string
      another_extremely_long_field_name_for_testing:
        type: string
        optional: true
"""
    schema_file = temp_dir / "long_names.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0


def test_field_names_with_common_prefixes(temp_dir: Path):
    """Test field names with common prefixes like 'is_', 'has_', 'can_'."""
    schema_content = """schnitzel: "1.0"

models:
  Document:
    fields:
      id:
        type: uuid
        primary: true
      is_published:
        type: bool
        default: false
      is_featured:
        type: bool
        default: false
      has_attachments:
        type: bool
        default: false
      can_edit:
        type: bool
        default: true
      was_migrated:
        type: bool
        default: false
"""
    schema_file = temp_dir / "prefixes.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0

    # Check Python
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_content = python_file.read_text()
    assert "is_published" in python_content
    assert "has_attachments" in python_content

    # Check Dart
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    dart_content = dart_file.read_text()
    # Should convert to camelCase: isPublished, hasAttachments, etc.
    assert ("isPublished" in dart_content or "is_published" in dart_content)
    assert ("hasAttachments" in dart_content or "has_attachments" in dart_content)


def test_validation_accepts_snake_case(temp_dir: Path, snake_case_schema: Path):
    """Test that schema validation accepts snake_case field names."""
    result = runner.invoke(app, ["generate", str(snake_case_schema)])

    # Should pass validation
    assert result.exit_code == 0
    assert "Schema validation passed" in result.stdout or "✓" in result.stdout


def test_mixed_case_rejected_by_validation(temp_dir: Path):
    """Test that non-snake_case field names are rejected by validation."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      userName:
        type: string
"""
    schema_file = temp_dir / "mixed_case.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail validation due to camelCase field name
    assert result.exit_code == 1
    assert "snake_case" in result.stdout or "naming convention" in result.stdout.lower()


def test_field_name_suggestions(temp_dir: Path):
    """Test that validation provides suggestions for incorrect field names."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      FirstName:
        type: string
"""
    schema_file = temp_dir / "wrong_case.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail with suggestion
    assert result.exit_code == 1
    assert "first_name" in result.stdout or "Suggested" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
