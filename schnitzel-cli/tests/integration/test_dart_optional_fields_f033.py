"""Integration test for F033: Dart Freezed models handle optional/nullable fields correctly.

Test Requirements:
1. test_required_field_has_required_keyword - Required fields should have 'required' keyword
2. test_optional_field_has_nullable_type - Optional fields should have nullable type (Type?)
3. test_mixed_required_and_optional_fields - Model with both required and optional fields
4. test_all_optional_model - Model where all fields are optional

Test Steps:
- Create schema with various field configurations
- Generate Dart code using DartModelGenerator
- Verify correct syntax for required vs optional fields
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


def test_required_field_has_required_keyword():
    """Test that required fields (optional=False) have 'required' keyword."""

    # Create schema with required fields only
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string", optional=False),
                    "name": FieldDefinition(type="string", optional=False),
                    "email": FieldDefinition(type="string", optional=False),
                }
            )
        }
    )

    # Generate Dart code
    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code for required fields:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify all fields have 'required' keyword
    assert "required String id," in generated_code, "id should have 'required' keyword"
    assert "required String name," in generated_code, "name should have 'required' keyword"
    assert "required String email," in generated_code, "email should have 'required' keyword"

    # Verify no nullable types (should not contain '?')
    lines = generated_code.split('\n')
    field_lines = [line for line in lines if 'String id' in line or 'String name' in line or 'String email' in line]
    for line in field_lines:
        assert '?' not in line, f"Required field should not have nullable type: {line}"


def test_optional_field_has_nullable_type():
    """Test that optional fields (optional=True) have nullable type (Type?)."""

    # Create schema with optional fields only
    schema = SchnitzelSchema(
        models={
            "Profile": Model(
                name="Profile",
                fields={
                    "bio": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                    "website": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    # Generate Dart code
    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code for optional fields:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify all fields have nullable type (Type?)
    assert "String? bio," in generated_code, "bio should have nullable type (String?)"
    assert "int? age," in generated_code, "age should have nullable type (int?)"
    assert "String? website," in generated_code, "website should have nullable type (String?)"

    # Verify no 'required' keyword for optional fields
    lines = generated_code.split('\n')
    field_lines = [line for line in lines if 'bio' in line or 'age' in line or 'website' in line]
    for line in field_lines:
        if 'String?' in line or 'int?' in line:
            assert 'required' not in line, f"Optional field should not have 'required' keyword: {line}"


def test_mixed_required_and_optional_fields():
    """Test model with both required and optional fields."""

    # Create schema with mixed required and optional fields
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    # Required fields
                    "id": FieldDefinition(type="string", optional=False),
                    "name": FieldDefinition(type="string", optional=False),
                    "email": FieldDefinition(type="string", optional=False),

                    # Optional fields
                    "bio": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                    "avatar_url": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    # Generate Dart code
    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code for mixed required/optional fields:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify required fields have 'required' keyword
    assert "required String id," in generated_code, "id should have 'required' keyword"
    assert "required String name," in generated_code, "name should have 'required' keyword"
    assert "required String email," in generated_code, "email should have 'required' keyword"

    # Verify optional fields have nullable type
    # snake_case fields are converted to camelCase with @JsonKey
    assert "String? bio," in generated_code, "bio should have nullable type"
    assert "int? age," in generated_code, "age should have nullable type"
    assert "@JsonKey(name: 'avatar_url') String? avatarUrl," in generated_code, "avatar_url becomes avatarUrl with @JsonKey"

    # Verify structure
    assert "@freezed" in generated_code, "Should have @freezed annotation"
    assert "class User with _$User" in generated_code, "Should have proper class declaration"
    assert "const factory User({" in generated_code, "Should have factory constructor"


def test_all_optional_model():
    """Test model where all fields are optional."""

    # Create schema with all optional fields
    schema = SchnitzelSchema(
        models={
            "Settings": Model(
                name="Settings",
                fields={
                    "theme": FieldDefinition(type="string", optional=True),
                    "notifications_enabled": FieldDefinition(type="bool", optional=True),
                    "max_results": FieldDefinition(type="int", optional=True),
                    "language": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    # Generate Dart code
    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code for all optional fields:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify all fields have nullable type
    # snake_case fields are converted to camelCase with @JsonKey
    assert "String? theme," in generated_code, "theme should be nullable"
    assert "@JsonKey(name: 'notifications_enabled') bool? notificationsEnabled," in generated_code, "notifications_enabled becomes notificationsEnabled"
    assert "@JsonKey(name: 'max_results') int? maxResults," in generated_code, "max_results becomes maxResults"
    assert "String? language," in generated_code, "language should be nullable"

    # Verify no 'required' keywords for optional fields
    lines = generated_code.split('\n')
    field_lines = [line for line in lines if any(field in line for field in ['theme', 'notificationsEnabled', 'maxResults', 'language'])]
    for line in field_lines:
        if '?' in line:  # It's a field line
            assert 'required' not in line, f"All-optional model should not have 'required' keyword: {line}"


def test_various_dart_types_with_optional():
    """Test optional flag works with various Dart types."""

    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    # Required fields with various types
                    "id": FieldDefinition(type="uuid", optional=False),
                    "created_at": FieldDefinition(type="datetime", optional=False),
                    "active": FieldDefinition(type="bool", optional=False),

                    # Optional fields with various types
                    "score": FieldDefinition(type="float", optional=True),
                    "metadata": FieldDefinition(type="json", optional=True),
                    "updated_at": FieldDefinition(type="datetime", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code for various types with optional:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify required fields (snake_case converted to camelCase with @JsonKey)
    assert "required String id," in generated_code, "uuid maps to String and should be required"
    assert "@JsonKey(name: 'created_at') required DateTime createdAt," in generated_code, "datetime should be required with camelCase"
    assert "required bool active," in generated_code, "bool should be required"

    # Verify optional fields (snake_case converted to camelCase with @JsonKey)
    assert "double? score," in generated_code, "float should map to double? when optional"
    assert "Map<String, dynamic>? metadata," in generated_code, "json should be nullable when optional"
    assert "@JsonKey(name: 'updated_at') DateTime? updatedAt," in generated_code, "datetime should be nullable with camelCase"


def test_list_types_with_optional():
    """Test optional flag works with list types."""

    schema = SchnitzelSchema(
        models={
            "Article": Model(
                name="Article",
                fields={
                    # Required list field
                    "tags": FieldDefinition(type="list<string>", optional=False),
                    
                    # Optional list field
                    "categories": FieldDefinition(type="list<string>", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code for list types with optional:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify required list
    assert "required List<String> tags," in generated_code, "required list should have 'required' keyword"

    # Verify optional list
    assert "List<String>? categories," in generated_code, "optional list should be nullable"


def test_freezed_structure():
    """Test that generated code has proper Freezed structure."""

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string", optional=False),
                    "name": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code structure:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify essential Freezed structure
    assert "import 'package:freezed_annotation/freezed_annotation.dart';" in generated_code, \
        "Should import freezed_annotation"
    assert "part 'models.freezed.dart';" in generated_code, \
        "Should have freezed part directive"
    assert "part 'models.g.dart';" in generated_code, \
        "Should have json_serializable part directive"
    assert "@freezed" in generated_code, \
        "Should have @freezed annotation"
    assert "class User with _$User" in generated_code, \
        "Should have proper class declaration with mixin"
    assert "const factory User({" in generated_code, \
        "Should have const factory constructor"
    assert "}) = _User;" in generated_code, \
        "Should have proper factory redirect"
    assert "factory User.fromJson(Map<String, dynamic> json) =>" in generated_code, \
        "Should have fromJson factory"
    assert "_$UserFromJson(json);" in generated_code, \
        "Should call generated fromJson method"


def test_default_optional_is_false():
    """Test that when optional is not specified, it defaults to False (required)."""

    # Create schema without specifying optional (should default to False)
    schema = SchnitzelSchema(
        models={
            "Product": Model(
                name="Product",
                fields={
                    # Not specifying optional - should default to False
                    "id": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                }
            )
        }
    )

    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Dart code with default optional behavior:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify fields are required by default
    assert "required String id," in generated_code, "Fields should be required by default"
    assert "required String name," in generated_code, "Fields should be required by default"
    
    # Should not have nullable types
    assert "String? id" not in generated_code, "Default fields should not be nullable"
    assert "String? name" not in generated_code, "Default fields should not be nullable"


if __name__ == "__main__":
    # Run tests manually for development
    print("Running F033 Integration Tests\n")
    
    test_required_field_has_required_keyword()
    print(" test_required_field_has_required_keyword PASSED\n")
    
    test_optional_field_has_nullable_type()
    print(" test_optional_field_has_nullable_type PASSED\n")
    
    test_mixed_required_and_optional_fields()
    print(" test_mixed_required_and_optional_fields PASSED\n")
    
    test_all_optional_model()
    print(" test_all_optional_model PASSED\n")
    
    test_various_dart_types_with_optional()
    print(" test_various_dart_types_with_optional PASSED\n")
    
    test_list_types_with_optional()
    print(" test_list_types_with_optional PASSED\n")
    
    test_freezed_structure()
    print(" test_freezed_structure PASSED\n")
    
    test_default_optional_is_false()
    print(" test_default_optional_is_false PASSED\n")

    print("=" * 80)
    print(" All F033 tests passed!")
    print("=" * 80)
