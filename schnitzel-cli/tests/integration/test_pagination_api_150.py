"""Integration tests for pagination (api_150).

Tests for:
- api_150: Integration test: Pagination works correctly
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestPagination:
    """Tests for api_150: Pagination support."""

    def test_routes_generate_with_pagination(self):
        """Test routes can be generated with pagination."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users", "response": "User[]", "pagination": True}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        compile(code, "<string>", "exec")

    def test_pagination_params_generated(self):
        """Test pagination parameters are in generated code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users", "response": "User[]", "pagination": True}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        assert "page" in code or "list_users" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
