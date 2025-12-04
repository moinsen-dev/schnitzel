"""Integration tests for F032: Dart type mapping in Freezed model generator.

Tests the DartModelGenerator's ability to correctly map all schema types
to Dart types, including handling list types, enums, and complex types.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart import DartModelGenerator


class TestDartTypeMappingBasic:
    """Test basic type mappings from schema to Dart."""

    def test_string_type_maps_to_dart_string(self):
        """Test that string type maps to Dart String."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have required String field
        assert "required String name," in code
        assert "class User" in code

    def test_uuid_type_maps_to_dart_string(self):
        """Test that uuid type maps to Dart String (UUIDs are strings in Dart)."""
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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # UUID should map to String in Dart
        assert "required String id," in code

    def test_datetime_type_maps_to_dart_datetime(self):
        """Test that datetime type maps to Dart DateTime."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should map to DateTime
        assert "required DateTime createdAt," in code

    def test_json_type_maps_to_map_string_dynamic(self):
        """Test that json type maps to Map<String, dynamic>."""
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


class TestDartTypeMappingListTypes:
    """Test list type mappings with proper inner type handling."""

    def test_list_type_maps_correctly(self):
        """Test that list types map correctly with inner types."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "tags": FieldDefinition(type="list<string>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should map to List<String>
        assert "required List<String> tags," in code

    def test_list_of_integers(self):
        """Test that list<int> maps to List<int>."""
        schema = SchnitzelSchema(
            models={
                "Data": Model(
                    name="Data",
                    fields={
                        "numbers": FieldDefinition(type="list<int>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required List<int> numbers," in code

    def test_vector_type_maps_to_list_double(self):
        """Test that vector type maps to List<double>."""
        schema = SchnitzelSchema(
            models={
                "Embedding": Model(
                    name="Embedding",
                    fields={
                        "vector": FieldDefinition(type="vector"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Vector should map to List<double>
        assert "required List<double> vector," in code

    def test_bytes_type_maps_to_list_int(self):
        """Test that bytes type maps to List<int>."""
        schema = SchnitzelSchema(
            models={
                "File": Model(
                    name="File",
                    fields={
                        "data": FieldDefinition(type="bytes"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Bytes should map to List<int>
        assert "required List<int> data," in code


class TestDartTypeMappingAllBasicTypes:
    """Test all basic type mappings."""

    def test_all_basic_types_mapped(self):
        """Test that all basic types from DART_TYPE_MAP are correctly mapped."""
        schema = SchnitzelSchema(
            models={
                "AllTypes": Model(
                    name="AllTypes",
                    fields={
                        "stringField": FieldDefinition(type="string"),
                        "strField": FieldDefinition(type="str"),
                        "intField": FieldDefinition(type="int"),
                        "integerField": FieldDefinition(type="integer"),
                        "floatField": FieldDefinition(type="float"),
                        "doubleField": FieldDefinition(type="double"),
                        "boolField": FieldDefinition(type="bool"),
                        "booleanField": FieldDefinition(type="boolean"),
                        "datetimeField": FieldDefinition(type="datetime"),
                        "dateField": FieldDefinition(type="date"),
                        "uuidField": FieldDefinition(type="uuid"),
                        "textField": FieldDefinition(type="text"),
                        "jsonField": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check all type mappings
        assert "required String stringField," in code
        assert "required String strField," in code
        assert "required int intField," in code
        assert "required int integerField," in code
        assert "required double floatField," in code
        assert "required double doubleField," in code
        assert "required bool boolField," in code
        assert "required bool booleanField," in code
        assert "required DateTime datetimeField," in code
        assert "required DateTime dateField," in code
        assert "required String uuidField," in code
        assert "required String textField," in code
        assert "required Map<String, dynamic> jsonField," in code

    def test_int_vs_integer_mapping(self):
        """Test that both 'int' and 'integer' map to Dart int."""
        schema = SchnitzelSchema(
            models={
                "Counter": Model(
                    name="Counter",
                    fields={
                        "count1": FieldDefinition(type="int"),
                        "count2": FieldDefinition(type="integer"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required int count1," in code
        assert "required int count2," in code

    def test_float_vs_double_mapping(self):
        """Test that both 'float' and 'double' map to Dart double."""
        schema = SchnitzelSchema(
            models={
                "Measurement": Model(
                    name="Measurement",
                    fields={
                        "value1": FieldDefinition(type="float"),
                        "value2": FieldDefinition(type="double"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required double value1," in code
        assert "required double value2," in code

    def test_bool_vs_boolean_mapping(self):
        """Test that both 'bool' and 'boolean' map to Dart bool."""
        schema = SchnitzelSchema(
            models={
                "Feature": Model(
                    name="Feature",
                    fields={
                        "enabled1": FieldDefinition(type="bool"),
                        "enabled2": FieldDefinition(type="boolean"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required bool enabled1," in code
        assert "required bool enabled2," in code

    def test_datetime_vs_date_mapping(self):
        """Test that both 'datetime' and 'date' map to Dart DateTime."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "timestamp": FieldDefinition(type="datetime"),
                        "eventDate": FieldDefinition(type="date"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required DateTime timestamp," in code
        assert "required DateTime eventDate," in code


class TestDartEnumHandling:
    """Test enum type handling in Dart."""

    def test_enum_type_maps_to_string(self):
        """Test that enum type maps to String in Dart."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "processing", "completed"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Enum should map to String in Dart
        assert "required String status," in code

    def test_optional_enum_field(self):
        """Test optional enum field handling."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"],
                            optional=True
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Optional enum should be String?
        assert "String? role," in code
        assert "required" not in code.split("role")[0].split("\n")[-1]


class TestDartOptionalFields:
    """Test optional field handling."""

    def test_optional_string_field(self):
        """Test that optional string fields are nullable."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "bio": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Optional field should be nullable and not required
        assert "String? bio," in code
        # Should not have 'required' keyword
        assert "required String? bio," not in code

    def test_optional_datetime_field(self):
        """Test optional DateTime field."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "publishedAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "DateTime? publishedAt," in code

    def test_required_vs_optional_fields(self):
        """Test mix of required and optional fields."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required fields should have 'required' keyword
        assert "required String id," in code
        assert "required String name," in code

        # Optional field should be nullable and not required
        assert "String? description," in code
        assert "required String? description," not in code


class TestDartGeneratedStructure:
    """Test the overall structure of generated Dart code."""

    def test_freezed_imports_present(self):
        """Test that necessary Freezed imports are present."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have Freezed imports
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code

    def test_part_directives_present(self):
        """Test that part directives are generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have part directives for Freezed and json_serializable
        # When generating all models to one file, uses models.freezed.dart and models.g.dart
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code

    def test_freezed_annotation_present(self):
        """Test that @freezed annotation is present."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "@freezed" in code
        assert "class Product with _$Product {" in code

    def test_from_json_factory_present(self):
        """Test that fromJson factory is generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code

    def test_factory_constructor_structure(self):
        """Test the structure of the factory constructor."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid"),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have factory constructor with all fields
        assert "const factory Product({" in code
        assert "required String id," in code
        assert "required String name," in code
        assert "required double price," in code
        assert "}) = _Product;" in code


class TestDartComplexScenarios:
    """Test complex scenarios with multiple types and fields."""

    def test_multiple_models_with_different_types(self):
        """Test generating multiple models with various field types."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int", optional=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "content": FieldDefinition(type="text"),
                        "tags": FieldDefinition(type="list<string>"),
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check User model
        assert "class User with _$User {" in code
        assert "required String id," in code
        assert "required String name," in code
        assert "int? age," in code

        # Check Post model
        assert "class Post with _$Post {" in code
        assert "required String title," in code
        assert "required String content," in code
        assert "required List<String> tags," in code
        assert "required DateTime createdAt," in code

    def test_model_with_all_list_variants(self):
        """Test model with different list type variants."""
        schema = SchnitzelSchema(
            models={
                "Data": Model(
                    name="Data",
                    fields={
                        "strings": FieldDefinition(type="list<string>"),
                        "integers": FieldDefinition(type="list<int>"),
                        "floats": FieldDefinition(type="list<float>"),
                        "vector": FieldDefinition(type="vector"),
                        "bytes": FieldDefinition(type="bytes"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required List<String> strings," in code
        assert "required List<int> integers," in code
        assert "required List<double> floats," in code
        assert "required List<double> vector," in code
        assert "required List<int> bytes," in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
