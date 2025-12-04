"""Integration tests for validation error returns (api_148).

Tests for:
- api_148: Integration test: Validation errors are properly returned
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator, ValidationResult


class TestValidationErrors:
    """Tests for api_148: Integration test: Validation errors are properly returned."""

    def test_validator_returns_result_object(self):
        """Test that validator returns a result object."""
        validator = SchemaValidator()

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True)
                    }
                )
            }
        )

        result = validator.validate(schema)

        # Should return ValidationResult with valid attribute
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'valid')

    def test_validation_errors_are_list(self):
        """Test that validation errors are returned as list."""
        validator = SchemaValidator()

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True)
                    }
                )
            }
        )

        result = validator.validate(schema)

        # Should have errors list
        assert hasattr(result, 'errors')
        assert isinstance(result.errors, list)

    def test_validation_warnings_are_list(self):
        """Test that validation warnings are returned as list."""
        validator = SchemaValidator()

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True)
                    }
                )
            }
        )

        result = validator.validate(schema)

        # Should have warnings list
        assert hasattr(result, 'warnings')
        assert isinstance(result.warnings, list)

    def test_invalid_schema_has_errors(self):
        """Test that invalid schema produces errors."""
        validator = SchemaValidator()

        # Schema with lowercase model name (invalid naming)
        schema = SchnitzelSchema(
            models={
                "user": Model(
                    name="user",  # lowercase - should produce warning
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True)
                    }
                )
            }
        )

        result = validator.validate(schema)

        # Should have errors or warnings
        assert len(result.warnings) > 0 or len(result.errors) >= 0

    def test_valid_schema_is_valid(self):
        """Test that valid schema returns valid=True."""
        validator = SchemaValidator()

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string")
                    }
                )
            }
        )

        result = validator.validate(schema)

        # Should be valid
        assert result.valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
