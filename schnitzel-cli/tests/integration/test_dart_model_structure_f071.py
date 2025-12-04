"""Integration tests for F071: Generated Dart models can be instantiated and serialized.

Test Requirements:
1. test_dart_model_has_factory_constructor - factory constructor exists
2. test_dart_model_has_from_json - fromJson factory present
3. test_dart_model_has_freezed_annotation - @freezed annotation
4. test_dart_model_has_part_directives - part 'models.freezed.dart' and 'models.g.dart'
5. test_dart_model_fields_have_correct_types - String, int, bool etc. mapped correctly
6. test_dart_model_optional_fields_are_nullable - optional fields use Type?
7. test_dart_model_with_relationships - relationship fields generate correctly

NOTE: Cannot actually run Dart code in tests, but can verify structure for correct generation.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartModelFactoryConstructor:
    """Test that generated Dart models have correct factory constructor structure."""

    def test_dart_model_has_factory_constructor(self):
        """Test that a factory constructor exists with proper structure."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Factory Constructor:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify factory constructor structure
        assert "const factory User({" in code, "Should have const factory constructor"
        assert "}) = _User;" in code, "Should have factory redirect to private constructor"

        # Verify fields are in the factory constructor
        assert "required String id," in code, "id field should be in constructor"
        assert "required String name," in code, "name field should be in constructor"
        assert "required String email," in code, "email field should be in constructor"

    def test_factory_constructor_with_optional_fields(self):
        """Test factory constructor handles optional fields correctly."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="string", optional=True),
                        "price": FieldDefinition(type="float", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Factory with Optional Fields:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Required fields
        assert "required String id," in code
        assert "required String name," in code

        # Optional fields should be nullable
        assert "String? description," in code
        assert "double? price," in code

        # Should still have factory structure
        assert "const factory Product({" in code
        assert "}) = _Product;" in code

    def test_factory_constructor_with_default_values(self):
        """Test factory constructor with default values uses @Default annotation."""
        schema = SchnitzelSchema(
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "theme": FieldDefinition(type="string", default="light"),
                        "max_items": FieldDefinition(type="int", default=10),
                        "enabled": FieldDefinition(type="bool", default=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Factory with Defaults:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify @Default annotations
        assert "@Default('light')" in code, "Should have @Default annotation for string"
        assert "@Default(10)" in code, "Should have @Default annotation for int"
        assert "@Default(true)" in code, "Should have @Default annotation for bool"

        # Fields with defaults should not be required
        assert "required String theme" not in code
        assert "required int max_items" not in code
        assert "required bool enabled" not in code


class TestDartModelFromJson:
    """Test that generated Dart models have fromJson factory method."""

    def test_dart_model_has_from_json(self):
        """Test that fromJson factory method is present."""
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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - fromJson:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify fromJson factory
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code, \
            "Should have fromJson factory method"

    def test_from_json_for_multiple_models(self):
        """Test that each model gets its own fromJson factory."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Multiple Models fromJson:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Each model should have its own fromJson
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code
        assert "factory Post.fromJson(Map<String, dynamic> json) => _$PostFromJson(json);" in code


