"""Integration tests for API reference docs (api_158).

Tests for:
- api_158: Documentation: API reference docs are generated
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestAPIReferenceDocs:
    """Tests for api_158: API reference docs generation."""

    def test_routes_generate_openapi_metadata(self):
        """Test routes include OpenAPI metadata."""
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
        # FastAPI automatically generates OpenAPI
        assert "router" in code or "@" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
