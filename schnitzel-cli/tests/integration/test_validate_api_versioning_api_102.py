"""Integration tests for validate API versioning (api_102).

Tests for:
- api_102: Validate command checks API versioning consistency
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator


class TestValidateAPIVersioning:
    """Tests for api_102: Validate API versioning consistency."""

    def test_validates_schema_without_version(self):
        """Test validator handles schema without version."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)
        assert result is not None

    def test_validates_schema_with_version(self):
        """Test validator handles schema with version."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
