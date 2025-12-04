"""Integration tests for F039: Dart model generator produces code that passes dart analyze.

Tests verify that generated Dart code follows Dart best practices and has valid syntax
that would pass 'dart analyze' without errors.

Since we can't run 'dart analyze' in tests (no Dart SDK), we verify:
- Proper import statements
- Valid class syntax
- Correct annotation usage
- No syntax errors in generated output
- Valid factory constructors
- Proper part directives
"""

import pytest
import re
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.models import DartModelGenerator


class TestValidImportStatements:
    """Test that import statements follow Dart conventions."""

    def test_import_statements_properly_formatted(self):
        """Test that import statements use correct Dart syntax."""
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

        # Check import format: import 'package:...';
        # All imports must end with semicolon
        imports = [line for line in code.split('\n') if line.startswith('import')]

        for import_line in imports:
            # Must start with 'import'
            assert import_line.startswith('import ')
            # Must have single quotes
            assert "'" in import_line
            # Must end with semicolon
            assert import_line.endswith(';')
            # Must contain 'package:' for package imports
            assert 'package:' in import_line

    def test_imports_use_single_quotes(self):
        """Test that imports use Dart-style single quotes, not double quotes."""
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

        # Imports should use single quotes
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code

        # Should NOT have double quotes in imports
        imports = [line for line in code.split('\n') if line.startswith('import')]
        for import_line in imports:
            assert '"' not in import_line

    def test_required_imports_present(self):
        """Test that all required imports are present for Freezed models."""
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

        # Must have freezed_annotation import
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        # Must have json_annotation import
        assert "import 'package:json_annotation/json_annotation.dart';" in code

    def test_imports_come_before_parts(self):
        """Test that import statements come before part directives."""
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

        # Find positions
        import_pos = code.find("import 'package:")
        part_pos = code.find("part '")

        # Imports must come before parts
        assert import_pos < part_pos

    def test_no_duplicate_imports(self):
        """Test that there are no duplicate import statements."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        imports = [line for line in code.split('\n') if line.startswith('import')]

        # Check no duplicates
        assert len(imports) == len(set(imports))


class TestValidClassDeclaration:
    """Test that class declarations use correct Dart syntax."""

    def test_class_declaration_with_mixin(self):
        """Test that classes use 'with _$ClassName' mixin syntax."""
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

        # Correct mixin syntax
        assert "class User with _$User {" in code
        # Should NOT use extends
        assert "class User extends" not in code

    def test_class_has_freezed_annotation(self):
        """Test that all model classes have @freezed annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Count @freezed annotations (should match number of models)
        freezed_count = code.count('@freezed')
        assert freezed_count == 2

    def test_class_name_follows_dart_conventions(self):
        """Test that class names use PascalCase."""
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check PascalCase is preserved
        assert "class UserProfile with _$UserProfile {" in code

    def test_class_ends_with_closing_brace(self):
        """Test that class declarations are properly closed."""
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

        # Find class start
        class_start = code.find("class User")
        assert class_start != -1

        # Find corresponding closing brace after fromJson
        fromjson_pos = code.find("UserFromJson", class_start)
        closing_brace = code.find("}", fromjson_pos)
        assert closing_brace != -1

    def test_multiple_classes_properly_separated(self):
        """Test that multiple classes are properly separated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Both classes should exist
        assert "class User with _$User {" in code
        assert "class Post with _$Post {" in code


class TestValidFactoryConstructor:
    """Test that factory constructors follow Dart conventions."""

    def test_factory_constructor_syntax(self):
        """Test that factory constructor uses correct Dart syntax."""
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

        # Check factory constructor format
        assert "const factory User({" in code
        assert "}) = _User;" in code

    def test_factory_uses_const_keyword(self):
        """Test that factory constructor uses 'const' keyword."""
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

        # Must use const factory
        assert "const factory User" in code

    def test_factory_parameters_have_trailing_commas(self):
        """Test that factory parameters have trailing commas (Dart best practice)."""
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

        # Each field should end with comma
        assert "required String id," in code
        assert "required String name," in code

    def test_empty_factory_for_no_fields(self):
        """Test that models with no fields have empty factory constructor."""
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

        # Empty factory should not have curly braces
        assert "const factory EmptyModel() = _EmptyModel;" in code

    def test_fromjson_factory_syntax(self):
        """Test that fromJson factory follows correct syntax."""
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

        # Check fromJson format
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code

    def test_fromjson_uses_correct_return_type(self):
        """Test that fromJson factory uses fat arrow syntax correctly."""
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

        # Should use => not { return ... }
        assert "=> _$UserFromJson(json);" in code
        # Should NOT have block body
        assert "{ return" not in code


class TestValidAnnotations:
    """Test that annotations follow Dart syntax rules."""

    def test_freezed_annotation_format(self):
        """Test that @freezed annotation is properly formatted."""
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

        # @freezed should be on its own line before class
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if '@freezed' in line:
                # Next non-empty line should be class declaration
                next_line = lines[i + 1].strip()
                assert next_line.startswith('class ')

    def test_jsonkey_annotation_format(self):
        """Test that @JsonKey annotation has correct syntax."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "userId": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # @JsonKey should use single quotes and have name parameter
        assert "@JsonKey(name: 'user_id')" in code
        # Should NOT use double quotes
        assert '@JsonKey(name: "user_id")' not in code

    def test_default_annotation_format(self):
        """Test that @Default annotation has correct syntax."""
        schema = SchnitzelSchema(
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

        # @Default should use single quotes for strings
        assert "@Default('active')" in code

    def test_multiple_annotations_on_same_field(self):
        """Test that multiple annotations are properly separated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "userName": FieldDefinition(type="string", default="guest"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have both @JsonKey and @Default
        assert "@JsonKey(name: 'user_name') @Default('guest')" in code

    def test_annotations_use_parentheses(self):
        """Test that all annotations use parentheses correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "userId": FieldDefinition(type="string"),
                        "count": FieldDefinition(type="int", default=0),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All annotations should have balanced parentheses
        annotations = re.findall(r'@\w+\([^)]+\)', code)
        for annotation in annotations:
            # Count opening and closing parentheses
            assert annotation.count('(') == annotation.count(')')


class TestNoSyntaxErrors:
    """Test that generated code has no syntax errors."""

    def test_all_braces_balanced(self):
        """Test that all opening braces have matching closing braces."""
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

        # Count braces
        opening = code.count('{')
        closing = code.count('}')
        assert opening == closing

    def test_all_parentheses_balanced(self):
        """Test that all opening parentheses have matching closing parentheses."""
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

        # Count parentheses
        opening = code.count('(')
        closing = code.count(')')
        assert opening == closing

    def test_semicolons_properly_placed(self):
        """Test that statements end with semicolons."""
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

        # Import statements should end with semicolon
        imports = [line for line in code.split('\n') if line.startswith('import')]
        for import_line in imports:
            assert import_line.endswith(';')

        # Part directives should end with semicolon
        parts = [line for line in code.split('\n') if line.strip().startswith('part ')]
        for part_line in parts:
            assert part_line.strip().endswith(';')

    def test_no_missing_commas_in_parameters(self):
        """Test that factory parameters have proper comma separation."""
        schema = SchnitzelSchema(
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

        # Each parameter should end with comma
        assert "required String id," in code
        assert "required String name," in code
        assert "required int age," in code

    def test_part_directives_properly_formatted(self):
        """Test that part directives use correct syntax."""
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

        # Part directives should use single quotes
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code

        # Should NOT use double quotes
        parts = [line for line in code.split('\n') if line.strip().startswith('part ')]
        for part_line in parts:
            assert '"' not in part_line

    def test_no_invalid_characters(self):
        """Test that generated code has no invalid characters."""
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

        # Code should be valid ASCII/UTF-8
        try:
            code.encode('utf-8')
        except UnicodeEncodeError:
            pytest.fail("Generated code contains invalid characters")

    def test_required_keyword_placement(self):
        """Test that 'required' keyword is properly placed."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required fields should have 'required' before type
        assert "required String id" in code
        # Optional fields should NOT have 'required'
        assert "String? name" in code
        assert "required String? name" not in code


class TestComplexScenarios:
    """Test complex scenarios that combine multiple validation aspects."""

    def test_complete_model_with_all_features(self):
        """Test a complex model with all features combined."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "userName": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "status": FieldDefinition(type="string", default="active"),
                        "loginCount": FieldDefinition(type="int", default=0),
                        "isActive": FieldDefinition(type="bool", default=True),
                    },
                    relations={
                        "createdPosts": Relation(type="hasMany", model="Post"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify structure is valid
        assert code.count('{') == code.count('}')
        assert code.count('(') == code.count(')')

        # Verify all imports present
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code

        # Verify class structure
        assert "@freezed" in code
        assert "class User with _$User {" in code
        assert "const factory User({" in code
        assert "}) = _User;" in code
        assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in code

        # Verify @JsonKey annotations
        assert "@JsonKey(name: 'user_name')" in code
        assert "@JsonKey(name: 'login_count')" in code
        assert "@JsonKey(name: 'is_active')" in code
        assert "@JsonKey(name: 'created_posts')" in code

        # Verify @Default annotations
        assert "@Default('active')" in code
        assert "@Default(0)" in code
        assert "@Default(true)" in code

    def test_model_with_relationships_is_valid(self):
        """Test that models with relationships have valid syntax."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                        "profile": Relation(type="hasOne", model="Profile"),
                        "createdBy": Relation(type="belongsTo", model="User"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify relationships have correct types
        assert "List<Post>? posts," in code
        assert "Profile? profile," in code
        assert "User? createdBy," in code

        # Verify all commas present
        assert code.count('posts,') >= 1
        assert code.count('profile,') >= 1
        assert code.count('createdBy,') >= 1

    def test_multiple_models_all_valid(self):
        """Test that multiple models all have valid syntax."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "userId": FieldDefinition(type="string"),
                        "userName": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "postId": FieldDefinition(type="string"),
                        "postTitle": FieldDefinition(type="string"),
                    }
                ),
                "Comment": Model(
                    name="Comment",
                    fields={
                        "commentId": FieldDefinition(type="string"),
                        "commentText": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All models should have valid structure
        for model_name in ["User", "Post", "Comment"]:
            assert f"@freezed" in code
            assert f"class {model_name} with _${model_name} {{" in code
            assert f"const factory {model_name}({{" in code
            assert f"}}) = _{model_name};" in code
            assert f"factory {model_name}.fromJson(Map<String, dynamic> json) => _${model_name}FromJson(json);" in code

    def test_special_characters_in_defaults_escaped(self):
        """Test that special characters in default values are properly escaped."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "path": FieldDefinition(type="string", default="C:\\Users\\default"),
                        "quote": FieldDefinition(type="string", default="He said 'hello'"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify escaping
        assert "@Default('C:\\\\Users\\\\default')" in code
        assert "@Default('He said \\'hello\\'')" in code


class TestEdgeCases:
    """Test edge cases that might cause dart analyze issues."""

    def test_single_character_field_names(self):
        """Test that single character field names work correctly."""
        schema = SchnitzelSchema(
            models={
                "Point": Model(
                    name="Point",
                    fields={
                        "x": FieldDefinition(type="int"),
                        "y": FieldDefinition(type="int"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Single char fields should work
        assert "required int x," in code
        assert "required int y," in code

    def test_numbers_in_field_names(self):
        """Test that field names with numbers are valid."""
        schema = SchnitzelSchema(
            models={
                "Model": Model(
                    name="Model",
                    fields={
                        "field1": FieldDefinition(type="string"),
                        "field2": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "required String field1," in code
        assert "required String field2," in code

    def test_long_field_names(self):
        """Test that long field names don't cause issues."""
        schema = SchnitzelSchema(
            models={
                "Model": Model(
                    name="Model",
                    fields={
                        "thisIsAVeryLongFieldNameThatShouldStillWork": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        assert "thisIsAVeryLongFieldNameThatShouldStillWork" in code

    def test_all_dart_primitive_types(self):
        """Test that all supported Dart types are valid."""
        schema = SchnitzelSchema(
            models={
                "TypeTest": Model(
                    name="TypeTest",
                    fields={
                        "stringField": FieldDefinition(type="string"),
                        "intField": FieldDefinition(type="int"),
                        "doubleField": FieldDefinition(type="float"),
                        "boolField": FieldDefinition(type="bool"),
                        "dateTimeField": FieldDefinition(type="datetime"),
                        "jsonField": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All types should be valid Dart types
        assert "String stringField," in code
        assert "int intField," in code
        assert "double doubleField," in code
        assert "bool boolField," in code
        assert "DateTime dateTimeField," in code
        assert "Map<String, dynamic> jsonField," in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
