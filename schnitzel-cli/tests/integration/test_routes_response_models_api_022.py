"""Integration tests for route response models with status codes (api_022).

Tests for:
- api_022: FastAPI route generator handles response models with status codes
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesResponseModels:
    """Tests for api_022: FastAPI route generator handles response models with status codes."""

    def test_response_model_200(self):
        """Test that 200 response includes response model."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "response": {200: {"type": "User"}}
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have return type as User
        assert "-> User" in code or "User" in code

    def test_response_model_201_created(self):
        """Test that 201 Created response is handled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "POST": {
                        "name": "create_user",
                        "response": {201: {"type": "User"}}
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have status_code=201
        assert "status_code=201" in code

    def test_response_model_204_no_content(self):
        """Test that 204 No Content is handled for DELETE."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "DELETE": {
                        "name": "delete_user",
                        "response": {204: {}}
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have status_code=204
        assert "status_code=204" in code

    def test_response_model_list_type(self):
        """Test that list response types are handled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "response": {200: {"type": "list[User]"}}
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have list return type
        assert "list[User]" in code or "List[User]" in code

    def test_response_model_paginated(self):
        """Test that paginated response types are handled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "response": {200: {"type": "PaginatedResponse<User>"}}
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should handle generic response type
        assert "PaginatedResponse" in code

    def test_multiple_response_codes(self):
        """Test that multiple response codes are handled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "response": {
                            200: {"type": "User"},
                            404: {"type": "ErrorResponse"}
                        }
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Primary response (200) should be used for return type
        assert "User" in code

    def test_response_model_import(self):
        """Test that response model is added to imports."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "response": {200: {"type": "User"}}
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should import the response model
        assert "from .models import" in code and "User" in code

    def test_default_status_codes(self):
        """Test that default status codes are used when not specified."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "POST": {
                        "name": "create_user"
                    }
                },
                "/users/{id}": {
                    "DELETE": {
                        "name": "delete_user"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # POST should default to 201
        assert "status_code=201" in code
        # DELETE should default to 204
        assert "status_code=204" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
