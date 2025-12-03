"""
Integration test for F011: Schema validator verifies belongsTo relationship target exists.

Test steps:
1. Create schema with Post model having belongsTo: author pointing to User
2. Create schema WITHOUT User model
3. Call SchemaValidator.validate(schema)
4. Verify validation fails
5. Verify error indicates User model doesn't exist
6. Verify error shows the relationship definition
7. Verify error includes both model names (Post and User)
"""

import pytest
from schnitzel.schema import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation


def test_belongsto_relationship_target_missing():
    """
    Test F011: Schema validator verifies belongsTo relationship target exists.

    This test verifies that SchemaValidator correctly detects when a belongsTo
    relationship references a model that doesn't exist in the schema.
    """
    # Step 1 & 2: Create schema with Post model having belongsTo: author pointing to User
    # WITHOUT User model in the schema
    schema = SchnitzelSchema(
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

    # Verify Post model exists but User model doesn't
    assert "Post" in schema.models, "Schema should contain Post model"
    assert "User" not in schema.models, "Schema should NOT contain User model"

    # Step 3: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 4: Verify validation fails
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
    assert result.valid is False, "Validation should fail for missing relationship target"
    assert len(result.errors) > 0, "Should have at least one error"

    # Get the error message
    error_message = "\n".join(result.errors)

    # Step 5: Verify error indicates User model doesn't exist
    assert "User" in error_message, "Error should mention the missing User model"
    assert "non-existent" in error_message.lower() or "not" in error_message.lower(), (
        "Error should indicate the model doesn't exist"
    )

    # Step 6: Verify error shows the relationship definition
    assert "author" in error_message, "Error should mention the relationship name 'author'"
    assert "belongsTo" in error_message, "Error should show the relationship type 'belongsTo'"

    # Step 7: Verify error includes both model names (Post and User)
    assert "Post" in error_message, "Error should include the source model name 'Post'"
    assert "User" in error_message, "Error should include the target model name 'User'"

    print("\n✓ Test F011 passed: Schema validator detects missing belongsTo target")


def test_error_message_format():
    """Test that error message follows the required format."""
    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Verify all required components are present
    assert "author" in error_message, "Error should mention relationship name 'author'"
    assert "Post" in error_message, "Error should mention source model 'Post'"
    assert "User" in error_message, "Error should mention target model 'User'"
    assert "belongsTo" in error_message, "Error should mention relationship type 'belongsTo'"

    print("\n✓ Error message follows required format")


def test_hasone_relationship_target_missing():
    """Test that validator detects missing hasOne relationship targets."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
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

    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "Profile" in error_message
    assert "hasOne" in error_message
    assert "User" in error_message

    print("\n✓ Validator detects missing hasOne relationship targets")


def test_hasmany_relationship_target_missing():
    """Test that validator detects missing hasMany relationship targets."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
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

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)
    assert "Post" in error_message
    assert "hasMany" in error_message
    assert "User" in error_message

    print("\n✓ Validator detects missing hasMany relationship targets")


def test_valid_relationship_passes():
    """Test that validator accepts schemas with valid relationships."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
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

    # Should pass validation
    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"
    assert result.errors == [], "Should have no errors"

    print("\n✓ Validator accepts valid relationships")


def test_multiple_invalid_relationships():
    """Test that validator catches multiple invalid relationships."""
    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "author_id": FieldDefinition(type="uuid"),
                    "category_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User"  # User doesn't exist
                    ),
                    "category": Relation(
                        type="belongsTo",
                        model="Category"  # Category doesn't exist
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    assert len(result.errors) >= 2, "Should have errors for both missing relationships"

    error_message = "\n".join(result.errors)
    assert "User" in error_message
    assert "Category" in error_message
    assert "author" in error_message
    assert "category" in error_message

    print("\n✓ Validator detects multiple invalid relationships")


def test_model_with_no_relations():
    """Test that validator doesn't fail for models without relationships."""
    schema = SchnitzelSchema(
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

    # Should pass validation
    assert result.valid is True
    assert result.errors == []

    print("\n✓ Validator handles models without relationships")


def test_bidirectional_relationships_valid():
    """Test that validator accepts valid bidirectional relationships."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation - both models exist
    assert result.valid is True
    assert result.errors == []

    print("\n✓ Validator accepts valid bidirectional relationships")


def test_self_referencing_relationship_valid():
    """Test that validator accepts self-referencing relationships."""
    schema = SchnitzelSchema(
        models={
            "Category": Model(
                name="Category",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "parent_id": FieldDefinition(type="uuid", optional=True),
                },
                relations={
                    "parent": Relation(
                        type="belongsTo",
                        model="Category",  # Self-reference
                        foreign_key="parent_id"
                    ),
                    "children": Relation(
                        type="hasMany",
                        model="Category"  # Self-reference
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation - self-reference is valid
    assert result.valid is True
    assert result.errors == []

    print("\n✓ Validator accepts self-referencing relationships")


if __name__ == "__main__":
    # Run all tests
    test_belongsto_relationship_target_missing()
    test_error_message_format()
    test_hasone_relationship_target_missing()
    test_hasmany_relationship_target_missing()
    test_valid_relationship_passes()
    test_multiple_invalid_relationships()
    test_model_with_no_relations()
    test_bidirectional_relationships_valid()
    test_self_referencing_relationship_valid()
    print("\n" + "="*60)
    print("✓ All F011 tests passed!")
    print("="*60)
