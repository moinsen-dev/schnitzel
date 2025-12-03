"""
Integration test for F012: Schema validator verifies hasMany relationship target exists.

This test also covers F011 (belongsTo relationship validation) since the implementation
handles all relationship types (belongsTo, hasMany, hasOne) uniformly.

Test steps for F012:
1. Create schema with User model having hasMany: posts pointing to Post
2. Create schema WITHOUT Post model
3. Call SchemaValidator.validate(schema)
4. Verify validation fails
5. Verify error indicates Post model doesn't exist
6. Verify error shows the relationship definition
7. Verify error includes relationship type (hasMany)
"""

from schnitzel.schema.models import FieldDefinition, Model, Relation, SchnitzelSchema
from schnitzel.schema.validator import SchemaValidator, ValidationResult


def test_hasmany_relationship_missing_target():
    """
    Test F012: Schema validator verifies hasMany relationship target exists.

    This test creates a schema with a User model that has a hasMany relationship
    pointing to a Post model, but the Post model is not defined in the schema.
    The validator should catch this and report a clear error.
    """
    # Step 1-2: Create schema with User model having hasMany: posts pointing to Post
    # But WITHOUT defining the Post model
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
                }
            )
        }
    )

    # Step 3: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 4: Verify validation fails
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is False, "Validation should fail when relationship target doesn't exist"

    # Step 5: Verify error indicates Post model doesn't exist
    assert len(result.errors) > 0, "Should have at least one error"
    error = result.errors[0]
    assert "Post" in error, "Error should mention the missing Post model"
    assert "does not exist" in error or "non-existent" in error, (
        "Error should clearly indicate the model doesn't exist"
    )

    # Step 6: Verify error shows the relationship definition
    assert "posts" in error, "Error should show the relationship name"
    assert "User" in error, "Error should show the source model name"

    # Step 7: Verify error includes relationship type (hasMany)
    assert "hasMany" in error, "Error should include the relationship type"

    print("\n" + "="*70)
    print("Test F012 passed: Schema validator verifies hasMany relationship target")
    print("="*70)
    print(f"\nError message:\n{error}")


def test_belongsto_relationship_missing_target():
    """
    Test F011: Schema validator verifies belongsTo relationship target exists.

    This test creates a schema with a Post model that has a belongsTo relationship
    pointing to a User model, but the User model is not defined in the schema.
    """
    # Create schema with Post model having belongsTo: author pointing to User
    # But WITHOUT defining the User model
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="author_id"
                    )
                }
            )
        }
    )

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails
    assert result.valid is False, "Validation should fail when belongsTo target doesn't exist"
    assert len(result.errors) > 0, "Should have at least one error"

    # Verify error content
    error = result.errors[0]
    assert "User" in error, "Error should mention the missing User model"
    assert "Post" in error, "Error should mention the Post model"
    assert "author" in error, "Error should show the relationship name"
    assert "belongsTo" in error, "Error should include the relationship type"

    print("\n" + "="*70)
    print("Test F011 passed: Schema validator verifies belongsTo relationship target")
    print("="*70)
    print(f"\nError message:\n{error}")


def test_hasone_relationship_missing_target():
    """
    Test that hasOne relationships are also validated for missing targets.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "profile": Relation(
                        type="hasOne",
                        model="Profile"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails
    assert result.valid is False, "Validation should fail when hasOne target doesn't exist"
    assert len(result.errors) > 0, "Should have at least one error"

    # Verify error content
    error = result.errors[0]
    assert "Profile" in error, "Error should mention the missing Profile model"
    assert "hasOne" in error, "Error should include the relationship type"

    print("\n" + "="*70)
    print("Test passed: Schema validator verifies hasOne relationship target")
    print("="*70)


def test_multiple_missing_relationship_targets():
    """
    Test that multiple missing relationship targets are all reported.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post"),
                    "profile": Relation(type="hasOne", model="Profile"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation fails with multiple errors
    assert result.valid is False, "Validation should fail"
    assert len(result.errors) == 2, f"Should have 2 errors, got {len(result.errors)}"

    # Check that both missing models are reported
    all_errors = "\n".join(result.errors)
    assert "Post" in all_errors, "Should report missing Post model"
    assert "Profile" in all_errors, "Should report missing Profile model"

    print("\n" + "="*70)
    print("Test passed: Multiple missing relationship targets are reported")
    print("="*70)


def test_valid_bidirectional_relationship():
    """
    Test F013: Schema validator accepts valid bidirectional relationship.

    This verifies that when both models exist and reference each other correctly,
    validation passes.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post")
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="author_id"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Validation should pass for valid relationships. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors"

    print("\n" + "="*70)
    print("Test F013 passed: Valid bidirectional relationship accepted")
    print("="*70)


def test_relationship_validation_with_no_relations():
    """
    Test that models without relationships pass validation.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
                # No relations defined
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, "Validation should pass for models without relationships"
    assert len(result.errors) == 0, "Should have no errors"

    print("\n" + "="*70)
    print("Test passed: Models without relationships pass validation")
    print("="*70)


def test_error_message_format():
    """
    Verify the error message contains all required information in a clear format.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error = result.errors[0]

    # Verify all required information is present
    assert "Post" in error, "Error should mention target model name"
    assert "User" in error, "Error should mention source model name"
    assert "posts" in error, "Error should mention relationship name"
    assert "hasMany" in error, "Error should mention relationship type"

    # Verify error is multi-line and informative
    lines = error.split("\n")
    assert len(lines) >= 3, "Error should be multi-line with detailed information"

    print("\n" + "="*70)
    print("Test passed: Error message format is clear and informative")
    print("="*70)
    print(f"\nFull error message:\n{error}")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*70)
    print("Running F012 (hasMany) and F011 (belongsTo) validation tests")
    print("="*70)

    test_hasmany_relationship_missing_target()
    test_belongsto_relationship_missing_target()
    test_hasone_relationship_missing_target()
    test_multiple_missing_relationship_targets()
    test_valid_bidirectional_relationship()
    test_relationship_validation_with_no_relations()
    test_error_message_format()

    print("\n" + "="*70)
    print("All relationship validation tests passed!")
    print("="*70)
