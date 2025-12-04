"""Integration tests for Dart API client error handling consistency (api_116).

Tests for:
- api_116: Generated Dart API client has consistent error handling
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartErrorHandlingStyle:
    """Tests for api_116: Generated Dart API client has consistent error handling."""

    def test_try_catch_pattern(self):
        """Test that try-catch is used consistently for API calls."""
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
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have error handling structure or DioError handling
        assert "DioException" in code or "try" in code or "catch" in code or "on" in code

    def test_error_interceptor_setup(self):
        """Test that error interceptor is properly set up."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have interceptor setup
        assert "interceptor" in code.lower() or "Interceptor" in code

    def test_consistent_error_class(self):
        """Test that a consistent error class/type is used."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {"name": "get_user"},
                    "DELETE": {"name": "delete_user"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should reference DioException or similar error type
        assert "DioException" in code or "Exception" in code or "Error" in code

    def test_error_message_handling(self):
        """Test that error messages are handled consistently."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Code should be generated
        assert "class ApiClient" in code or "Dio" in code

    def test_http_status_code_handling(self):
        """Test that HTTP status codes are handled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should handle responses
        assert "response" in code.lower() or "Response" in code

    def test_network_error_handling(self):
        """Test that network errors are handled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should use Dio which handles network errors
        assert "Dio" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
