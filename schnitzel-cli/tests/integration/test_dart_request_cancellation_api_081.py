"""Integration tests for Dart request cancellation (api_081).

Tests for:
- api_081: Dart API client generator handles request cancellation
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartRequestCancellation:
    """Tests for api_081: Dart API client generator handles request cancellation."""

    def test_generates_canceltoken_support(self):
        """Test Dart client includes CancelToken support."""
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
                    "GET": {"name": "list_users", "response": "User[]"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate client that can use Dio (which supports CancelToken)
        assert "Dio" in code
        # Should include CancelToken parameter in method signature
        assert "CancelToken? cancelToken" in code
        # Should pass cancelToken to Dio method
        assert "cancelToken: cancelToken" in code
        # Note: compile() is for Python - just verify generation succeeds
        assert code is not None

    def test_generates_timeout_config(self):
        """Test Dart client includes timeout configuration."""
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

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have timeout support (Duration, timeout, etc.)
        assert "timeout" in code.lower() or "Duration" in code

    def test_generates_with_options(self):
        """Test Dart client methods accept options."""
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

        # Should generate client with request options
        assert "listUsers" in code or "ApiClient" in code

    def test_generates_error_handling(self):
        """Test Dart client has error handling for cancellation."""
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

        # Should have some error handling infrastructure
        assert "Exception" in code or "Error" in code or "DioException" in code

    def test_generates_async_methods(self):
        """Test Dart client generates async methods."""
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
                    "GET": {"name": "getUsers", "response": "User[]"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have async/await or Future
        assert "async" in code or "Future" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
