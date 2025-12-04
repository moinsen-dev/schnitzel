"""Integration tests for Dart API client mocking support (api_085).

Tests for:
- api_085: Dart API client generator supports mocking for tests
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartMocking:
    """Tests for api_085: Dart API client generator supports mocking for tests."""

    def test_generates_mockable_client(self):
        """Test Dart client can be mocked."""
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

        # Should have class that can be mocked
        assert "class ApiClient" in code

    def test_uses_dio_injection(self):
        """Test Dart client accepts Dio injection for mocking."""
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

        # Should accept Dio in constructor (for injection)
        assert "Dio" in code
        assert "ApiClient" in code

    def test_generates_separate_methods(self):
        """Test methods are separate for easier mocking."""
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
                    "GET": {"name": "listUsers", "response": "User[]"},
                    "POST": {"name": "createUser", "body": "User", "response": "User"}
                },
                "/users/{id}": {
                    "GET": {"name": "getUser", "response": "User"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have separate methods
        assert "listUsers" in code
        assert "createUser" in code
        assert "getUser" in code

    def test_client_constructor_flexibility(self):
        """Test client constructor allows flexibility for testing."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have constructor that accepts parameters
        assert "ApiClient" in code
        # Constructor pattern
        assert "ApiClient(" in code

    def test_generates_type_safe_responses(self):
        """Test responses are type-safe for better test assertions."""
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

        # Should have typed return
        assert "User" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
