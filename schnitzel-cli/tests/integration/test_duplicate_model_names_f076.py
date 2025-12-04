"""
Integration test for F076: Schema validator detects duplicate model names.

Test steps:
1. Create schema with duplicate model names (same name defined twice)
2. Call SchemaValidator.validate(schema)
3. Verify validation fails
4. Verify error message indicates duplicate model
5. Verify error message mentions which model is duplicated
6. Verify schemas with unique model names pass validation
"""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema import SchemaValidator, ValidationResult


def test_duplicate_model_detected():
    """
    Test F076: Schema validator detects duplicate model names.

    This test verifies that when the same model name is used twice in a schema
    (e.g., in the dictionary key vs model.name mismatch), the validator catches it.
    """
    # Create schema where model.name doesn't match dictionary key
    # This simulates a duplicate model name scenario
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string")
                }
            ),
            "Account": Model(
                name="User",  # Duplicate name!
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string")
                }
            )
        }
    )

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should fail validation
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is False, "Validation should fail when duplicate model names exist"
    assert len(result.errors) > 0, "Should have at least one error"

    # Verify error mentions the duplicate
    error_text = "\n".join(result.errors)
    assert "duplicate" in error_text.lower(), "Error should mention 'duplicate'"
    assert "User" in error_text, "Error should mention the duplicated model name 'User'"

    print("\n✓ Test passed: Duplicate model names are detected")


def test_unique_models_pass():
    """
    Test that schemas with unique model names pass validation.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string")
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string")
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass for unique model names. Errors: {result.errors}"
    assert result.errors == [], "Should have no errors for unique model names"

    print("✓ Unique model names pass validation")


def test_error_message_mentions_duplicate():
    """
    Test that error message clearly indicates which model is duplicated.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Customer": Model(
                name="Account",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True)
                }
            ),
            "Vendor": Model(
                name="Account",  # Duplicate!
                fields={
                    "id": FieldDefinition(type="uuid", primary=True)
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Should fail validation"
    assert len(result.errors) > 0, "Should have errors"

    error_text = "\n".join(result.errors)

    # Error should mention the duplicate model name
    assert "Account" in error_text, "Error should mention the duplicated model name 'Account'"
    assert "duplicate" in error_text.lower(), "Error should explicitly mention 'duplicate'"

    # Should ideally mention both locations where it appears
    # (either Customer/Account or Vendor/Account)
    assert "Customer" in error_text or "Vendor" in error_text, (
        "Error should mention at least one of the dictionary keys where duplicate appears"
    )

    print("✓ Error message clearly identifies the duplicate model")


def test_multiple_duplicates_detected():
    """
    Test that multiple duplicate model names are all detected.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "A": Model(
                name="Duplicate1",
                fields={"id": FieldDefinition(type="uuid", primary=True)}
            ),
            "B": Model(
                name="Duplicate1",  # First duplicate
                fields={"id": FieldDefinition(type="uuid", primary=True)}
            ),
            "C": Model(
                name="Duplicate2",
                fields={"id": FieldDefinition(type="uuid", primary=True)}
            ),
            "D": Model(
                name="Duplicate2",  # Second duplicate
                fields={"id": FieldDefinition(type="uuid", primary=True)}
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Should fail validation"

    error_text = "\n".join(result.errors)

    # Should report both duplicates
    assert "Duplicate1" in error_text, "Should report first duplicate"
    assert "Duplicate2" in error_text, "Should report second duplicate"

    print("✓ Multiple duplicate model names are detected")


def test_case_sensitive_model_names():
    """
    Test that model name comparison is case-sensitive.
    """
    # Model names should be case-sensitive, so "User" and "user" are different
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True)
                }
            ),
            "UserAccount": Model(
                name="user",  # Different case - should be allowed (though bad practice)
                fields={
                    "id": FieldDefinition(type="uuid", primary=True)
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass - "User" and "user" are different names (case-sensitive)
    # Note: "user" will fail PascalCase validation, but that's a different check
    assert "duplicate" not in "\n".join(result.errors).lower() or result.valid, (
        "Should not report duplicate for different case names (case-sensitive comparison)"
    )

    print("✓ Model name duplicate detection is case-sensitive")


def test_single_model_no_duplicate():
    """
    Test that a schema with a single model passes (no duplicate possible).
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Check specifically for duplicate errors (ignore other validation errors)
    error_text = "\n".join(result.errors)
    assert "duplicate" not in error_text.lower(), "Should not report duplicate for single model"

    print("✓ Single model schema has no duplicate")


def test_empty_schema_no_duplicate():
    """
    Test that an empty schema (no models) passes without duplicate errors.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={}
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should not have duplicate errors
    error_text = "\n".join(result.errors)
    assert "duplicate" not in error_text.lower(), "Should not report duplicate for empty schema"

    print("✓ Empty schema has no duplicate errors")


if __name__ == "__main__":
    # Run all tests
    print("Running F076 tests: Schema validator detects duplicate model names\n")
    print("="*60)

    test_duplicate_model_detected()
    test_unique_models_pass()
    test_error_message_mentions_duplicate()
    test_multiple_duplicates_detected()
    test_case_sensitive_model_names()
    test_single_model_no_duplicate()
    test_empty_schema_no_duplicate()

    print("\n" + "="*60)
    print("✓ All F076 tests passed!")
    print("="*60)
