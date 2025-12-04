"""Test F086: Schema validator validates email format constraint.

This feature tests that the schema validator correctly handles the 'email' format constraint.
It focuses on ensuring email format is accepted during schema validation and doesn't block
code generation.

Test Requirements:
- test_email_format_accepted: Verify format: email is accepted as valid constraint
- test_field_with_email_format: Verify field with email format validates correctly
- test_email_format_in_generated_code: Verify email format doesn't block code generation
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app
from schnitzel.schema import SchemaValidator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


def test_email_format_accepted():
    """Test that format: email is accepted as a valid constraint in schema validation.

    This test verifies that the validator recognizes 'email' as one of the supported
    format values for string fields.
    """
    # Create a schema with email format constraint
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email"),
                }
            )
        }
    )

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Email format should be accepted but got errors: {result.errors}"
    assert result.errors == [], "Should have no validation errors for valid email format"


def test_field_with_email_format():
    """Test that a field with email format constraint validates correctly.

    This test verifies that:
    - Email format can be combined with other field properties
    - Validation recognizes the format constraint
    - All combinations of email format with other constraints work properly
    """
    # Test email format with various field configurations
    schema = SchnitzelSchema(
        models={
            "Contact": Model(
                name="Contact",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    # Required email with unique constraint
                    "primary_email": FieldDefinition(
                        type="string",
                        format="email",
                        unique=True,
                        required=True
                    ),
                    # Optional email with default
                    "secondary_email": FieldDefinition(
                        type="string",
                        format="email",
                        optional=True,
                        default=None
                    ),
                    # Simple email field
                    "backup_email": FieldDefinition(
                        type="string",
                        format="email"
                    ),
                }
            )
        }
    )

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Field with email format should validate correctly: {result.errors}"
    assert result.errors == []

    # Verify unique constraint is tracked for primary_email
    assert "Contact" in result.unique_fields
    assert "primary_email" in result.unique_fields["Contact"]


def test_email_format_in_generated_code():
    """Test that email format constraint doesn't block code generation.

    This is a critical integration test that verifies:
    - Schema with email format passes validation
    - Code generation proceeds without errors
    - Generated files are created successfully
    """
    runner = CliRunner()
    original_cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            temp_dir = Path(tmpdir)

            # Create a valid schema with email format constraint
            schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User account with email"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
        unique: true
      username:
        type: string
        unique: true
      created_at:
        type: datetime
        auto: create
"""
            schema_file = temp_dir / "schema.yaml"
            schema_file.write_text(schema_content)

            # Run generate command
            result = runner.invoke(app, ["generate", str(schema_file)])

            # Verify command succeeds
            assert result.exit_code == 0, f"Generate should succeed with email format: {result.stdout}"

            # Verify validation passed
            assert "Schema parsed successfully" in result.stdout
            assert "Schema validation passed" in result.stdout

            # Verify code generation was not blocked
            assert "Schema validation failed" not in result.stdout
            assert "Unsupported format" not in result.stdout

            # Verify generation proceeded
            output_lines = result.stdout.lower()
            generation_indicators = [
                "generating" in output_lines,
                "generated" in output_lines,
                "generation complete" in output_lines,
                "ready for code generation" in output_lines
            ]
            assert any(generation_indicators), \
                "Should show generation progress or completion"

        finally:
            os.chdir(original_cwd)


def test_multiple_email_fields_in_model():
    """Test that multiple fields with email format in the same model validate correctly.

    This verifies that the validator can handle multiple email format constraints
    in a single model without conflicts.
    """
    schema = SchnitzelSchema(
        models={
            "Account": Model(
                name="Account",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "primary_email": FieldDefinition(type="string", format="email", unique=True),
                    "recovery_email": FieldDefinition(type="string", format="email", optional=True),
                    "contact_email": FieldDefinition(type="string", format="email", optional=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Multiple email fields should validate: {result.errors}"
    assert result.errors == []


def test_email_format_across_multiple_models():
    """Test that email format constraint works across multiple models.

    This ensures the validator correctly handles email format in different models
    within the same schema.
    """
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email", unique=True),
                }
            ),
            "Invitation": Model(
                name="Invitation",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "recipient_email": FieldDefinition(type="string", format="email"),
                    "sender_email": FieldDefinition(type="string", format="email"),
                }
            ),
            "Contact": Model(
                name="Contact",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "business_email": FieldDefinition(type="string", format="email"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes for all models
    assert result.valid is True, f"Email format across models should validate: {result.errors}"
    assert result.errors == []


def test_email_format_with_relationships():
    """Test that email format constraint works in models with relationships.

    This verifies that format constraints don't interfere with relationship validation.
    """
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email", unique=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": {
                        "type": "hasMany",
                        "model": "Post"
                    }
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                    "contact_email": FieldDefinition(type="string", format="email", optional=True),
                },
                relations={
                    "author": {
                        "type": "belongsTo",
                        "model": "User",
                        "foreign_key": "author_id"
                    }
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Email format with relationships should validate: {result.errors}"
    assert result.errors == []


def test_email_format_is_case_sensitive():
    """Test that format constraint is case-sensitive (lowercase 'email' only).

    This verifies that the validator enforces the correct format value casing.
    """
    # Test with incorrect casing - should fail
    schema_uppercase = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="EMAIL"),  # Wrong case
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema_uppercase)

    # Should fail validation due to wrong case
    assert result.valid is False, "Format constraint should be case-sensitive"
    assert len(result.errors) > 0

    error_message = "\n".join(result.errors)
    assert "EMAIL" in error_message or "Unsupported format" in error_message
