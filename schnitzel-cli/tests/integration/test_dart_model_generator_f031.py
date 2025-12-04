"""Integration tests for F031: Dart Freezed model generator.

Tests the generation of Dart Freezed models from Schnitzel schemas.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartFreezedBasicGeneration:
    """Test basic Dart Freezed model generation."""

    def test_simple_model_generates_freezed_class(self):
        """Test that a simple model generates a proper Freezed class structure."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @freezed annotation
        assert "@freezed" in code
        
        # Verify class declaration with mixin
        assert "class User with _$User {" in code
        
        # Verify factory constructor
        assert "const factory User({" in code
        assert "}) = _User;" in code
        
        # Verify fromJson factory
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code

    def test_imports_and_parts_correct(self):
        """Test that generated code includes correct imports and part directives."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify freezed_annotation import
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        
        # Verify part directives
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code
        
        # Verify imports come before part directives
        import_pos = code.find("import 'package:freezed_annotation")
        part_pos = code.find("part 'models.freezed.dart'")
        assert import_pos < part_pos

    def test_basic_fields_in_factory(self):
        """Test that basic fields are correctly included in factory constructor."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all fields are in factory constructor
        assert "required String id" in code
        assert "required String name" in code
        assert "required int age" in code


class TestDartTypeMapping:
    """Test Dart type mapping from schema types."""

    def test_string_type_maps_to_string(self):
        """Test that string type maps to Dart String."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
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

        assert "required String name" in code

    def test_uuid_type_maps_to_string(self):
        """Test that uuid type maps to Dart String."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
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

        assert "required String id" in code

    def test_int_type_maps_to_int(self):
        """Test that int type maps to Dart int."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "count": FieldDefinition(type="int"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required int count" in code

    def test_float_type_maps_to_double(self):
        """Test that float type maps to Dart double."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required double price" in code

    def test_bool_type_maps_to_bool(self):
        """Test that bool type maps to Dart bool."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "is_active": FieldDefinition(type="bool"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required bool is_active" in code

    def test_datetime_type_maps_to_datetime(self):
        """Test that datetime type maps to Dart DateTime."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "created_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required DateTime created_at" in code

    def test_json_type_maps_to_map(self):
        """Test that json type maps to Dart Map<String, dynamic>."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "metadata": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required Map<String, dynamic> metadata" in code


class TestDartOptionalFields:
    """Test optional field handling in Dart Freezed models."""

    def test_optional_field_is_nullable(self):
        """Test that optional fields are marked as nullable with ?."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "nickname": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required field should not be nullable
        assert "required String id" in code
        
        # Optional field should be nullable and not required
        assert "String? nickname" in code
        assert "required String? nickname" not in code

    def test_multiple_optional_fields(self):
        """Test that multiple optional fields are handled correctly."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "nickname": FieldDefinition(type="string", optional=True),
                        "bio": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All optional fields should be nullable
        assert "String? nickname" in code
        assert "String? bio" in code
        assert "int? age" in code


class TestDartDefaultValues:
    """Test default value handling in Dart Freezed models."""

    def test_string_default_uses_single_quotes(self):
        """Test that string defaults use Dart-style single quotes with @Default annotation."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "status": FieldDefinition(type="string", default="active"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @Default annotation with single quotes (Freezed pattern)
        assert "@Default('active') String status" in code

    def test_numeric_defaults_unquoted(self):
        """Test that numeric defaults are not quoted with @Default annotation."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "count": FieldDefinition(type="int", default=0),
                        "price": FieldDefinition(type="float", default=9.99),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify int default is unquoted in @Default annotation
        assert "@Default(0) int count" in code

        # Verify float default is unquoted in @Default annotation
        assert "@Default(9.99) double price" in code

    def test_boolean_defaults_lowercase(self):
        """Test that boolean defaults use Dart lowercase true/false with @Default annotation."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "is_active": FieldDefinition(type="bool", default=True),
                        "is_deleted": FieldDefinition(type="bool", default=False),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify lowercase true/false in @Default annotation (Dart convention)
        assert "@Default(true) bool is_active" in code
        assert "@Default(false) bool is_deleted" in code


class TestDartMultipleModels:
    """Test generation of multiple models."""

    def test_multiple_models_generated(self):
        """Test that multiple models are correctly generated."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "title": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify both models are generated
        assert "@freezed" in code
        assert "class User with _$User {" in code
        assert "class Post with _$Post {" in code
        
        # Verify both have factory constructors
        assert "const factory User({" in code
        assert "const factory Post({" in code
        
        # Verify both have fromJson factories
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code
        assert "factory Post.fromJson(Map<String, dynamic> json) => _$PostFromJson(json);" in code


class TestDartEdgeCases:
    """Test edge cases in Dart model generation."""

    def test_empty_model_generates_valid_class(self):
        """Test that a model with no fields generates valid code."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "EmptyModel": Model(
                    name="EmptyModel",
                    fields={}
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should still generate valid Freezed class structure
        assert "@freezed" in code
        assert "class EmptyModel with _$EmptyModel {" in code
        assert "const factory EmptyModel() = _EmptyModel;" in code
        assert "factory EmptyModel.fromJson(Map<String, dynamic> json) => _$EmptyModelFromJson(json);" in code

    def test_snake_case_field_names(self):
        """Test that snake_case field names don't need @JsonKey annotation."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "user_id": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify fields are included without @JsonKey (already in snake_case)
        assert "String user_id" in code
        assert "DateTime created_at" in code
        # No @JsonKey needed since fields are already in snake_case
        assert "@JsonKey(name: 'user_id')" not in code
        assert "@JsonKey(name: 'created_at')" not in code

    def test_camel_case_field_names_need_json_key(self):
        """Test that camelCase field names get @JsonKey annotation."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "userId": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @JsonKey annotations for camelCase fields (convert to snake_case)
        assert "@JsonKey(name: 'user_id')" in code
        assert "@JsonKey(name: 'created_at')" in code
        # Field names remain camelCase in Dart
        assert "String userId" in code
        assert "DateTime createdAt" in code
