"""
Integration test for F018: Schema validator validates unique field constraints.

Test steps:
1. Create User model with email field marked as unique: true
2. Call SchemaValidator.validate(schema)
3. Verify validation passes
4. Verify unique constraint is recognized
5. Verify validator tracks unique fields for database generation
"""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema import SchemaValidator, ValidationResult


def test_unique_field_constraint_validation():
    """
    Test F018: Schema validator validates unique field constraints.

    This test verifies that SchemaValidator correctly accepts and tracks
    unique field constraints for database generation.
    """
    # Step 1: Create User model with email field marked as unique: true
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", unique=True),
                    "username": FieldDefinition(type="string", unique=True),
                    "name": FieldDefinition(type="string"),
                    "created_at": FieldDefinition(type="datetime"),
                }
            )
        }
    )

    # Step 2: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 3: Verify validation passes
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is True, f"Validation should pass for unique constraints. Errors: {result.errors}"
    assert result.errors == [], f"Should have no errors. Got: {result.errors}"

    # Step 4: Verify unique constraint is recognized
    assert hasattr(result, "unique_fields"), "ValidationResult should have unique_fields attribute"
    assert isinstance(result.unique_fields, dict), "unique_fields should be a dictionary"

    # Step 5: Verify validator tracks unique fields for database generation
    assert "User" in result.unique_fields, "User model should be in unique_fields tracking"
    assert "email" in result.unique_fields["User"], "email field should be tracked as unique"
    assert "username" in result.unique_fields["User"], "username field should be tracked as unique"
    assert "name" not in result.unique_fields["User"], "name field should NOT be tracked as unique"
    assert len(result.unique_fields["User"]) == 2, "Should track exactly 2 unique fields"

    print("\n✓ Test F018 passed: Schema validator validates unique field constraints")


def test_no_unique_fields_returns_empty_dict():
    """
    Test that models without unique fields result in empty unique_fields dict.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
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

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Validation should pass"
    assert result.unique_fields == {}, "Should have empty unique_fields dict when no unique constraints"

    print("✓ Models without unique fields return empty unique_fields dict")


def test_multiple_models_with_unique_fields():
    """
    Test that unique fields are tracked across multiple models.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", unique=True),
                    "name": FieldDefinition(type="string"),
                }
            ),
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "sku": FieldDefinition(type="string", unique=True),
                    "name": FieldDefinition(type="string"),
                }
            ),
            "Category": Model(
                name="Category",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),  # No unique constraint
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Validation should pass"
    assert "User" in result.unique_fields, "User model should be tracked"
    assert "Product" in result.unique_fields, "Product model should be tracked"
    assert "Category" not in result.unique_fields, "Category model should NOT be tracked (no unique fields)"
    assert result.unique_fields["User"] == ["email"], "User should have email as unique"
    assert result.unique_fields["Product"] == ["sku"], "Product should have sku as unique"

    print("✓ Multiple models with unique fields are tracked correctly")


def test_unique_field_with_various_types():
    """
    Test that unique constraint works with different field types.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Entity": Model(
                name="Entity",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "code": FieldDefinition(type="string", unique=True),
                    "serial_number": FieldDefinition(type="int", unique=True),
                    "identifier": FieldDefinition(type="uuid", unique=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Validation should pass for unique constraints on various types"
    assert len(result.unique_fields["Entity"]) == 3, "Should track 3 unique fields"
    assert "code" in result.unique_fields["Entity"], "string type can be unique"
    assert "serial_number" in result.unique_fields["Entity"], "int type can be unique"
    assert "identifier" in result.unique_fields["Entity"], "uuid type can be unique"

    print("✓ Unique constraint works with various field types")


def test_unique_constraint_default_is_false():
    """
    Test that unique constraint defaults to False when not specified.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string"),  # No unique specified
                }
            )
        }
    )

    # Verify the FieldDefinition has unique=False by default
    user_model = schema.models["User"]
    email_field = user_model.fields["email"]
    assert email_field.unique is False, "unique should default to False"

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Validation should pass"
    assert result.unique_fields == {}, "Should have empty unique_fields when no unique constraints"

    print("✓ Unique constraint defaults to False when not specified")


def test_unique_and_primary_together():
    """
    Test that a field can be both primary and unique.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True, unique=True),
                    "email": FieldDefinition(type="string", unique=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Validation should pass for field with both primary and unique"
    assert "User" in result.unique_fields, "User model should be tracked"
    # Both id and email should be tracked as unique
    assert "id" in result.unique_fields["User"], "id field should be tracked as unique"
    assert "email" in result.unique_fields["User"], "email field should be tracked as unique"

    print("✓ Field can be both primary and unique")


def test_unique_constraint_preserved_through_validation():
    """
    Test that unique constraint is preserved and accessible after validation.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", unique=True),
                }
            )
        }
    )

    # Verify FieldDefinition has unique attribute before validation
    user_model = schema.models["User"]
    email_field = user_model.fields["email"]
    assert hasattr(email_field, "unique"), "FieldDefinition should have unique attribute"
    assert email_field.unique is True, "email field should have unique=True"

    # Validate
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify unique constraint is still accessible after validation
    assert result.valid is True, "Validation should pass"
    assert email_field.unique is True, "unique constraint should be preserved after validation"

    print("✓ Unique constraint is preserved through validation")


def test_validation_result_structure():
    """
    Test that ValidationResult has the correct structure with unique_fields.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", unique=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify ValidationResult structure
    assert hasattr(result, "valid"), "ValidationResult should have 'valid' attribute"
    assert hasattr(result, "errors"), "ValidationResult should have 'errors' attribute"
    assert hasattr(result, "unique_fields"), "ValidationResult should have 'unique_fields' attribute"

    assert isinstance(result.valid, bool), "'valid' should be a boolean"
    assert isinstance(result.errors, list), "'errors' should be a list"
    assert isinstance(result.unique_fields, dict), "'unique_fields' should be a dict"

    # Verify unique_fields structure
    assert "User" in result.unique_fields, "unique_fields should contain model names as keys"
    assert isinstance(result.unique_fields["User"], list), "unique_fields values should be lists"
    assert all(isinstance(field_name, str) for field_name in result.unique_fields["User"]), \
        "unique_fields lists should contain field names as strings"

    print("✓ ValidationResult has correct structure with unique_fields")


def test_unique_field_with_other_constraints():
    """
    Test that unique constraint works alongside other field constraints.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(
                        type="string",
                        unique=True,
                        optional=False,
                        format="email"
                    ),
                    "age": FieldDefinition(
                        type="int",
                        unique=False,
                        min=0,
                        max=150
                    ),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Validation should pass with multiple constraints"
    assert "User" in result.unique_fields, "User model should be tracked"
    assert result.unique_fields["User"] == ["email"], "Only email should be tracked as unique"

    print("✓ Unique constraint works alongside other field constraints")


if __name__ == "__main__":
    # Run all tests
    test_unique_field_constraint_validation()
    test_no_unique_fields_returns_empty_dict()
    test_multiple_models_with_unique_fields()
    test_unique_field_with_various_types()
    test_unique_constraint_default_is_false()
    test_unique_and_primary_together()
    test_unique_constraint_preserved_through_validation()
    test_validation_result_structure()
    test_unique_field_with_other_constraints()
    print("\n" + "="*60)
    print("✓ All F018 tests passed!")
    print("="*60)
