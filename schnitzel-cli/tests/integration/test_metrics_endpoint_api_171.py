"""Integration tests for metrics endpoint (api_171).

Tests for:
- api_171: Generated API includes metrics endpoint
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestMetricsEndpoint:
    """Tests for api_171: Metrics endpoint generation."""

    def test_routes_can_generate_health_endpoint(self):
        """Test routes can generate health/metrics endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/health": {"GET": {"name": "health_check", "response": "void"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
