"""
Integration test for F017: Schema validator validates required field constraints.

Test steps:
1. Create User model with field: email marked as required: true
2. Create another field: bio with required: false (or optional: true)
3. Call SchemaValidator.validate(schema)
4. Verify validation passes
5. Verify required constraint is parsed correctly
6. Verify optional fields are recognized
7. Verify validator tracks which fields are required
"""

from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema
from schnitzel.schema.validator import SchemaValidator, ValidationResult


def test_required_field_constraint_validation():
    """
    Test F017: Schema validator validates required field constraints.

    This test verifies that the validator correctly accepts and tracks
    required and optional field constraints.
    """
    # Step 1-2: Create User model with email marked as required
    # and bio marked as optional
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", required=True),
                    "bio": FieldDefinition(type="string", optional=True),
                    "name": FieldDefinition(type="string"),  # neither required nor optional
                }
            )
        }
    )

    # Step 3: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 4: Verify validation passes
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is True, f"Validation should pass for valid required/optional constraints. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors"

    # Step 5: Verify required constraint is parsed correctly
    required_fields = validator.get_required_fields("User")
    assert "email" in required_fields, "email should be tracked as required"

    # Step 6: Verify optional fields are recognized
    optional_fields = validator.get_optional_fields("User")
    assert "bio" in optional_fields, "bio should be tracked as optional"

    # Step 7: Verify validator tracks which fields are required
    # Required fields should only include fields explicitly marked as required
    assert len(required_fields) == 1, f"Should have exactly 1 required field, got {len(required_fields)}: {required_fields}"
    assert "email" in required_fields, "email should be the only required field"

    # Optional fields should only include fields explicitly marked as optional
    assert len(optional_fields) == 1, f"Should have exactly 1 optional field, got {len(optional_fields)}: {optional_fields}"
    assert "bio" in optional_fields, "bio should be the only optional field"

    # Fields without explicit required/optional should not be in either set
    assert "name" not in required_fields, "name should not be in required fields"
    assert "name" not in optional_fields, "name should not be in optional fields"
    assert "id" not in required_fields, "id should not be in required fields"
    assert "id" not in optional_fields, "id should not be in optional fields"

    print("\n" + "="*70)
    print("Test F017 passed: Schema validator validates required field constraints")
    print("="*70)
    print(f"\nRequired fields for User: {required_fields}")
    print(f"Optional fields for User: {optional_fields}")


def test_required_only_fields():
    """
    Test that a model can have only required fields.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", required=True),
                    "username": FieldDefinition(type="string", required=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"

    required_fields = validator.get_required_fields("User")
    assert len(required_fields) == 2, f"Should have 2 required fields, got {len(required_fields)}"
    assert "email" in required_fields, "email should be required"
    assert "username" in required_fields, "username should be required"

    optional_fields = validator.get_optional_fields("User")
    assert len(optional_fields) == 0, "Should have no optional fields"

    print("\n✓ Model with only required fields passes validation")


def test_optional_only_fields():
    """
    Test that a model can have only optional fields.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "nickname": FieldDefinition(type="string", optional=True),
                    "avatar": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"

    optional_fields = validator.get_optional_fields("User")
    assert len(optional_fields) == 2, f"Should have 2 optional fields, got {len(optional_fields)}"
    assert "nickname" in optional_fields, "nickname should be optional"
    assert "avatar" in optional_fields, "avatar should be optional"

    required_fields = validator.get_required_fields("User")
    assert len(required_fields) == 0, "Should have no required fields"

    print("✓ Model with only optional fields passes validation")


def test_mixed_required_optional_fields():
    """
    Test that a model can have a mix of required, optional, and neutral fields.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string", required=True),
                    "content": FieldDefinition(type="string", required=True),
                    "summary": FieldDefinition(type="string", optional=True),
                    "tags": FieldDefinition(type="string", optional=True),
                    "created_at": FieldDefinition(type="datetime"),  # neutral
                    "updated_at": FieldDefinition(type="datetime"),  # neutral
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"

    required_fields = validator.get_required_fields("Post")
    assert len(required_fields) == 2, f"Should have 2 required fields, got {required_fields}"
    assert "title" in required_fields
    assert "content" in required_fields

    optional_fields = validator.get_optional_fields("Post")
    assert len(optional_fields) == 2, f"Should have 2 optional fields, got {optional_fields}"
    assert "summary" in optional_fields
    assert "tags" in optional_fields

    # Neutral fields should not be in either set
    assert "created_at" not in required_fields
    assert "created_at" not in optional_fields
    assert "updated_at" not in required_fields
    assert "updated_at" not in optional_fields

    print("✓ Model with mixed required/optional/neutral fields passes validation")


def test_multiple_models_required_tracking():
    """
    Test that the validator correctly tracks required fields across multiple models.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", required=True),
                    "bio": FieldDefinition(type="string", optional=True),
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string", required=True),
                    "content": FieldDefinition(type="string", required=True),
                    "draft": FieldDefinition(type="bool", optional=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"

    # Check User model
    user_required = validator.get_required_fields("User")
    assert len(user_required) == 1
    assert "email" in user_required

    user_optional = validator.get_optional_fields("User")
    assert len(user_optional) == 1
    assert "bio" in user_optional

    # Check Post model
    post_required = validator.get_required_fields("Post")
    assert len(post_required) == 2
    assert "title" in post_required
    assert "content" in post_required

    post_optional = validator.get_optional_fields("Post")
    assert len(post_optional) == 1
    assert "draft" in post_optional

    print("✓ Multiple models with required/optional fields tracked correctly")


def test_mutually_exclusive_required_optional():
    """
    Test that a field cannot be both required and optional.
    This should fail at the FieldDefinition level via Pydantic validation.
    """
    try:
        # This should raise a ValueError from Pydantic validation
        field = FieldDefinition(
            type="string",
            required=True,
            optional=True
        )
        # If we get here, the validation didn't work
        assert False, "Should have raised ValueError for mutually exclusive required and optional"
    except ValueError as e:
        assert "required and optional" in str(e).lower(), f"Error should mention mutual exclusivity: {e}"
        print("✓ Field cannot be both required and optional (correctly rejected)")


def test_empty_model_no_constraints():
    """
    Test that a model with no fields has no required or optional fields.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "Empty": Model(
                name="Empty",
                fields={}
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Validation should pass (empty model is valid)
    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"

    required_fields = validator.get_required_fields("Empty")
    optional_fields = validator.get_optional_fields("Empty")

    assert len(required_fields) == 0, "Empty model should have no required fields"
    assert len(optional_fields) == 0, "Empty model should have no optional fields"

    print("✓ Empty model has no required or optional fields")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*70)
    print("Running F017 required field constraint validation tests")
    print("="*70)

    test_required_field_constraint_validation()
    test_required_only_fields()
    test_optional_only_fields()
    test_mixed_required_optional_fields()
    test_multiple_models_required_tracking()
    test_mutually_exclusive_required_optional()
    test_empty_model_no_constraints()

    print("\n" + "="*70)
    print("All F017 tests passed!")
    print("="*70)
