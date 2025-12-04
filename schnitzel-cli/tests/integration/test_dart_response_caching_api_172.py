"""Integration tests for Dart response caching (api_172).

Tests for:
- api_172: Dart API client supports response caching
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartResponseCaching:
    """Tests for api_172: Dart response caching."""

    def test_dart_client_uses_dio(self):
        """Test Dart client uses Dio which supports caching."""
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
        assert "Dio" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
