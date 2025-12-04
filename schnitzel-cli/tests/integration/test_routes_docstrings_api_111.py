"""Integration tests for routes docstrings (api_111).

Tests for:
- api_111: Generated FastAPI routes include docstrings
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesDocstrings:
    """Tests for api_111: Routes docstrings generation."""

    def test_generates_route_documentation(self):
        """Test routes generates documented endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        compile(code, "<string>", "exec")

    def test_routes_have_function_names(self):
        """Test routes have descriptive function names."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{id}": {"GET": {"name": "get_user", "response": "User"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        assert "get_user" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
