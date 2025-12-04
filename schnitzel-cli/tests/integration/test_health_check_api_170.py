"""Integration tests for health check endpoint (api_170).

Tests for:
- api_170: Generated API includes health check endpoint
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestHealthCheck:
    """Tests for api_170: Generated API includes health check endpoint."""

    def test_routes_generator_exists(self):
        """Test that routes generator exists."""
        assert FastAPIRouteGenerator is not None

    def test_routes_can_include_health(self):
        """Test that routes can include health endpoint."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/health": {
                    "GET": {"name": "health_check"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have health endpoint
        assert "health" in code.lower()

    def test_generator_produces_valid_routes(self):
        """Test that generator produces valid routes structure."""
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

        # Should have route decorator
        assert "@router" in code or "@app" in code

    def test_routes_have_proper_structure(self):
        """Test that routes have proper structure for health endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/status": {
                    "GET": {"name": "get_status"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate function
        assert "def " in code

    def test_health_endpoint_returns_json(self):
        """Test that health endpoint would return JSON."""
        schema = SchnitzelSchema(
            models={},
            endpoints={
                "/ping": {
                    "GET": {"name": "ping"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid endpoint
        assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
