"""Test F010: Schema validator rejects model with unsupported field type."""

import pytest
from schnitzel.schema import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


def test_unsupported_field_type_decimal():
    """Test that validator rejects unsupported 'decimal' type."""
    # Create schema with User model having field: age with type 'decimal'
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "age": FieldDefinition(type="decimal"),
                }
            )
        }
    )

    # Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails
    assert result.valid is False, "Validation should fail for unsupported type 'decimal'"
    assert len(result.errors) > 0, "Should have at least one error"

    # Get the error message
    error_message = "\n".join(result.errors)

    # Verify error message lists unsupported type 'decimal'
    assert "decimal" in error_message, "Error should mention unsupported type 'decimal'"

    # Verify error suggests valid alternatives (float, int)
    assert "float" in error_message or "int" in error_message, (
        "Error should suggest 'float' or 'int' as alternatives"
    )

    # Verify error includes field name and model name
    assert "age" in error_message, "Error should include field name 'age'"
    assert "User" in error_message, "Error should include model name 'User'"


def test_error_message_format():
    """Test that error message follows the required format."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "age": FieldDefinition(type="decimal"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails
    assert result.valid is False

    error_message = "\n".join(result.errors)

    # Verify format components
    assert "Unsupported field type" in error_message
    assert "'decimal'" in error_message
    assert "field 'age'" in error_message
    assert "model 'User'" in error_message
    assert "Supported types:" in error_message
    assert "Did you mean:" in error_message


def test_supported_types_listed_in_error():
    """Test that error message lists all supported types."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "data": FieldDefinition(type="unknown"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Verify supported types are listed
    assert "string" in error_message
    assert "int" in error_message
    assert "float" in error_message
    assert "bool" in error_message
    assert "datetime" in error_message
    assert "uuid" in error_message
    assert "json" in error_message
    assert "enum" in error_message
    assert "vector" in error_message
    assert "list<T>" in error_message


def test_did_you_mean_suggestions():
    """Test that 'did you mean' provides similar type suggestions."""
    test_cases = [
        ("decimal", ["float", "int"]),  # Should suggest float or int
        ("integer", ["int"]),  # Should suggest int
        ("str", ["string"]),  # Should suggest string
        ("number", ["int", "float"]),  # Could suggest numeric types
    ]

    for unsupported_type, expected_suggestions in test_cases:
        schema = SchnitzelSchema(
            models={
                "TestModel": Model(
                    name="TestModel",
                    fields={
                        "field": FieldDefinition(type=unsupported_type),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is False
        error_message = "\n".join(result.errors)

        # Verify at least one expected suggestion appears
        has_suggestion = any(
            suggestion in error_message for suggestion in expected_suggestions
        )
        assert has_suggestion, (
            f"Error should suggest one of {expected_suggestions} for '{unsupported_type}'"
        )


def test_unsupported_type_in_list():
    """Test that validator rejects unsupported types inside list<T>."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "tags": FieldDefinition(type="list<decimal>"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Verify error mentions the unsupported inner type
    assert "decimal" in error_message
    assert "tags" in error_message
    assert "User" in error_message


def test_valid_schema_passes():
    """Test that validator accepts schemas with only supported types."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "age": FieldDefinition(type="int"),
                    "balance": FieldDefinition(type="float"),
                    "active": FieldDefinition(type="bool"),
                    "created_at": FieldDefinition(type="datetime"),
                    "metadata": FieldDefinition(type="json"),
                    "tags": FieldDefinition(type="list<string>"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_multiple_models_with_unsupported_types():
    """Test that validator catches unsupported types across multiple models."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "age": FieldDefinition(type="decimal"),  # Invalid
                }
            ),
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should have validation errors
    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "decimal" in error_message
    assert "User" in error_message


def test_enum_type_is_supported():
    """Test that 'enum' is recognized as a supported type."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "role": FieldDefinition(
                        type="enum",
                        values=["admin", "user", "guest"]
                    ),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_vector_type_is_supported():
    """Test that 'vector' is recognized as a supported type."""
    schema = SchnitzelSchema(
        models={
            "Embedding": Model(
                name="Embedding",
                fields={
                    "vector": FieldDefinition(type="vector", dimensions=1536),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []
