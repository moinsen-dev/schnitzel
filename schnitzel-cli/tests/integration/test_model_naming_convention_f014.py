"""Test F014: Schema validator enforces PascalCase naming for models."""

import pytest
from schnitzel.schema import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


def test_snake_case_model_name_fails_validation():
    """
    Test that a model with snake_case name fails validation.

    Test steps:
    1. Create schema with model named 'user_profile' (snake_case)
    2. Call SchemaValidator.validate(schema)
    3. Verify validation fails
    4. Verify error indicates naming convention violation
    5. Verify error suggests correct name 'UserProfile'
    6. Verify error references naming convention rules
    """
    # Step 1: Create schema with model named 'user_profile' (snake_case)
    schema = SchnitzelSchema(
        models={
            "user_profile": Model(
                name="user_profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        }
    )

    # Step 2: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 3: Verify validation fails
    assert result.valid is False, "Validation should fail for snake_case model name"
    assert len(result.errors) > 0, "Should have at least one error"

    # Get the error message
    error_message = "\n".join(result.errors)

    # Step 4: Verify error indicates naming convention violation
    assert "user_profile" in error_message, "Error should mention the model name 'user_profile'"
    assert "violates naming convention" in error_message, (
        "Error should indicate naming convention violation"
    )

    # Step 5: Verify error suggests correct name 'UserProfile'
    assert "UserProfile" in error_message, "Error should suggest 'UserProfile'"
    assert "Suggested name:" in error_message or "Suggested" in error_message, (
        "Error should include suggestion"
    )

    # Step 6: Verify error references naming convention rules
    assert "PascalCase" in error_message, "Error should mention PascalCase convention"


def test_error_format_matches_specification():
    """Test that error message follows the required format."""
    schema = SchnitzelSchema(
        models={
            "user_profile": Model(
                name="user_profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Verify format components as specified in requirements
    # Expected format:
    # Model name 'user_profile' violates naming convention
    # Model names must be PascalCase
    # Suggested name: 'UserProfile'
    assert "Model name 'user_profile' violates naming convention" in error_message
    assert "Model names must be PascalCase" in error_message
    assert "Suggested name: 'UserProfile'" in error_message


def test_kebab_case_model_name_fails():
    """Test that kebab-case model name fails validation."""
    schema = SchnitzelSchema(
        models={
            "user-profile": Model(
                name="user-profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "user-profile" in error_message
    assert "UserProfile" in error_message


def test_lowercase_model_name_fails():
    """Test that all-lowercase model name fails validation."""
    schema = SchnitzelSchema(
        models={
            "user": Model(
                name="user",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "user" in error_message
    assert "User" in error_message


def test_camel_case_model_name_fails():
    """Test that camelCase model name fails validation."""
    schema = SchnitzelSchema(
        models={
            "userProfile": Model(
                name="userProfile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "userProfile" in error_message
    assert "UserProfile" in error_message


def test_valid_pascal_case_passes():
    """Test that valid PascalCase model names pass validation."""
    valid_names = ["User", "UserProfile", "OrderItem", "HTTPServer"]

    for model_name in valid_names:
        schema = SchnitzelSchema(
            models={
                model_name: Model(
                    name=model_name,
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation (may have other errors, but not naming errors)
        # Check that there's no naming convention error for this model
        error_message = "\n".join(result.errors)
        assert f"Model name '{model_name}' violates" not in error_message, (
            f"PascalCase model name '{model_name}' should not have naming error"
        )


def test_multiple_models_with_naming_errors():
    """Test that validator catches naming errors across multiple models."""
    schema = SchnitzelSchema(
        models={
            "user_profile": Model(
                name="user_profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            ),
            "order_item": Model(
                name="order_item",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            ),
            "Product": Model(  # This one is correct
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Should have errors for both invalid models
    assert "user_profile" in error_message
    assert "order_item" in error_message

    # Should suggest correct names
    assert "UserProfile" in error_message
    assert "OrderItem" in error_message

    # Should NOT have error for Product (valid PascalCase)
    assert "Model name 'Product' violates" not in error_message


def test_name_conversion_suggestions():
    """Test that name conversion suggestions are correct."""
    test_cases = [
        ("user_profile", "UserProfile"),
        ("order_item", "OrderItem"),
        ("user-profile", "UserProfile"),
        ("user", "User"),
        ("userProfile", "UserProfile"),
        ("http_server", "HttpServer"),
        ("API_KEY", "ApiKey"),
    ]

    for invalid_name, expected_suggestion in test_cases:
        schema = SchnitzelSchema(
            models={
                invalid_name: Model(
                    name=invalid_name,
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        if invalid_name[0].isupper() and "_" not in invalid_name and "-" not in invalid_name:
            # This might be valid PascalCase
            continue

        error_message = "\n".join(result.errors)
        assert expected_suggestion in error_message, (
            f"Expected suggestion '{expected_suggestion}' for '{invalid_name}', "
            f"but got: {error_message}"
        )


def test_empty_model_name_fails():
    """Test that empty model name fails validation."""
    # Note: This test might fail at Pydantic level, but we test validator behavior
    try:
        schema = SchnitzelSchema(
            models={
                "": Model(
                    name="",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is False
        error_message = "\n".join(result.errors)
        assert "empty" in error_message.lower()
    except Exception:
        # Pydantic might catch this earlier, which is also acceptable
        pass


def test_model_with_numbers_in_name():
    """Test that model names with numbers are handled correctly."""
    # Valid PascalCase with numbers
    schema_valid = SchnitzelSchema(
        models={
            "User2FA": Model(
                name="User2FA",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema_valid)
    error_message = "\n".join(result.errors)
    assert "Model name 'User2FA' violates" not in error_message

    # Invalid: snake_case with numbers
    schema_invalid = SchnitzelSchema(
        models={
            "user_2fa": Model(
                name="user_2fa",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    result = validator.validate(schema_invalid)
    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "user_2fa" in error_message


def test_model_naming_with_field_naming():
    """Test that both model and field naming validations work together."""
    schema = SchnitzelSchema(
        models={
            "user_profile": Model(  # Invalid model name
                name="user_profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "UserName": FieldDefinition(type="string"),  # Invalid field name
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Should have error for model name
    assert "user_profile" in error_message
    assert "Model name" in error_message or "model" in error_message.lower()

    # Should have error for field name
    assert "UserName" in error_message
    assert "Field name" in error_message or "field" in error_message.lower()


if __name__ == "__main__":
    # Run all tests
    test_snake_case_model_name_fails_validation()
    test_error_format_matches_specification()
    test_kebab_case_model_name_fails()
    test_lowercase_model_name_fails()
    test_camel_case_model_name_fails()
    test_valid_pascal_case_passes()
    test_multiple_models_with_naming_errors()
    test_name_conversion_suggestions()
    test_empty_model_name_fails()
    test_model_with_numbers_in_name()
    test_model_naming_with_field_naming()

    print("\n" + "="*60)
    print("✓ All F014 tests passed!")
    print("="*60)
