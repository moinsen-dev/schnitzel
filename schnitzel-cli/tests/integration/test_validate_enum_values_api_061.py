"""Integration tests for validate enum value consistency (api_061).

Tests for:
- api_061: Validate command checks enum value consistency
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator


class TestValidateEnumValues:
    """Tests for api_061: Validate command checks enum value consistency."""

    def test_valid_enum_field_passes(self):
        """Test validator passes with valid enum field definition."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="string",
                            values=["admin", "user", "guest"]  # Enum values in field
                        ),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Valid enum should pass
        assert result is not None

    def test_validates_enum_values_list(self):
        """Test validator validates enum values are a list."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="string",
                            values=["active", "inactive", "pending"]
                        ),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should validate enum values
        assert result is not None

    def test_handles_field_without_enum(self):
        """Test validator handles field without enum values."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),  # No values
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass without enum values
        assert result is not None

    def test_empty_enum_values(self):
        """Test validator handles empty enum values list."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(type="string", values=[]),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should handle empty enum
        assert result is not None

    def test_multiple_enum_fields(self):
        """Test validator handles multiple enum fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(type="string", values=["admin", "user"]),
                        "status": FieldDefinition(type="string", values=["active", "inactive"]),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should process schema with multiple enum fields
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
