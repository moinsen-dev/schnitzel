"""Integration tests for F037: Dart model generator handles snake_case to camelCase conversion.

This feature ensures that:
1. Field names in schema (typically snake_case) are converted to Dart camelCase
2. @JsonKey(name: 'snake_case') is added to map JSON snake_case to Dart camelCase
3. Fields already in camelCase don't need @JsonKey
4. Single-word fields don't need @JsonKey since they're the same
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartSnakeCaseConversion:
    """Test Dart model generator snake_case to camelCase conversion feature (F037)."""

    def test_camel_case_field_no_json_key_needed(self):
        """Test that camelCase fields don't need @JsonKey when JSON key matches.

        When a field is defined in camelCase (e.g., userId, createdAt), and the JSON
        also uses camelCase, no @JsonKey annotation is needed.
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

        # When fields are already camelCase (matching Dart convention),
        # no @JsonKey is needed since JSON key = Dart field name
        assert "required String userId," in code
        assert "DateTime? createdAt," in code
        assert "required String firstName," in code

        # No @JsonKey needed when field names already match
        assert "@JsonKey(name: 'userId')" not in code
        assert "@JsonKey(name: 'createdAt')" not in code
        assert "@JsonKey(name: 'firstName')" not in code

    def test_snake_case_field_converted_to_camel_case_with_json_key(self):
        """Test that snake_case fields are converted to camelCase with @JsonKey.

        When a field is in snake_case (e.g., user_id, created_at), the generator
        should convert it to camelCase and add @JsonKey(name: 'snake_case') to
        maintain JSON compatibility.
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

        # snake_case fields should be converted to camelCase with @JsonKey
        assert "@JsonKey(name: 'user_id') required String userId," in code
        assert "@JsonKey(name: 'created_at') DateTime? createdAt," in code
        assert "@JsonKey(name: 'first_name') required String firstName," in code

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

    def test_to_camel_case_conversion(self):
        """Test the _to_camel_case() helper method for various inputs.

        The helper should correctly convert:
        - snake_case to lowerCamelCase (user_id -> userId)
        - Leave camelCase unchanged (userId -> userId)
        - Leave single words unchanged (name -> name)
        """
        generator = DartModelGenerator()

        # Test snake_case conversion
        assert generator._to_camel_case("user_id") == "userId"
        assert generator._to_camel_case("created_at") == "createdAt"
        assert generator._to_camel_case("first_name") == "firstName"
        assert generator._to_camel_case("is_active") == "isActive"

        # Test camelCase remains unchanged
        assert generator._to_camel_case("userId") == "userId"
        assert generator._to_camel_case("createdAt") == "createdAt"

        # Test single words remain unchanged
        assert generator._to_camel_case("id") == "id"
        assert generator._to_camel_case("name") == "name"
        assert generator._to_camel_case("email") == "email"

    def test_complete_model_with_mixed_field_names(self):
        """Test a complete model with a mix of snake_case and camelCase fields.

        This integration test verifies that the generator correctly handles a realistic
        model with various field naming patterns, applying @JsonKey only where needed.
        """
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        # snake_case - needs @JsonKey and camelCase conversion
                        "user_id": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", optional=True),
                        # single word - no @JsonKey needed
                        "name": FieldDefinition(type="string"),
                        # snake_case - needs @JsonKey and camelCase conversion
                        "user_role": FieldDefinition(type="string"),
                        # snake_case - needs @JsonKey and camelCase conversion
                        "is_active": FieldDefinition(type="boolean", default=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @JsonKey is present for snake_case fields (converted to camelCase)
        assert "@JsonKey(name: 'user_id')" in code
        assert "@JsonKey(name: 'created_at')" in code
        assert "@JsonKey(name: 'user_role')" in code
        assert "@JsonKey(name: 'is_active')" in code

        # Count total @JsonKey occurrences - should be exactly 4
        json_key_count = code.count("@JsonKey")
        assert json_key_count == 4, f"Expected 4 @JsonKey annotations, found {json_key_count}"

        # Verify field declarations use camelCase
        assert "required String userId," in code
        assert "DateTime? createdAt," in code
        assert "required String name," in code
        assert "required String userRole," in code
        assert "@Default(true) bool isActive," in code

    def test_needs_json_key_method(self):
        """Test the _needs_json_key() helper method.

        This method should return True when the JSON field name differs from
        the Dart field name (after camelCase conversion).
        """
        generator = DartModelGenerator()

        # snake_case fields need @JsonKey (JSON name != Dart camelCase name)
        # _needs_json_key takes (field_name, dart_field_name) - we need to provide both
        assert generator._needs_json_key("user_id", "userId") is True
        assert generator._needs_json_key("created_at", "createdAt") is True
        assert generator._needs_json_key("first_name", "firstName") is True
        assert generator._needs_json_key("is_active", "isActive") is True

        # Fields where JSON key = Dart field name don't need @JsonKey
        assert generator._needs_json_key("userId", "userId") is False
        assert generator._needs_json_key("createdAt", "createdAt") is False
        assert generator._needs_json_key("id", "id") is False
        assert generator._needs_json_key("name", "name") is False
        assert generator._needs_json_key("email", "email") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
