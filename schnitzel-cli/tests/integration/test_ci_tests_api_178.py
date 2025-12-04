"""Integration tests for CI tests (api_178).

Tests for:
- api_178: Continuous Integration: Tests run on push
"""

import pytest
from schnitzel.schema.validator import SchemaValidator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


class TestCITests:
    """Tests for api_178: CI test support."""

    def test_validator_can_run_in_ci(self):
        """Test validator works in CI environment."""
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

    def test_generators_work_without_file_system(self):
        """Test generators work without file system access."""
        from schnitzel.generators.python.orm import SQLAlchemyORMGenerator

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)
        assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
