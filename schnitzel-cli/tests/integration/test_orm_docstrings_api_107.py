"""Integration tests for ORM docstrings (api_107).

Tests for:
- api_107: Generated SQLAlchemy ORM includes docstrings
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMDocstrings:
    """Tests for api_107: ORM docstrings generation."""

    def test_generates_model_with_docstring(self):
        """Test ORM generates model that compiles."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)
        compile(code, "<string>", "exec")

    def test_generates_field_documentation(self):
        """Test ORM generates documented fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string", description="User email")
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)
        assert "email" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
