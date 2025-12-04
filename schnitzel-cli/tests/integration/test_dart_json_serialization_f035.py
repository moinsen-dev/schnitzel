"""Integration tests for F035: Dart Freezed model generator with JSON serialization annotations."""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartJsonSerialization:
    """Test Dart model generator JSON serialization features."""

    def test_fromjson_factory_generated(self):
        """Test that fromJson factory method is generated for each model."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check that fromJson factory is generated
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code

    def test_json_key_annotation_for_snake_case_fields(self):
        """Test that @JsonKey annotation is added for snake_case fields (converted to camelCase)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "user_id": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # snake_case fields are converted to camelCase with @JsonKey
        assert "@JsonKey(name: 'user_id')" in code
        assert "@JsonKey(name: 'created_at')" in code
        assert "String userId," in code
        assert "DateTime? createdAt," in code

    def test_imports_include_freezed_annotation(self):
        """Test that freezed_annotation import is included (provides @JsonKey)."""
        schema = SchnitzelSchema(
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

        # Check that freezed_annotation is imported (it provides @JsonKey, so json_annotation is not needed)
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        # json_annotation is NOT needed when using freezed_annotation
        assert "import 'package:json_annotation/json_annotation.dart';" not in code

    def test_part_directive_for_generated_file(self):
        """Test that part directives for .g.dart files are generated."""
        schema = SchnitzelSchema(
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

        # Check that part directive for generated file is included
        # Using single-file approach: models.dart -> models.g.dart + models.freezed.dart
        assert "part 'models.g.dart';" in code
        assert "part 'models.freezed.dart';" in code

    def test_no_json_key_for_camel_case_fields(self):
        """Test that @JsonKey is NOT added for fields already in camelCase (JSON key matches Dart name)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "userId": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Fields already in camelCase should NOT have @JsonKey since JSON key = Dart field name
        assert code.count("@JsonKey") == 0
        assert "required String userId," in code
        assert "DateTime? createdAt," in code

    def test_complete_model_structure(self):
        """Test complete model structure with all JSON serialization features."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "user_id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check overall structure
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code
        assert "@freezed" in code
        assert "class User with _$User {" in code
        assert "@JsonKey(name: 'user_id')" in code
        assert "@JsonKey(name: 'created_at')" in code
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code

    def test_multiple_models_with_json_serialization(self):
        """Test multiple models each with JSON serialization."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "userId": FieldDefinition(type="string"),
                    }
                ),
                "Product": Model(
                    name="Product",
                    fields={
                        "productId": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check both models have fromJson
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code
        assert "factory Product.fromJson(Map<String, dynamic> json) => _$ProductFromJson(json);" in code

        # Check part directives (single-file approach, both models in models.dart)
        assert "part 'models.g.dart';" in code
        assert "part 'models.freezed.dart';" in code

    def test_relationship_fields_with_json_key(self):
        """Test that relationship fields also get @JsonKey when needed."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    },
                    relations={
                        "created_by": Relation(type="belongsTo", model="User"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check that relationship field gets @JsonKey (snake_case converted to camelCase)
        assert "@JsonKey(name: 'created_by')" in code
        assert "User? createdBy," in code

    def test_freezed_annotation_present(self):
        """Test that @freezed annotation is present on models."""
        schema = SchnitzelSchema(
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

        # Check that @freezed annotation is present
        assert "@freezed" in code

    def test_required_fields_with_json_key(self):
        """Test that required fields work correctly with @JsonKey."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "user_id": FieldDefinition(type="string"),  # required by default
                        "user_name": FieldDefinition(type="string"),  # required by default
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check that required keyword is present with @JsonKey
        assert "@JsonKey(name: 'user_id') required String userId," in code
        assert "@JsonKey(name: 'user_name') required String userName," in code

    def test_optional_fields_with_json_key(self):
        """Test that optional fields work correctly with @JsonKey."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "user_id": FieldDefinition(type="string"),
                        "middle_name": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check that optional fields don't have required keyword
        assert "@JsonKey(name: 'middle_name') String? middleName," in code
        # Should NOT have "required" before the type for optional fields
        assert "required String? middleName" not in code

    def test_snake_case_conversion(self):
        """Test snake_case conversion logic."""
        generator = DartModelGenerator()

        # Test various conversions
        assert generator._to_snake_case("userId") == "user_id"
        assert generator._to_snake_case("createdAt") == "created_at"
        assert generator._to_snake_case("userName") == "user_name"
        assert generator._to_snake_case("id") == "id"
        assert generator._to_snake_case("user_id") == "user_id"
        assert generator._to_snake_case("HTTPResponse") == "h_t_t_p_response"

    def test_needs_json_key_logic(self):
        """Test the logic that determines if @JsonKey is needed."""
        generator = DartModelGenerator()

        # _needs_json_key takes (field_name, dart_field_name) and returns True if they differ
        # snake_case fields converted to camelCase need @JsonKey
        assert generator._needs_json_key("user_id", "userId") is True
        assert generator._needs_json_key("created_at", "createdAt") is True

        # Fields where JSON key = Dart field name don't need @JsonKey
        assert generator._needs_json_key("id", "id") is False
        assert generator._needs_json_key("name", "name") is False
        assert generator._needs_json_key("userId", "userId") is False

    def test_freezed_import_present(self):
        """Test that freezed_annotation import is present."""
        schema = SchnitzelSchema(
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

        # Check that freezed_annotation is imported
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code

    def test_has_many_relationship_with_json_key(self):
        """Test hasMany relationships with @JsonKey annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    },
                    relations={
                        "created_posts": Relation(type="hasMany", model="Post"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check that hasMany relationship gets @JsonKey (snake_case converted to camelCase)
        assert "@JsonKey(name: 'created_posts') List<Post>? createdPosts," in code

    def test_model_with_no_fields_still_has_fromjson(self):
        """Test that models with no fields still get fromJson factory."""
        schema = SchnitzelSchema(
            models={
                "EmptyModel": Model(
                    name="EmptyModel",
                    fields={}
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Even empty models should have fromJson
        assert "factory EmptyModel.fromJson(Map<String, dynamic> json) => _$EmptyModelFromJson(json);" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
