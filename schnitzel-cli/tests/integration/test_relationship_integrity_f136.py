"""Integration test for F136: Relationship integrity - Bidirectional relationships with validation.

Test Requirements:
- Test bidirectional relationships (hasMany + belongsTo) validate correctly
- Test that both sides of relationship reference existing models
- Test that foreign keys are properly validated
- Test multiple bidirectional relationships in same schema
- Test hasOne + belongsTo bidirectional relationships
"""

import pytest
from schnitzel.schema import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation


def test_bidirectional_hasmany_belongsto_valid():
    """Test that valid bidirectional hasMany/belongsTo relationships pass validation."""
    schema = SchnitzelSchema(
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

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors"


def test_bidirectional_hasone_belongsto_valid():
    """Test that valid bidirectional hasOne/belongsTo relationships pass validation."""
    schema = SchnitzelSchema(
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
            ),
            "Profile": Model(
                name="Profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "user_id": FieldDefinition(type="uuid", unique=True),
                    "bio": FieldDefinition(type="string", optional=True),
                },
                relations={
                    "user": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors"


def test_multiple_bidirectional_relationships():
    """Test schema with multiple bidirectional relationships validates correctly."""
    schema = SchnitzelSchema(
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
                    ),
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
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
                    ),
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "content": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                    "post_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="author_id"
                    ),
                    "post": Relation(
                        type="belongsTo",
                        model="Post",
                        foreign_key="post_id"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors"


def test_bidirectional_relationship_missing_target():
    """Test that bidirectional relationships with missing target model fail validation."""
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
                        model="Post"  # Post model doesn't exist
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False, "Validation should fail for missing target model"
    assert len(result.errors) > 0, "Should have at least one error"

    error_message = "\n".join(result.errors)
    assert "Post" in error_message, "Error should mention missing Post model"
    assert "User" in error_message, "Error should mention source User model"


def test_foreign_key_field_exists():
    """Test that foreign key field exists in model with belongsTo relationship."""
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
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),  # Foreign key field exists
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

    # Should pass - foreign key field exists
    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"


def test_complex_relationship_graph():
    """Test complex bidirectional relationship graph with multiple models."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post"),
                    "profile": Relation(type="hasOne", model="Profile"),
                    "comments": Relation(type="hasMany", model="Comment"),
                }
            ),
            "Profile": Model(
                name="Profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "user_id": FieldDefinition(type="uuid", unique=True),
                },
                relations={
                    "user": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    )
                }
            ),
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
                        model="User",
                        foreign_key="author_id"
                    ),
                    "category": Relation(
                        type="belongsTo",
                        model="Category",
                        foreign_key="category_id"
                    ),
                    "comments": Relation(type="hasMany", model="Comment"),
                }
            ),
            "Category": Model(
                name="Category",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post")
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "author_id": FieldDefinition(type="uuid"),
                    "post_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="author_id"
                    ),
                    "post": Relation(
                        type="belongsTo",
                        model="Post",
                        foreign_key="post_id"
                    )
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # All models exist, relationships should validate correctly
    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no errors"


if __name__ == "__main__":
    test_bidirectional_hasmany_belongsto_valid()
    test_bidirectional_hasone_belongsto_valid()
    test_multiple_bidirectional_relationships()
    test_bidirectional_relationship_missing_target()
    test_foreign_key_field_exists()
    test_complex_relationship_graph()
    print("\n" + "="*60)
    print("✓ All F136 tests passed!")
    print("="*60)
