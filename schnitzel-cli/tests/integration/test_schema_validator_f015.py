"""
Integration test for F015: Schema validator enforces snake_case naming for fields.

Test steps:
1. Create User model with field named 'firstName' (camelCase)
2. Call SchemaValidator.validate(schema)
3. Verify validation fails
4. Verify error indicates field naming violation
5. Verify error suggests correct name 'first_name'
6. Verify error includes model name and field name
"""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema import SchemaValidator, ValidationResult


def test_camel_case_field_name_validation_fails():
    """
    Test F015: Schema validator rejects camelCase field names.

    This test verifies that the SchemaValidator correctly rejects field names
    that don't follow snake_case convention and provides helpful error messages.
    """
    # Step 1: Create User model with field named 'firstName' (camelCase)
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "firstName": FieldDefinition(type="string"),  # camelCase - should fail
                    "email": FieldDefinition(type="string")  # snake_case - should pass
                }
            )
        }
    )

    # Step 2: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 3: Verify validation fails
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is False, "Validation should fail for camelCase field name"
    assert len(result.errors) > 0, "Should have at least one error"

    # Step 4: Verify error indicates field naming violation
    error_text = "\n".join(result.errors)
    assert "firstName" in error_text, "Error should mention the violating field name 'firstName'"
    assert "naming convention" in error_text.lower(), "Error should mention naming convention"

    # Step 5: Verify error suggests correct name 'first_name'
    assert "first_name" in error_text.lower(), "Error should suggest correct name 'first_name'"
    assert "suggested" in error_text.lower(), "Error should include suggestion"

    # Step 6: Verify error includes model name and field name
    assert "User" in error_text, "Error should include model name 'User'"
    assert "snake_case" in error_text, "Error should specify snake_case convention"

    print("\n✓ Test F015 passed: Schema validator rejects camelCase field names")


def test_valid_snake_case_field_names_pass():
    """
    Test that valid snake_case field names pass validation.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "first_name": FieldDefinition(type="string"),
                    "last_name": FieldDefinition(type="string"),
                    "email_address": FieldDefinition(type="string"),
                    "created_at": FieldDefinition(type="datetime"),
                    "is_active": FieldDefinition(type="bool"),
                    "age": FieldDefinition(type="int"),
                    "score2": FieldDefinition(type="float"),  # with digit
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Valid snake_case names should pass. Errors: {result.errors}"
    assert result.errors == [], "Should have no errors for valid snake_case names"

    print("✓ Valid snake_case field names pass validation")


def test_multiple_camel_case_violations():
    """
    Test that multiple camelCase violations are all reported.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "firstName": FieldDefinition(type="string"),
                    "lastName": FieldDefinition(type="string"),
                    "emailAddress": FieldDefinition(type="string"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Validation should fail"
    assert len(result.errors) == 3, f"Should have 3 errors (one for each camelCase field). Got {len(result.errors)}"

    error_text = "\n".join(result.errors)
    assert "firstName" in error_text, "Should report firstName violation"
    assert "lastName" in error_text, "Should report lastName violation"
    assert "emailAddress" in error_text, "Should report emailAddress violation"

    print("✓ Multiple camelCase violations are all reported")


def test_pascal_case_field_name_validation_fails():
    """
    Test that PascalCase field names are also rejected.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "FirstName": FieldDefinition(type="string"),  # PascalCase - should fail
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Validation should fail for PascalCase field name"
    error_text = "\n".join(result.errors)
    assert "FirstName" in error_text, "Error should mention the violating field name"
    assert "first_name" in error_text.lower(), "Error should suggest 'first_name'"

    print("✓ PascalCase field names are rejected")


def test_invalid_snake_case_patterns():
    """
    Test that invalid snake_case patterns are rejected.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "_private": FieldDefinition(type="string"),  # starts with underscore
                    "trailing_": FieldDefinition(type="string"),  # ends with underscore
                    "double__underscore": FieldDefinition(type="string"),  # double underscore
                    "UPPERCASE": FieldDefinition(type="string"),  # all uppercase
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Validation should fail for invalid snake_case patterns"
    # Should have 4 errors (all invalid patterns except 'id')
    assert len(result.errors) >= 4, f"Should have at least 4 errors. Got {len(result.errors)}"

    print("✓ Invalid snake_case patterns are rejected")


def test_error_message_format():
    """
    Test that error messages follow the specified format.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "firstName": FieldDefinition(type="string"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert len(result.errors) > 0, "Should have errors"
    error = result.errors[0]

    # Verify error format matches requirements:
    # Field name 'firstName' in model 'User' violates naming convention
    # Field names must be snake_case
    # Suggested name: 'first_name'
    assert "Field name 'firstName' in model 'User' violates naming convention" in error
    assert "Field names must be snake_case" in error
    assert "Suggested name: 'first_name'" in error

    print("✓ Error message format is correct")


def test_multiple_models_validation():
    """
    Test validation across multiple models.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "userName": FieldDefinition(type="string"),  # camelCase in User
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "postTitle": FieldDefinition(type="string"),  # camelCase in Post
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Validation should fail"
    assert len(result.errors) == 2, "Should have 2 errors (one per model)"

    error_text = "\n".join(result.errors)
    assert "userName" in error_text and "User" in error_text, "Should report error in User model"
    assert "postTitle" in error_text and "Post" in error_text, "Should report error in Post model"

    print("✓ Validation works across multiple models")


if __name__ == "__main__":
    # Run all tests
    test_camel_case_field_name_validation_fails()
    test_valid_snake_case_field_names_pass()
    test_multiple_camel_case_violations()
    test_pascal_case_field_name_validation_fails()
    test_invalid_snake_case_patterns()
    test_error_message_format()
    test_multiple_models_validation()
    print("\n" + "="*60)
    print("✓ All F015 tests passed!")
    print("="*60)
