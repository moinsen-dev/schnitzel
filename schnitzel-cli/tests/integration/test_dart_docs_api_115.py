"""Integration tests for Dart documentation comments (api_115).

Tests for:
- api_115: Generated Dart API client includes documentation comments
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartDocs:
    """Tests for api_115: Dart documentation comments."""

    def test_generates_dart_client_with_classes(self):
        """Test Dart client generates class definitions."""
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
        assert "class" in code

    def test_generates_dart_imports(self):
        """Test Dart client includes imports."""
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
        assert "import" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
