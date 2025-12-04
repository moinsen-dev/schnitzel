"""Integration tests for routes handling missing optional fields (api_153).

Tests for:
- api_153: Unit test: Routes generator handles missing optional fields
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesMissingOptional:
    """Tests for api_153: Unit test: Routes generator handles missing optional fields."""

    def test_generates_with_no_endpoints(self):
        """Test routes generator works with no endpoints defined."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
            # No endpoints defined
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should still generate valid code (may be minimal)
        assert code is not None

    def test_generates_with_empty_endpoints(self):
        """Test routes generator works with empty endpoints dict."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={}
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should still generate valid code
        assert code is not None

    def test_generates_with_minimal_endpoint(self):
        """Test routes generator with minimal endpoint definition."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}  # Only name, no other options
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate route
        assert "list_users" in code or "/users" in code

    def test_handles_missing_auth(self):
        """Test routes generator handles missing auth field."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}  # No auth specified
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate without error
        assert code is not None

    def test_handles_missing_response(self):
        """Test routes generator handles missing response field."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}  # No response specified
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate without error
        assert code is not None

    def test_handles_partial_endpoint_methods(self):
        """Test routes generator handles partial HTTP method definitions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {"name": "get_user"}
                    # DELETE not defined
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should only generate GET route
        assert "get_user" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
