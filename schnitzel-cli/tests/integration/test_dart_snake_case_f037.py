"""Integration tests for F037: Dart model generator handles snake_case to camelCase conversion.

This feature ensures that:
1. Field names keep their original format from schema (usually camelCase for Dart)
2. @JsonKey(name: 'snake_case') is added when the JSON key differs from field name
3. A helper converts camelCase to snake_case for JSON key generation
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartSnakeCaseConversion:
    """Test Dart model generator snake_case to camelCase conversion feature (F037)."""

    def test_camel_case_field_gets_json_key(self):
        """Test that camelCase fields get @JsonKey annotation with snake_case name.

        When a field is defined in camelCase (e.g., userId, createdAt), the generator
        should add @JsonKey(name: 'snake_case_version') to map JSON snake_case to Dart camelCase.
        """
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "userId": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime", optional=True),
                        "firstName": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @JsonKey is added with correct snake_case names
        assert "@JsonKey(name: 'user_id') required String userId," in code
        assert "@JsonKey(name: 'created_at') DateTime? createdAt," in code
        assert "@JsonKey(name: 'first_name') required String firstName," in code

    def test_snake_case_field_no_json_key_needed(self):
        """Test that snake_case fields do NOT get @JsonKey annotation.

        When a field is already in snake_case (e.g., user_id, created_at), no @JsonKey
        annotation should be added since the Dart field name matches the JSON key.
        """
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "user_id": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", optional=True),
                        "first_name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify NO @JsonKey annotations are added
        assert "@JsonKey" not in code

        # Verify fields are present in the generated code
        assert "required String user_id," in code
        assert "DateTime? created_at," in code
        assert "required String first_name," in code

    def test_single_word_field_no_json_key(self):
        """Test that single-word fields do NOT get @JsonKey annotation.

        Single-word fields like 'name', 'id', 'email' are the same in both camelCase
        and snake_case, so they don't need @JsonKey annotation.
        """
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify NO @JsonKey annotations for single-word fields
        assert "@JsonKey" not in code

        # Verify fields are present without @JsonKey
        assert "required String id," in code
        assert "required String name," in code
        assert "required String email," in code
        assert "int? age," in code

    def test_to_snake_case_conversion(self):
        """Test the _to_snake_case() helper method for various inputs.

        The helper should correctly convert:
        - camelCase to snake_case (userId -> user_id)
        - PascalCase to snake_case (UserName -> user_name)
        - Handle consecutive capitals (HTTPResponse -> h_t_t_p_response)
        - Leave snake_case unchanged (user_id -> user_id)
        - Leave single words unchanged (name -> name)
        """
        generator = DartModelGenerator()

        # Test camelCase conversion
        assert generator._to_snake_case("userId") == "user_id"
        assert generator._to_snake_case("createdAt") == "created_at"
        assert generator._to_snake_case("firstName") == "first_name"
        assert generator._to_snake_case("isActive") == "is_active"

        # Test PascalCase conversion
        assert generator._to_snake_case("UserName") == "user_name"
        assert generator._to_snake_case("FirstName") == "first_name"

        # Test snake_case remains unchanged
        assert generator._to_snake_case("user_id") == "user_id"
        assert generator._to_snake_case("created_at") == "created_at"
        assert generator._to_snake_case("first_name") == "first_name"

        # Test single words remain unchanged
        assert generator._to_snake_case("id") == "id"
        assert generator._to_snake_case("name") == "name"
        assert generator._to_snake_case("email") == "email"

        # Test consecutive capitals
        assert generator._to_snake_case("HTTPResponse") == "h_t_t_p_response"
        assert generator._to_snake_case("URLPath") == "u_r_l_path"

        # Test edge cases
        assert generator._to_snake_case("a") == "a"
        assert generator._to_snake_case("A") == "a"
        assert generator._to_snake_case("aB") == "a_b"

    def test_complete_model_with_mixed_field_names(self):
        """Test a complete model with a mix of camelCase, snake_case, and single-word fields.

        This integration test verifies that the generator correctly handles a realistic
        model with various field naming patterns, applying @JsonKey only where needed.
        """
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        # camelCase - needs @JsonKey
                        "userId": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime", optional=True),
                        # single word - no @JsonKey needed
                        "name": FieldDefinition(type="string"),
                        # snake_case - no @JsonKey needed
                        "user_role": FieldDefinition(type="string"),
                        # camelCase - needs @JsonKey
                        "isActive": FieldDefinition(type="boolean", default=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @JsonKey is present for camelCase fields
        assert "@JsonKey(name: 'user_id')" in code
        assert "@JsonKey(name: 'created_at')" in code
        assert "@JsonKey(name: 'is_active')" in code

        # Verify NO @JsonKey for single-word and snake_case fields
        # Count total @JsonKey occurrences - should be exactly 3
        json_key_count = code.count("@JsonKey")
        assert json_key_count == 3, f"Expected 3 @JsonKey annotations, found {json_key_count}"

        # Verify field declarations
        assert "required String userId," in code
        assert "DateTime? createdAt," in code
        assert "required String name," in code
        assert "required String user_role," in code
        assert "@Default(true) bool isActive," in code

    def test_needs_json_key_method(self):
        """Test the _needs_json_key() helper method.

        This method should return True when a field name would convert to a different
        snake_case version, and False when the field is already in snake_case or is
        a single word.
        """
        generator = DartModelGenerator()

        # Fields that NEED @JsonKey (camelCase)
        assert generator._needs_json_key("userId") is True
        assert generator._needs_json_key("createdAt") is True
        assert generator._needs_json_key("firstName") is True
        assert generator._needs_json_key("isActive") is True

        # Fields that DO NOT need @JsonKey (already snake_case or single word)
        assert generator._needs_json_key("user_id") is False
        assert generator._needs_json_key("created_at") is False
        assert generator._needs_json_key("id") is False
        assert generator._needs_json_key("name") is False
        assert generator._needs_json_key("email") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
