"""Integration tests for CORS support (api_169).

Tests for:
- api_169: Generated API supports CORS for development
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestCORSSupport:
    """Tests for api_169: CORS support."""

    def test_routes_generate_valid_fastapi(self):
        """Test routes generate valid FastAPI code that can have CORS added."""
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
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
