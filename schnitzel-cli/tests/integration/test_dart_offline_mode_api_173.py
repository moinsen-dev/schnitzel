"""Integration tests for Dart offline mode (api_173).

Tests for:
- api_173: Dart API client supports offline mode
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartOfflineMode:
    """Tests for api_173: Dart offline mode support."""

    def test_dart_client_has_interceptors(self):
        """Test Dart client has interceptors for offline support."""
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
        assert "Interceptor" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
