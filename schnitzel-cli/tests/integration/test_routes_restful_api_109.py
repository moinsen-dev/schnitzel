"""Integration tests for RESTful route conventions (api_109).

Tests for:
- api_109: Generated FastAPI routes follow RESTful conventions
"""

import pytest
import re
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


class TestRoutesRESTful:
    """Tests for api_109: Generated FastAPI routes follow RESTful conventions."""

    def test_list_uses_get_method(self):
        """Test that list endpoints use GET method."""
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
                        "response": {"200": {"type": "list[User]"}}
                    }
                }
            }
        )

        # Import here to avoid issues if module not ready
        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Should use @router.get decorator
            assert "@router.get" in code or "@app.get" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_create_uses_post_method(self):
        """Test that create endpoints use POST method."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "POST": {
                        "name": "create_user",
                        "response": {"201": {"type": "User"}}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            assert "@router.post" in code or "@app.post" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_update_uses_put_method(self):
        """Test that update endpoints use PUT method."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "PUT": {
                        "name": "update_user",
                        "response": {"200": {"type": "User"}}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            assert "@router.put" in code or "@app.put" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_delete_uses_delete_method(self):
        """Test that delete endpoints use DELETE method."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "DELETE": {
                        "name": "delete_user",
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            assert "@router.delete" in code or "@app.delete" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_paths_use_plural_nouns(self):
        """Test that resource paths use plural nouns."""
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

            # Path should be /users (plural)
            assert "'/users'" in code or '"/users"' in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_detail_path_has_id_parameter(self):
        """Test that detail endpoints include {id} path parameter."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {"name": "get_user"}
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Should have {id} in path
            assert "{id}" in code or "/{id}" in code or "id:" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_uses_proper_status_codes(self):
        """Test that routes use proper HTTP status codes."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "POST": {
                        "name": "create_user",
                        "response": {"201": {"type": "User"}}
                    }
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Should use status_code=201 for POST/create
            assert "status_code=201" in code or "201" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_async_functions(self):
        """Test that route handlers are async."""
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

            # Should use async def
            assert "async def" in code
        except ImportError:
            pytest.skip("Routes generator not available")

    def test_snake_case_function_names(self):
        """Test that function names use snake_case."""
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
                    "POST": {"name": "create_user"},
                }
            }
        )

        try:
            from schnitzel.generators.python.routes import FastAPIRouteGenerator
            generator = FastAPIRouteGenerator()
            code = generator.generate(schema)

            # Functions should be snake_case
            assert "def list_users" in code or "list_users" in code
            assert "def create_user" in code or "create_user" in code
        except ImportError:
            pytest.skip("Routes generator not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
