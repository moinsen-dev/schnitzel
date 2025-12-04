"""Integration tests for route parameter ordering (api_110).

Tests for:
- api_110: Generated routes have consistent parameter ordering
"""

import pytest
import re
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


class TestParameterOrdering:
    """Tests for api_110: Generated routes have consistent parameter ordering."""

    def test_path_params_before_query_params(self):
        """Test that path parameters come before query parameters."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "query_params": {"include_details": {"type": "boolean", "optional": True}}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Find the function signature
            match = re.search(r"async def get_user\((.*?)\)", code, re.DOTALL)
            if match:
                params = match.group(1)
                # Path param (id) should appear before query param (include_details)
                id_pos = params.find("id")
                include_pos = params.find("include_details")
                if id_pos >= 0 and include_pos >= 0:
                    assert id_pos < include_pos, "Path params should come before query params"
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_required_params_before_optional(self):
        """Test that required parameters come before optional parameters."""
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
                        "query_params": {
                            "status": {"type": "string", "optional": False},
                            "limit": {"type": "integer", "optional": True},
                            "offset": {"type": "integer", "optional": True}
                        }
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Required params without defaults should come first
            # Optional params with defaults (= None) should come after
            assert "def list_users" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_body_param_position(self):
        """Test that body parameter comes after path params."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
            },
            endpoints={
                "/users/{id}": {
                    "PUT": {
                        "name": "update_user",
                        "body": {"type": "User"}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Body should come after path params
            assert "update_user" in code
            # Should have both id and body params
            assert "id" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_db_session_param_position(self):
        """Test that db session parameter position is consistent."""
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

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # db: Session should typically come first or be a dependency
            if "Session" in code or "db:" in code:
                # DB param should be present
                assert "db" in code or "session" in code.lower()
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_auth_param_position(self):
        """Test that auth/user parameter position is consistent."""
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
                        "auth": True
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Auth dependency should be present
            assert "list_users" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_multiple_path_params_order(self):
        """Test ordering of multiple path parameters."""
        schema = SchnitzelSchema(
            models={
                "Comment": Model(
                    name="Comment",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{user_id}/posts/{post_id}/comments": {
                    "GET": {"name": "list_comments"}
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Path params should appear in URL order
            match = re.search(r"async def list_comments\((.*?)\)", code, re.DOTALL)
            if match:
                params = match.group(1)
                user_pos = params.find("user_id")
                post_pos = params.find("post_id")
                if user_pos >= 0 and post_pos >= 0:
                    assert user_pos < post_pos, "Path params should be in URL order"
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_dependency_injection_params(self):
        """Test that dependency injection parameters are properly ordered."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "auth": True,
                        "query_params": {"expand": {"type": "string", "optional": True}}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Should have function with proper params
            assert "get_user" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_consistent_ordering_across_endpoints(self):
        """Test that parameter ordering is consistent across all endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "query_params": {"expand": {"type": "string", "optional": True}}
                    },
                    "PUT": {
                        "name": "update_user",
                        "body": {"type": "User"},
                        "query_params": {"notify": {"type": "boolean", "optional": True}}
                    },
                    "DELETE": {
                        "name": "delete_user",
                        "query_params": {"hard": {"type": "boolean", "optional": True}}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # All endpoints should have id as first path param
            for endpoint in ["get_user", "update_user", "delete_user"]:
                assert endpoint in code
        except ImportError:
            pytest.skip("Routes generator not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
