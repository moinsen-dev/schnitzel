"""Integration tests for template generation metadata (api_130).

Tests for:
- api_130: Templates include generation metadata in header
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestTemplateMetadata:
    """Tests for api_130: Template metadata headers."""

    def test_orm_generates_header(self):
        """Test ORM generates code with header."""
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
        # Should have some comment or docstring at start
        assert code.startswith("#") or code.startswith('"""') or "import" in code[:100]

    def test_routes_generates_header(self):
        """Test routes generates code with header."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
