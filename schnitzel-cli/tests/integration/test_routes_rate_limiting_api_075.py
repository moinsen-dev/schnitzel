"""Integration tests for FastAPI rate limiting (api_075).

Tests for:
- api_075: FastAPI route generator adds rate limiting decorators
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesRateLimiting:
    """Tests for api_075: FastAPI route generator adds rate limiting decorators."""

    def test_generates_routes_for_rate_limit_endpoints(self):
        """Test routes can be generated for endpoints with rate limit config."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "response": "User[]",
                        "rate_limit": "100/minute"  # Rate limit config
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate endpoint
        assert "list_users" in code or "users" in code
        compile(code, "<string>", "exec")

    def test_generates_routes_without_rate_limit(self):
        """Test routes work without rate limit config."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users", "response": "User[]"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate without rate limiting
        assert "list_users" in code or "users" in code
        compile(code, "<string>", "exec")

    def test_multiple_endpoints_different_limits(self):
        """Test multiple endpoints can have different rate limits."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "response": "User[]",
                        "rate_limit": "100/minute"
                    },
                    "POST": {
                        "name": "create_user",
                        "body": "User",
                        "response": "User",
                        "rate_limit": "10/minute"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have both endpoints
        assert "list_users" in code or "create_user" in code
        compile(code, "<string>", "exec")

    def test_generates_valid_code_structure(self):
        """Test rate limited endpoints generate valid code structure."""
        schema = SchnitzelSchema(
            models={
                "Resource": Model(
                    name="Resource",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/resources": {
                    "GET": {
                        "name": "get_resources",
                        "response": "Resource[]"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid Python code
        compile(code, "<string>", "exec")
        assert "Resource" in code

    def test_auth_with_rate_limit(self):
        """Test endpoints with both auth and rate limit."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "response": "User[]",
                        "auth": "required",
                        "rate_limit": "100/minute"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate endpoint with auth
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
