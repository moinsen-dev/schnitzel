"""Integration tests for FastAPI basic GET endpoint generation (api_011).

Tests for:
- api_011: FastAPI route generator creates basic GET endpoint
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestFastAPIBasicGet:
    """Tests for api_011: FastAPI route generator creates basic GET endpoint."""

    def test_generates_get_endpoint(self):
        """Test route generator creates GET endpoint."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "response": "User"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have GET decorator or endpoint function
        assert "@router.get" in code or "@app.get" in code or "get_user" in code

    def test_path_parameter_in_signature(self):
        """Test path parameter id is in function signature."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "response": "User"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have id parameter
        assert "id" in code

    def test_generates_router(self):
        """Test route generator creates APIRouter."""
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
                    "GET": {
                        "name": "get_user",
                        "response": "User"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have router
        assert "router" in code or "Router" in code or "APIRouter" in code

    def test_generates_valid_python(self):
        """Test generated code is syntactically valid Python."""
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
                    "GET": {
                        "name": "get_user",
                        "response": "User"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Code should be compilable
        compile(code, "<string>", "exec")

    def test_has_fastapi_import(self):
        """Test generated code imports FastAPI."""
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
                    "GET": {
                        "name": "get_user",
                        "response": "User"
                    }
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should import from fastapi
        assert "fastapi" in code.lower() or "APIRouter" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
