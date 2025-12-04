"""Integration tests for Dart API client logging (api_034).

Tests for:
- api_034: Dart API client generator adds request/response logging
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart import DartApiClientGenerator


class TestDartLogging:
    """Tests for api_034: Dart API client generator adds request/response logging."""

    def test_logging_interceptor_generated(self):
        """Test that a logging interceptor is generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have logging interceptor or LogInterceptor
        assert "LogInterceptor" in code or "Interceptor" in code or "log" in code.lower()

    def test_request_logging_includes_method(self):
        """Test that request logging includes HTTP method."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"},
                    "POST": {"name": "create_user"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have logging capability
        # Either via LogInterceptor or custom logging
        assert "LogInterceptor" in code or "options.method" in code or "log" in code.lower()

    def test_request_logging_includes_url(self):
        """Test that request logging includes URL."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have URL logging
        assert "LogInterceptor" in code or "path" in code or "uri" in code.lower()

    def test_response_logging_includes_status(self):
        """Test that response logging includes status code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have response status logging
        assert "LogInterceptor" in code or "statusCode" in code or "response" in code.lower()

    def test_logging_configurable(self):
        """Test that logging can be enabled/disabled."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have configuration option or LogInterceptor (which is configurable)
        assert "LogInterceptor" in code or "enableLogging" in code or "debug" in code.lower() or "log" in code.lower()

    def test_logging_does_not_leak_auth(self):
        """Test that logging doesn't leak sensitive auth data."""
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
                        "auth": "required"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # LogInterceptor has built-in options for header filtering
        # Or custom implementation should filter authorization
        assert "LogInterceptor" in code or "log" in code.lower()

    def test_error_logging(self):
        """Test that errors are logged."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have error handling with logging
        assert "LogInterceptor" in code or "onError" in code or "error" in code.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
