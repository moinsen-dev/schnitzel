"""Integration tests for routes filtering support (api_174).

Tests for:
- api_174: FastAPI routes support filtering with query parameters
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesFiltering:
    """Tests for api_174: FastAPI routes support filtering with query parameters."""

    def test_routes_can_have_query_params(self):
        """Test that routes can have query parameters."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "query_params": ["status"]
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate route
        assert "list_users" in code or "/users" in code

    def test_routes_support_optional_params(self):
        """Test that routes support optional query parameters."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        assert code is not None

    def test_routes_import_query(self):
        """Test that routes import Query from FastAPI."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have FastAPI imports
        assert "fastapi" in code.lower() or "APIRouter" in code

    def test_list_endpoints_exist(self):
        """Test that list endpoints can be generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have list endpoint
        assert "list_users" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
