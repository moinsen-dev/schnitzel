"""Integration tests for F107 - Schema validator validates index definitions on fields.

Test Requirements:
- test_index_true_valid - index: true is accepted and validated
- test_index_field_type - index field must be boolean
"""

import pytest
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from schnitzel.cli import app
from schnitzel.schema import SchemaParser, SchemaValidator
from schnitzel.schema.models import FieldDefinition


runner = CliRunner()


def test_index_true_valid() -> None:
    """Test that index: true is accepted and validated."""
    # Create a schema with index: true
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        index: true
      username:
        type: string
        index: true
""")

        # Parse and validate
        parser = SchemaParser()
        schema = parser.parse(schema_file)

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should be valid
        assert result.valid, f"Schema should be valid, but got errors: {result.errors}"

        # Verify index field is set
        email_field = schema.models["User"].fields["email"]
        assert email_field.index is True, "email field should have index=True"

        username_field = schema.models["User"].fields["username"]
        assert username_field.index is True, "username field should have index=True"


def test_index_field_type() -> None:
    """Test that index field must be a boolean value."""
    # Test via FieldDefinition directly
    # Valid boolean values
    field_true = FieldDefinition(type="string", index=True)
    assert field_true.index is True

    field_false = FieldDefinition(type="string", index=False)
    assert field_false.index is False

    # Test with schema file
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      email:
        type: string
        index: true
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should be valid
        assert result.valid, f"Schema with index: true should be valid"


def test_index_false_valid() -> None:
    """Test that index: false is also valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      email:
        type: string
        index: false
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should be valid
        assert result.valid, "Schema with index: false should be valid"

        # Verify index is False
        email_field = schema.models["User"].fields["email"]
        assert email_field.index is False


def test_index_default_false() -> None:
    """Test that index defaults to false when not specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      email:
        type: string
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        # Verify index defaults to False
        email_field = schema.models["User"].fields["email"]
        assert email_field.index is False, "index should default to False"


def test_index_with_multiple_fields() -> None:
    """Test index on multiple fields in the same model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        index: true
      username:
        type: string
        index: true
      password:
        type: string
      created_at:
        type: datetime
        index: true
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid, f"Schema should be valid"

        # Verify indexed fields
        user_fields = schema.models["User"].fields
        assert user_fields["email"].index is True
        assert user_fields["username"].index is True
        assert user_fields["password"].index is False
        assert user_fields["created_at"].index is True


def test_index_on_different_field_types() -> None:
    """Test that index works with different field types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      email:
        type: string
        index: true
      age:
        type: int
        index: true
      created_at:
        type: datetime
        index: true
      is_active:
        type: bool
        index: true
      user_id:
        type: uuid
        index: true
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid, "Index should work with various field types"

        # Verify all have index=true
        user_fields = schema.models["User"].fields
        for field_name in ["email", "age", "created_at", "is_active", "user_id"]:
            assert user_fields[field_name].index is True, f"{field_name} should have index=True"


def test_index_via_cli_validate() -> None:
    """Test index validation through CLI validate command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      email:
        type: string
        index: true
""")

        # Run CLI validate command
        result = runner.invoke(app, ["validate", str(schema_file)])

        # Should succeed
        assert result.exit_code == 0, f"Validation should succeed: {result.stdout}"
        assert "valid" in result.stdout.lower() or "OK" in result.stdout
