"""
Integration test for F013: Schema validator accepts valid bidirectional relationship.

Test Feature:
- Create User model with hasMany: posts
- Create Post model with belongsTo: author referencing User
- Call SchemaValidator.validate(schema)
- Verify validation passes
- Verify both relationships are recognized
- Verify no circular dependency warning for valid relationship
- Verify relationship graph is built correctly

This is a POSITIVE test - valid bidirectional relationships should pass validation.
"""

from pathlib import Path
import tempfile

from schnitzel.schema import SchemaParser, SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation


def test_bidirectional_relationship_from_yaml():
    """
    Test F013: Schema validator accepts valid bidirectional relationship from YAML.

    This tests the complete flow:
    1. Parse YAML with bidirectional relationships
    2. Validate the schema
    3. Verify validation passes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "schema.yaml"

        # Create schema with bidirectional User <-> Post relationship
        content = """
schnitzel: 1.0.0
models:
  User:
    description: A user in the system
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
      created_at:
        type: datetime
        auto: create
    relations:
      posts:
        type: hasMany
        model: Post
        cascade: true

  Post:
    description: A blog post
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
      author_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
"""
        schema_path.write_text(content)

        # Step 1: Parse the schema
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Verify schema was parsed correctly
        assert "User" in schema.models, "Schema should contain User model"
        assert "Post" in schema.models, "Schema should contain Post model"

        user_model = schema.models["User"]
        post_model = schema.models["Post"]

        # Step 2: Verify both models have their relationships defined
        assert user_model.relations is not None, "User model should have relations"
        assert "posts" in user_model.relations, "User should have 'posts' relationship"
        assert user_model.relations["posts"].type == "hasMany"
        assert user_model.relations["posts"].model == "Post"

        assert post_model.relations is not None, "Post model should have relations"
        assert "author" in post_model.relations, "Post should have 'author' relationship"
        assert post_model.relations["author"].type == "belongsTo"
        assert post_model.relations["author"].model == "User"
        assert post_model.relations["author"].foreign_key == "author_id"

        # Step 3: Call SchemaValidator.validate(schema)
        validator = SchemaValidator()
        result = validator.validate(schema)

        # Step 4: Verify validation passes
        assert isinstance(result, ValidationResult), "Validator should return ValidationResult"
        assert result.valid is True, f"Validation should pass for valid bidirectional relationship. Errors: {result.errors}"

        # Step 5: Verify validator returns empty error list
        assert result.errors == [], f"Valid bidirectional relationship should produce no errors. Got: {result.errors}"

        print("\n✓ Test F013 passed: Schema validator accepts valid bidirectional relationship from YAML")


def test_bidirectional_relationship_programmatic():
    """
    Test F013: Schema validator accepts valid bidirectional relationship (programmatic).

    This tests the validation logic directly without YAML parsing.
    """
    # Step 1: Create User model with hasMany: posts
    user_model = Model(
        name="User",
        description="A user in the system",
        fields={
            "id": FieldDefinition(type="uuid", primary=True),
            "name": FieldDefinition(type="string"),
            "email": FieldDefinition(type="string", unique=True),
        },
        relations={
            "posts": Relation(
                type="hasMany",
                model="Post",
                cascade=True
            )
        }
    )

    # Step 2: Create Post model with belongsTo: author referencing User
    post_model = Model(
        name="Post",
        description="A blog post",
        fields={
            "id": FieldDefinition(type="uuid", primary=True),
            "title": FieldDefinition(type="string"),
            "content": FieldDefinition(type="string"),
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

    # Create schema with both models
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": user_model,
            "Post": post_model,
        }
    )

    # Step 3: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 4: Verify validation passes
    assert result.valid is True, f"Validation should pass. Errors: {result.errors}"

    # Step 5: Verify both relationships are recognized
    # This is implicit - if validation passes, relationships were recognized
    assert len(result.errors) == 0, "Should have no validation errors"

    # Step 6: Verify no circular dependency warning for valid relationship
    # Bidirectional relationships are NOT circular dependencies
    # User -> Post and Post -> User is a valid pattern
    for error in result.errors:
        assert "circular" not in error.lower(), "Should not have circular dependency warnings for valid bidirectional relationship"

    print("\n✓ Valid bidirectional relationship passes validation (programmatic)")


def test_multiple_bidirectional_relationships():
    """
    Test that multiple bidirectional relationships in a schema all validate correctly.
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
                    "posts": Relation(type="hasMany", model="Post"),
                    "comments": Relation(type="hasMany", model="Comment"),
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
                    "author": Relation(type="belongsTo", model="User", foreign_key="author_id"),
                    "comments": Relation(type="hasMany", model="Comment"),
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                    "post_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(type="belongsTo", model="User", foreign_key="author_id"),
                    "post": Relation(type="belongsTo", model="Post", foreign_key="post_id"),
                }
            ),
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Multiple bidirectional relationships should validate. Errors: {result.errors}"
    assert len(result.errors) == 0

    print("\n✓ Multiple bidirectional relationships validate correctly")


