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

    def test_routes_can_generate_metrics_endpoint(self):
        """Test routes can generate /metrics endpoint for Prometheus."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/metrics": {
                    "GET": {
                        "name": "metrics",
                        "response": "void",
                        "summary": "Prometheus metrics endpoint"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Verify code compiles
        compile(code, "<string>", "exec")

        # Verify metrics endpoint is in generated code
        assert "/metrics" in code
        assert "def metrics" in code

    def test_routes_can_generate_both_health_and_metrics(self):
        """Test routes can generate both health and metrics endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/health": {
                    "GET": {
                        "name": "health_check",
                        "response": "void",
                        "summary": "Health check endpoint"
                    }
                },
                "/metrics": {
                    "GET": {
                        "name": "metrics",
                        "response": "void",
                        "summary": "Prometheus metrics endpoint"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Verify code compiles
        compile(code, "<string>", "exec")

        # Verify both endpoints are in generated code
        assert "/health" in code
        assert "def health_check" in code
        assert "/metrics" in code
        assert "def metrics" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
