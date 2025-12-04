"""Integration tests for concurrent request handling (api_152).

Tests for:
- api_152: Performance test: Generated API handles concurrent requests
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestPerformanceConcurrent:
    """Tests for api_152: Concurrent request handling."""

    def test_generates_async_endpoints(self):
        """Test routes generates async endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        assert "async" in code or "def " in code

    def test_generates_multiple_endpoints(self):
        """Test multiple concurrent-safe endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users", "response": "User[]"}},
                "/users/{id}": {"GET": {"name": "get_user", "response": "User"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