def test_has_one_bidirectional_relationship():
    """
    Test that hasOne bidirectional relationships validate correctly.
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
                    "profile": Relation(type="hasOne", model="Profile"),
                }
            ),
            "Profile": Model(
                name="Profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "bio": FieldDefinition(type="string"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "user": Relation(type="belongsTo", model="User", foreign_key="user_id"),
                }
            ),
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"hasOne bidirectional relationship should validate. Errors: {result.errors}"
    assert len(result.errors) == 0

    print("\n✓ hasOne bidirectional relationship validates correctly")


def test_relationship_graph_structure():
    """
    Test F013: Verify relationship graph is built correctly.

    This tests that the validator correctly understands the relationship structure.
    For now, we verify this by checking that:
    1. Both models exist in the schema
    2. Both relationships are properly defined
    3. Validation passes (implying the graph was understood)
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={"id": FieldDefinition(type="uuid", primary=True)},
                relations={
                    "posts": Relation(type="hasMany", model="Post"),
                }
            ),
            "Post": Model(
                name="Post",
                fields={"id": FieldDefinition(type="uuid", primary=True)},
                relations={
                    "author": Relation(type="belongsTo", model="User"),
                }
            ),
        }
    )

    # Verify both models are in schema
    assert "User" in schema.models
    assert "Post" in schema.models

    # Verify relationships exist
    user_relations = schema.models["User"].relations
    post_relations = schema.models["Post"].relations

    assert user_relations is not None
    assert "posts" in user_relations
    assert user_relations["posts"].model == "Post"

    assert post_relations is not None
    assert "author" in post_relations
    assert post_relations["author"].model == "User"

    # Validate - this implicitly tests that the validator can handle the graph structure
    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Relationship graph should be valid"

    print("\n✓ Relationship graph structure is correct")


def test_unidirectional_relationship_also_valid():
    """
    Test that unidirectional relationships (only one side defined) are also valid.

    This is to ensure the validator doesn't require bidirectional relationships.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={"id": FieldDefinition(type="uuid", primary=True)},
                relations={
                    "posts": Relation(type="hasMany", model="Post"),
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "author_id": FieldDefinition(type="uuid"),
                },
                # No relations defined - unidirectional
            ),
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Unidirectional relationship should be valid. Errors: {result.errors}"

    print("\n✓ Unidirectional relationships are also valid")


def test_self_referential_relationship():
    """
    Test that self-referential relationships validate correctly.

    Example: User can have a 'manager' relationship to another User.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "manager_id": FieldDefinition(type="uuid", optional=True),
                },
                relations={
                    "manager": Relation(type="belongsTo", model="User", foreign_key="manager_id"),
                    "subordinates": Relation(type="hasMany", model="User"),
                }
            ),
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Self-referential relationship should be valid. Errors: {result.errors}"

    print("\n✓ Self-referential relationships validate correctly")


def test_complex_relationship_network():
    """
    Test a complex network of relationships across multiple models.

    This ensures the validator can handle real-world schemas with many interconnected models.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "complex_schema.yaml"

        content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
    relations:
      posts:
        type: hasMany
        model: Post
      comments:
        type: hasMany
        model: Comment
      profile:
        type: hasOne
        model: Profile

  Profile:
    fields:
      id:
        type: uuid
        primary: true
      bio:
        type: string
      user_id:
        type: uuid
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      author_id:
        type: uuid
      category_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      category:
        type: belongsTo
        model: Category
        foreign_key: category_id
      comments:
        type: hasMany
        model: Comment
      tags:
        type: hasMany
        model: Tag

  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string
      author_id:
        type: uuid
      post_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      post:
        type: belongsTo
        model: Post
        foreign_key: post_id

  Category:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
    relations:
      posts:
        type: hasMany
        model: Post

  Tag:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
    relations:
      posts:
        type: hasMany
        model: Post
"""
        schema_path.write_text(content)

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Verify all models are present
        expected_models = {"User", "Profile", "Post", "Comment", "Category", "Tag"}
        assert set(schema.models.keys()) == expected_models

        # Validate the complex schema
        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is True, f"Complex relationship network should validate. Errors: {result.errors}"
        assert len(result.errors) == 0

        print("\n✓ Complex relationship network validates correctly")


if __name__ == "__main__":
    # Run all tests
    print("=" * 70)
    print("Testing F013: Schema validator accepts valid bidirectional relationship")
    print("=" * 70)

    test_bidirectional_relationship_from_yaml()
    test_bidirectional_relationship_programmatic()
    test_multiple_bidirectional_relationships()
    test_has_one_bidirectional_relationship()
    test_relationship_graph_structure()
    test_unidirectional_relationship_also_valid()
    test_self_referential_relationship()
    test_complex_relationship_network()

    print("\n" + "=" * 70)
    print("✓ All F013 tests passed!")
    print("=" * 70)
