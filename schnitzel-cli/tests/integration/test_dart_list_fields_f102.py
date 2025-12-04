"""Integration tests for F102: Dart generator handles List fields (array type).

Test Requirements:
- test_dart_list_field - verify list<string> generates List<String>
- test_dart_list_type - verify list<int> generates List<int>
- test_dart_list_elements - verify various element types work
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartListFields:
    """Test Dart model generator with list/array fields."""

    def test_dart_list_field(self):
        """Test that list<string> field generates List<String> in Dart."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify List<String> type is generated
        assert "required List<String> tags" in code or "List<String> tags" in code

    def test_dart_list_type(self):
        """Test that list<int> generates List<int> type in Dart."""
        schema = SchnitzelSchema(
            models={
                "Survey": Model(
                    name="Survey",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "ratings": FieldDefinition(type="list<int>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify List<int> type is generated
        assert "required List<int> ratings" in code or "List<int> ratings" in code

    def test_dart_list_elements(self):
        """Test that list fields work with various element types in Dart."""
        schema = SchnitzelSchema(
            models={
                "Analytics": Model(
                    name="Analytics",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                        "scores": FieldDefinition(type="list<float>"),
                        "counts": FieldDefinition(type="list<int>"),
                        "flags": FieldDefinition(type="list<bool>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all list types are generated correctly
        # Note: In Dart, float maps to double
        assert "List<String> tags" in code
        assert "List<double> scores" in code
        assert "List<int> counts" in code
        assert "List<bool> flags" in code

    def test_dart_list_field_optional(self):
        """Test that optional list fields generate correctly in Dart."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify optional list type with nullable syntax
        assert "List<String>? tags" in code
        # Should not have required keyword
        assert "required List<String>? tags" not in code

    def test_dart_list_field_with_default(self):
        """Test that list fields with default values generate correctly in Dart."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "features": FieldDefinition(type="list<string>", default=[]),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify list with default empty list using @Default annotation
        assert "@Default([]) List<String> features" in code

    def test_dart_list_uuid_type(self):
        """Test that list<uuid> generates List<String> in Dart (UUIDs are strings)."""
        schema = SchnitzelSchema(
            models={
                "Relationships": Model(
                    name="Relationships",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "friend_ids": FieldDefinition(type="list<uuid>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify List<String> type (UUIDs are strings in Dart)
        assert "List<String> friend_ids" in code

    def test_dart_list_datetime_type(self):
        """Test that list<datetime> generates List<DateTime> in Dart."""
        schema = SchnitzelSchema(
            models={
                "Timeline": Model(
                    name="Timeline",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "timestamps": FieldDefinition(type="list<datetime>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify List<DateTime> type
        assert "List<DateTime> timestamps" in code

    def test_dart_multiple_list_fields(self):
        """Test that multiple list fields in same model work correctly in Dart."""
        schema = SchnitzelSchema(
            models={
                "DataSet": Model(
                    name="DataSet",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                        "values": FieldDefinition(type="list<float>"),
                        "ids": FieldDefinition(type="list<uuid>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all list fields are present
        assert "List<String> tags" in code
        assert "List<double> values" in code  # float -> double in Dart
        assert "List<String> ids" in code  # uuid -> String in Dart

    def test_dart_list_field_required(self):
        """Test that required list fields have required keyword in Dart."""
        schema = SchnitzelSchema(
            models={
                "RequiredList": Model(
                    name="RequiredList",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "required_tags": FieldDefinition(type="list<string>", required=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify required list field with required keyword
        assert "required List<String> required_tags" in code

    def test_dart_list_with_default_values(self):
        """Test that list fields with non-empty default values generate correctly."""
        schema = SchnitzelSchema(
            models={
                "Defaults": Model(
                    name="Defaults",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", default=["default", "tags"]),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify list with default values using @Default annotation
        assert "@Default(['default', 'tags']) List<String> tags" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
