"""Integration tests for F080: Dart generator handles models with nested JSON fields.

Tests that the Dart model generator correctly handles fields of type 'json',
which maps to Map<String, dynamic> in Dart (equivalent to dict in Python).
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartJsonFieldGeneration:
    """Test JSON field generation in Dart models."""

    def test_json_field_generates(self):
        """Test that a model with a json field generates correctly."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "settings": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should generate a Config model
        assert "class Config with _$Config" in code
        # Should have a json field
        assert "settings" in code

    def test_json_type_is_map(self):
        """Test that json type becomes Map<String, dynamic> in Dart."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "settings": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # JSON should map to Map<String, dynamic>
        assert "required Map<String, dynamic> settings," in code

    def test_json_field_with_default(self):
        """Test that json field with default value generates correctly."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "metadata": FieldDefinition(type="json", default={}),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @Default annotation with empty map
        assert "@Default({}) Map<String, dynamic> metadata," in code
        # Should NOT have 'required' keyword when default is provided
        assert "required" not in code.split("metadata")[0].split("\n")[-1]

    def test_optional_json_field(self):
        """Test that optional json field becomes nullable Map."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "preferences": FieldDefinition(type="json", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Optional json should be nullable and not required
        assert "Map<String, dynamic>? preferences," in code
        assert "required Map<String, dynamic>? preferences," not in code

    def test_required_json_field(self):
        """Test that required json field is properly marked."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "data": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required json field should have 'required' keyword
        assert "required Map<String, dynamic> data," in code

    def test_multiple_json_fields(self):
        """Test model with multiple json fields."""
        schema = SchnitzelSchema(
            models={
                "Application": Model(
                    name="Application",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "config": FieldDefinition(type="json"),
                        "metadata": FieldDefinition(type="json", optional=True),
                        "defaults": FieldDefinition(type="json", default={}),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required json field
        assert "required Map<String, dynamic> config," in code
        # Optional json field
        assert "Map<String, dynamic>? metadata," in code
        # Json field with default
        assert "@Default({}) Map<String, dynamic> defaults," in code

    def test_json_field_with_snake_case_conversion(self):
        """Test that json fields with camelCase names get @JsonKey annotation."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "apiSettings": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @JsonKey annotation for snake_case conversion
        assert "@JsonKey(name: 'api_settings')" in code
        assert "required Map<String, dynamic> apiSettings," in code


class TestDartJsonFieldsComplex:
    """Test JSON fields in complex scenarios."""

    def test_json_field_in_model_with_mixed_types(self):
        """Test json field alongside other field types."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int", optional=True),
                        "preferences": FieldDefinition(type="json", default={}),
                        "metadata": FieldDefinition(type="json", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all fields are present with correct types
        assert "required String id," in code
        assert "required String name," in code
        assert "required String email," in code
        assert "int? age," in code
        assert "@Default({}) Map<String, dynamic> preferences," in code
        assert "Map<String, dynamic>? metadata," in code

    def test_multiple_models_with_json_fields(self):
        """Test multiple models containing json fields."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "settings": FieldDefinition(type="json"),
                    }
                ),
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "preferences": FieldDefinition(type="json", optional=True),
                    }
                ),
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify both models have json fields
        assert "class Config with _$Config" in code
        assert "required Map<String, dynamic> settings," in code
        assert "class User with _$User" in code
        assert "Map<String, dynamic>? preferences," in code

    def test_json_field_with_json_serialization(self):
        """Test that json fields work with fromJson factory."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "data": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have fromJson factory
        assert "factory Document.fromJson(Map<String, dynamic> json) => _$DocumentFromJson(json);" in code
        # Should have the json field
        assert "required Map<String, dynamic> data," in code


class TestDartJsonFieldEdgeCases:
    """Test edge cases for JSON field handling."""

    def test_json_field_only_model(self):
        """Test a model with only a json field (no id)."""
        schema = SchnitzelSchema(
            models={
                "Payload": Model(
                    name="Payload",
                    fields={
                        "data": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should generate successfully
        assert "class Payload with _$Payload" in code
        assert "required Map<String, dynamic> data," in code

    def test_json_field_case_sensitivity(self):
        """Test that 'json' type is case-insensitive."""
        # The _get_dart_type method uses .lower() for comparison
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "settings": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should work with lowercase 'json'
        assert "required Map<String, dynamic> settings," in code

    def test_json_field_with_default_and_optional(self):
        """Test that json field with both default and optional uses default (non-nullable)."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "settings": FieldDefinition(type="json", optional=True, default={}),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # When a default is provided, field should NOT be nullable
        assert "@Default({}) Map<String, dynamic> settings," in code
        # Should NOT be nullable (no '?')
        assert "Map<String, dynamic>? settings" not in code


class TestDartJsonFieldImports:
    """Test that proper imports are generated for json fields."""

    def test_json_field_requires_no_additional_imports(self):
        """Test that json fields don't require additional imports beyond standard Freezed imports."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "settings": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have standard Freezed imports
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code
        # Map<String, dynamic> is a Dart built-in, no additional import needed

    def test_json_field_with_part_directives(self):
        """Test that json fields work with generated part files."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "settings": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have part directives
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
