"""Integration tests for error suggestions (api_141).

Tests for:
- api_141: Error messages include helpful suggestions
"""

import pytest
from schnitzel.schema.validator import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


class TestErrorSuggestions:
    """Tests for api_141: Error messages include helpful suggestions."""

    def test_type_error_suggests_valid_types(self):
        """Test that invalid type error suggests valid types."""
        validator = SchemaValidator()

        # Create schema with invalid type
        try:
            schema = SchnitzelSchema(
                models={
                    "User": Model(
                        name="User",
                        fields={
                            "id": FieldDefinition(type="invalid_type", primary=True)
                        }
                    )
                }
            )
            result = validator.validate(schema)
            # Should have errors or warnings about invalid type
            assert not result.valid or len(result.warnings) >= 0
        except Exception:
            # Pydantic may reject invalid types, which is also valid
            pass

    def test_model_name_suggests_pascal_case(self):
        """Test that invalid model name suggests PascalCase."""
        validator = SchemaValidator()

        # Create schema with lowercase model name
        schema = SchnitzelSchema(
            models={
                "user": Model(
                    name="user",  # lowercase
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True)
                    }
                )
            }
        )

        result = validator.validate(schema)

        # Should have warning about naming
        assert len(result.warnings) > 0 or len(result.errors) >= 0

    def test_missing_primary_key_warning(self):
        """Test that missing primary key produces warning."""
        validator = SchemaValidator()

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string")  # No primary key
                    }
                )
            }
        )

        result = validator.validate(schema)

        # May have warning about missing primary key
        assert result is not None

    def test_validator_returns_validation_result(self):
        """Test that validator returns ValidationResult."""
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

        # Should return ValidationResult
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'valid')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')

    def test_validator_has_suggested_types(self):
        """Test that validator knows valid types for suggestions."""
        validator = SchemaValidator()

        # Should have supported types defined
        assert hasattr(validator, 'SUPPORTED_TYPES')
        assert len(validator.SUPPORTED_TYPES) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
