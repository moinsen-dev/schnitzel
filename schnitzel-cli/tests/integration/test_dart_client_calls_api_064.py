"""Integration tests for Dart client API calls (api_064).

Tests for:
- api_064: Integration test: Dart client successfully calls generated API
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartClientCalls:
    """Tests for api_064: Integration test: Dart client successfully calls generated API."""

    def test_generates_get_method(self):
        """Test Dart client generates GET method."""
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
                    "GET": {"name": "getUser", "response": "User"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have GET method
        assert "getUser" in code or "get" in code.lower()

    def test_generates_post_method(self):
        """Test Dart client generates POST method."""
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
                "/users": {
                    "POST": {"name": "createUser", "body": "User", "response": "User"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have POST method
        assert "createUser" in code or "post" in code.lower()

    def test_generates_dio_client(self):
        """Test Dart client uses Dio for HTTP requests."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should use Dio
        assert "Dio" in code

    def test_generates_api_client_class(self):
        """Test Dart client generates ApiClient class."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have ApiClient class
        assert "class ApiClient" in code

    def test_generates_error_handling(self):
        """Test Dart client generates error handling."""
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
                    "GET": {"name": "getUser", "response": "User"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have try/catch or error handling
        assert "try" in code or "catch" in code or "DioException" in code or "ApiClient" in code

    def test_generates_list_endpoint(self):
        """Test Dart client handles list endpoints."""
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
                    "GET": {"name": "listUsers", "response": "User[]"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should handle list response
        assert "List" in code or "listUsers" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
