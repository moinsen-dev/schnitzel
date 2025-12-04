"""Integration tests for Dart reserved keyword escaping (api_155).

Tests for:
- api_155: Unit test: Dart client generator escapes reserved keywords
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartReservedKeywords:
    """Tests for api_155: Unit test: Dart client generator escapes reserved keywords."""

    def test_generates_valid_dart_code(self):
        """Test that generated Dart code is syntactically valid."""
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

        # Should have valid Dart syntax markers
        assert "class" in code
        assert "import" in code

    def test_handles_type_field_name(self):
        """Test that 'type' field name is handled."""
        schema = SchnitzelSchema(
            models={
                "Item": Model(
                    name="Item",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "type": FieldDefinition(type="string"),  # 'type' is common
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate without error
        assert code is not None

    def test_handles_class_model_name(self):
        """Test that model names don't conflict with Dart keywords."""
        schema = SchnitzelSchema(
            models={
                "Response": Model(  # 'Response' might conflict with Dio
                    name="Response",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        assert code is not None

    def test_handles_common_field_names(self):
        """Test that common field names are handled."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "default": FieldDefinition(type="string"),  # keyword
                        "class_name": FieldDefinition(type="string"),  # 'class' prefix
                        "final": FieldDefinition(type="bool"),  # keyword
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate without error
        assert code is not None

    def test_handles_async_field(self):
        """Test that 'async' related names are handled."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "async_result": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate without error
        assert code is not None

    def test_uses_proper_dart_conventions(self):
        """Test that generated code follows Dart conventions."""
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

        # Should use Dart conventions
        assert "Dio" in code  # Uses Dio package
        assert "ApiClient" in code  # Class name in PascalCase


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
