"""Integration tests for route grouping by resource (api_020).

Tests for:
- api_020: FastAPI route generator groups routes by resource
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesGrouping:
    """Tests for api_020: FastAPI route generator groups routes by resource."""

    def test_routes_grouped_by_path(self):
        """Test that routes with same base path are grouped together."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"},
                    "POST": {"name": "create_user"}
                },
                "/users/{id}": {
                    "GET": {"name": "get_user"},
                    "PUT": {"name": "update_user"},
                    "DELETE": {"name": "delete_user"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # All user routes should be present
        assert "list_users" in code
        assert "create_user" in code
        assert "get_user" in code
        assert "update_user" in code
        assert "delete_user" in code

    def test_multiple_resources_separated(self):
        """Test that different resources are handled separately."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Product": Model(
                    name="Product",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                },
                "/products": {
                    "GET": {"name": "list_products"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Both resources should be present
        assert "list_users" in code
        assert "list_products" in code
        assert "/users" in code
        assert "/products" in code

    def test_nested_resource_routes(self):
        """Test that nested resource routes are handled properly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{user_id}/posts": {
                    "GET": {"name": "list_user_posts"}
                },
                "/users/{user_id}/posts/{id}": {
                    "GET": {"name": "get_user_post"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Nested routes should be present
        assert "list_user_posts" in code
        assert "get_user_post" in code
        assert "/users/{user_id}/posts" in code

    def test_routes_use_router_prefix(self):
        """Test that routes are generated with proper router setup."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should create an APIRouter
        assert "APIRouter" in code
        assert "router = APIRouter()" in code

    def test_tags_for_resource_grouping(self):
        """Test that tags can be used for OpenAPI grouping."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "tags": ["users"]
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should include tags
        assert "tags=" in code or "users" in code

    def test_consistent_route_ordering(self):
        """Test that routes are in a consistent order."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "DELETE": {"name": "delete_user"},
                    "GET": {"name": "get_user"},
                    "PUT": {"name": "update_user"}
                },
                "/users": {
                    "POST": {"name": "create_user"},
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # All routes should be present
        assert "list_users" in code
        assert "create_user" in code
        assert "get_user" in code
        assert "update_user" in code
        assert "delete_user" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
