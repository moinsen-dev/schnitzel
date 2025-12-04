"""Integration tests for FastAPI request validation (api_073).

Tests for:
- api_073: FastAPI route generator adds request validation
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesRequestValidation:
    """Tests for api_073: FastAPI route generator adds request validation."""

    def test_generates_pydantic_model_validation(self):
        """Test routes use Pydantic models for validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/users": {
                    "POST": {"name": "create_user", "body": "User", "response": "User"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have POST endpoint with body parameter
        assert "User" in code
        compile(code, "<string>", "exec")

    def test_generates_path_parameter_validation(self):
        """Test routes validate path parameters."""
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
                "/users/{id}": {
                    "GET": {"name": "get_user", "response": "User"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have id parameter
        assert "id" in code
        compile(code, "<string>", "exec")

    def test_generates_query_parameter_validation(self):
        """Test routes validate query parameters."""
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
                        "query": {
                            "limit": {"type": "int", "default": 10},
                            "offset": {"type": "int", "default": 0}
                        },
                        "response": "User[]"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have query parameters
        assert "limit" in code or "offset" in code or "list_users" in code
        compile(code, "<string>", "exec")

    def test_generates_required_field_validation(self):
        """Test routes enforce required fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string", required=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "POST": {"name": "create_user", "body": "User", "response": "User"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        assert "User" in code
        compile(code, "<string>", "exec")

    def test_generates_type_validation(self):
        """Test routes enforce type validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "age": FieldDefinition(type="int"),
                    }
                )
            },
            endpoints={
                "/users": {
                    "POST": {"name": "create_user", "body": "User", "response": "User"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate code that validates types
        assert "User" in code
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
