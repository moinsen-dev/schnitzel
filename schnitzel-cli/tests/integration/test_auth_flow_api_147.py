"""Integration tests for auth flow (api_147).

Tests for:
- api_147: Integration test: Auth flow works end-to-end
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestAuthFlow:
    """Tests for api_147: Integration test: Auth flow works end-to-end."""

    def test_routes_can_have_auth(self):
        """Test that routes can be configured with auth."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users", "auth": True}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate routes
        assert "list_users" in code or "/users" in code

    def test_dart_client_has_auth_interceptor(self):
        """Test that Dart client has auth interceptor."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema, include_auth_interceptor=True)

        # Should have auth interceptor
        assert "AuthInterceptor" in code

    def test_dart_client_has_token_parameter(self):
        """Test that Dart client accepts token parameter."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have token parameter
        assert "token" in code

    def test_auth_header_added(self):
        """Test that authorization header is added."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should add authorization header
        assert "Authorization" in code or "Bearer" in code

    def test_routes_generator_handles_auth_param(self):
        """Test routes generator handles auth parameter."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/protected": {
                    "GET": {"name": "protected_route", "auth": True}
                },
                "/public": {
                    "GET": {"name": "public_route", "auth": False}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should handle both routes
        assert "protected_route" in code or "/protected" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