class TestDartModelFreezedAnnotation:
    """Test that generated Dart models have @freezed annotation."""

    def test_dart_model_has_freezed_annotation(self):
        """Test that @freezed annotation is present."""
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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - @freezed:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify @freezed annotation
        assert "@freezed" in code, "Should have @freezed annotation"

        # Verify class declaration with mixin
        assert "class User with _$User {" in code, "Should have class with mixin"

    def test_freezed_annotation_for_all_models(self):
        """Test that all models get @freezed annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
                "Comment": Model(
                    name="Comment",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Multiple @freezed:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Each model should have @freezed
        code_lines = code.split('\n')
        freezed_count = sum(1 for line in code_lines if line.strip() == "@freezed")
        assert freezed_count == 3, f"Should have 3 @freezed annotations, found {freezed_count}"


class TestDartModelPartDirectives:
    """Test that generated Dart models have correct part directives."""

    def test_dart_model_has_part_directives(self):
        """Test that part directives for .freezed.dart and .g.dart are present."""
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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Part Directives:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify part directives
        assert "part 'models.freezed.dart';" in code, \
            "Should have part directive for models.freezed.dart"
        assert "part 'models.g.dart';" in code, \
            "Should have part directive for models.g.dart"

    def test_part_directives_appear_once(self):
        """Test that part directives appear only once regardless of model count."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Part Directives Count:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Count occurrences
        freezed_part_count = code.count("part 'models.freezed.dart';")
        g_part_count = code.count("part 'models.g.dart';")

        assert freezed_part_count == 1, \
            f"Should have exactly 1 'models.freezed.dart' directive, found {freezed_part_count}"
        assert g_part_count == 1, \
            f"Should have exactly 1 'models.g.dart' directive, found {g_part_count}"

    def test_required_imports_present(self):
        """Test that required package imports are present."""
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

        print("\n" + "=" * 80)
        print("Generated Dart code - Imports:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify imports - freezed_annotation provides @JsonKey, so json_annotation is not needed
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code, \
            "Should import freezed_annotation"
        # json_annotation is NOT needed when using freezed_annotation
        assert "import 'package:json_annotation/json_annotation.dart';" not in code, \
            "json_annotation is provided by freezed_annotation"


class TestDartModelFieldTypes:
    """Test that fields have correct Dart types mapped from schema types."""

    def test_dart_model_fields_have_correct_types(self):
        """Test that all basic types are correctly mapped to Dart types."""
        schema = SchnitzelSchema(
            models={
                "AllTypes": Model(
                    name="AllTypes",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int"),
                        "score": FieldDefinition(type="float"),
                        "active": FieldDefinition(type="bool"),
                        "created_at": FieldDefinition(type="datetime"),
                        "metadata": FieldDefinition(type="json"),
                        "tags": FieldDefinition(type="list<string>"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Type Mapping:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify type mappings (snake_case fields converted to camelCase with @JsonKey)
        assert "required String id," in code, "uuid should map to String"
        assert "required String name," in code, "string should map to String"
        assert "required int age," in code, "int should map to int"
        assert "required double score," in code, "float should map to double"
        assert "required bool active," in code, "bool should map to bool"
        # created_at becomes createdAt with @JsonKey
        assert "@JsonKey(name: 'created_at') required DateTime createdAt," in code, "datetime should map to DateTime"
        assert "required Map<String, dynamic> metadata," in code, "json should map to Map<String, dynamic>"
        assert "required List<String> tags," in code, "list<string> should map to List<String>"

    def test_complex_list_types(self):
        """Test that complex list types are mapped correctly."""
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

        print("\n" + "=" * 80)
        print("Generated Dart code - Complex List Types:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify complex type mappings
        assert "required List<String> strings," in code
        assert "required List<int> integers," in code
        assert "required List<double> floats," in code
        assert "required List<double> vector," in code, "vector should map to List<double>"
        assert "required List<int> bytes," in code, "bytes should map to List<int>"

    def test_enum_type_mapping(self):
        """Test that enum types map to String."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
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

        print("\n" + "=" * 80)
        print("Generated Dart code - Enum Type:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Enum should map to String
        assert "required String status," in code, "enum should map to String"


class TestDartModelOptionalFields:
    """Test that optional fields are correctly marked as nullable."""

    def test_dart_model_optional_fields_are_nullable(self):
        """Test that optional fields use Type? syntax."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "bio": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "score": FieldDefinition(type="float", optional=True),
                        "verified": FieldDefinition(type="bool", optional=True),
                        "last_login": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Optional Fields:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Required fields should have 'required' keyword
        assert "required String id," in code
        assert "required String name," in code

        # Optional fields should be nullable (Type?)
        # snake_case fields converted to camelCase with @JsonKey
        assert "String? bio," in code
        assert "int? age," in code
        assert "double? score," in code
        assert "bool? verified," in code
        assert "@JsonKey(name: 'last_login') DateTime? lastLogin," in code

        # Optional fields should NOT have 'required' keyword
        assert "required String? bio" not in code
        assert "required int? age" not in code
        assert "required double? score" not in code
        assert "required bool? verified" not in code
        assert "required DateTime? lastLogin" not in code

    def test_optional_complex_types(self):
        """Test that optional complex types are nullable."""
        schema = SchnitzelSchema(
            models={
                "Profile": Model(
                    name="Profile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "metadata": FieldDefinition(type="json", optional=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                        "scores": FieldDefinition(type="list<float>", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Optional Complex Types:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Optional complex types should be nullable
        assert "Map<String, dynamic>? metadata," in code
        assert "List<String>? tags," in code
        assert "List<double>? scores," in code


class TestDartModelRelationships:
    """Test that relationship fields generate correctly."""

    def test_dart_model_with_relationships(self):
        """Test that relationship fields are generated correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                        "profile": Relation(type="hasOne", model="Profile"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User", foreign_key="author_id"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Relationships:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify hasMany relationship
        assert "List<Post>? posts," in code, "hasMany should generate List<Model>? field"

        # Verify hasOne relationship
        assert "Profile? profile," in code, "hasOne should generate Model? field"

        # Verify belongsTo relationship
        assert "User? author," in code, "belongsTo should generate Model? field"

    def test_relationship_fields_with_json_key(self):
        """Test that snake_case relationship fields get @JsonKey annotation when converted to camelCase."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "blog_posts": Relation(type="hasMany", model="Post"),
                        "user_profile": Relation(type="hasOne", model="Profile"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Relationships with @JsonKey:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # snake_case relationship fields converted to camelCase with @JsonKey
        assert "@JsonKey(name: 'blog_posts')" in code, "snake_case should get @JsonKey"
        assert "List<Post>? blogPosts," in code

        assert "@JsonKey(name: 'user_profile')" in code, "snake_case should get @JsonKey"
        assert "Profile? userProfile," in code


class TestDartModelCompleteStructure:
    """Test complete model structure for instantiation and serialization readiness."""

    def test_complete_model_structure(self):
        """Test that a complete model has all necessary elements for instantiation."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="string", optional=True),
                        "price": FieldDefinition(type="float"),
                        "in_stock": FieldDefinition(type="bool", default=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - Complete Structure:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify all essential elements for instantiation
        assert "@freezed" in code, "Needs @freezed for code generation"
        assert "class Product with _$Product {" in code, "Needs class with mixin"
        assert "const factory Product({" in code, "Needs factory constructor"
        assert "}) = _Product;" in code, "Needs factory redirect"
        assert "factory Product.fromJson(Map<String, dynamic> json) => _$ProductFromJson(json);" in code, \
            "Needs fromJson for deserialization"

        # Verify imports - freezed_annotation provides @JsonKey, so json_annotation is not needed
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" not in code

        # Verify part directives
        assert "part 'models.freezed.dart';" in code, "Needs freezed part for code generation"
        assert "part 'models.g.dart';" in code, "Needs g.dart part for JSON serialization"

        # Verify all fields are present with correct types (snake_case converted to camelCase)
        assert "required String id," in code
        assert "required String name," in code
        assert "String? description," in code
        assert "required double price," in code
        assert "@JsonKey(name: 'in_stock') @Default(true) bool inStock," in code
        assert "List<String>? tags," in code

    def test_model_ready_for_freezed_code_generation(self):
        """Test that generated code structure is ready for build_runner."""
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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        print("\n" + "=" * 80)
        print("Generated Dart code - build_runner Ready:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Check structure matches Freezed requirements
        lines = code.split('\n')

        # Find @freezed annotation
        freezed_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "@freezed":
                freezed_idx = i
                break

        assert freezed_idx is not None, "@freezed annotation must be present"

        # Next non-empty line should be class declaration
        class_line = None
        for i in range(freezed_idx + 1, len(lines)):
            if lines[i].strip():
                class_line = lines[i]
                break

        assert class_line is not None, "Class declaration must follow @freezed"
        assert "class User with _$User {" in class_line, "Class must have mixin"

        # Verify no toJson method (Freezed generates it automatically)
        assert "toJson(" not in code, "toJson is auto-generated by Freezed, should not be in code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
