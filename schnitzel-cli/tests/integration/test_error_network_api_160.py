"""Integration tests for graceful network error handling (api_160).

Tests for:
- api_160: Error handling: Graceful failure on network issues
"""

import pytest
from schnitzel.generators.dart.api_client import DartApiClientGenerator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


class TestErrorNetwork:
    """Tests for api_160: Network error handling."""

    def test_dart_client_has_error_handling(self):
        """Test Dart client includes error handling."""
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
        assert "Exception" in code or "Error" in code

    def test_dart_client_has_retry_interceptor(self):
        """Test Dart client includes retry logic."""
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
        assert "RetryInterceptor" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
