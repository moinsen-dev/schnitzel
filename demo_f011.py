#!/usr/bin/env python3
"""
Demo for F011: Schema validator verifies belongsTo relationship target exists

This demo shows how the SchemaValidator detects when a model relationship
references a model that doesn't exist in the schema.
"""

import sys
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema import SchemaValidator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_missing_belongsto_target():
    """Demo 1: BelongsTo relationship with missing target."""
    print_section("Demo 1: Missing belongsTo Target")

    # Create schema with Post model that references non-existent User model
    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "content": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",  # User model doesn't exist!
                        foreign_key="author_id"
                    )
                }
            )
        }
    )

    print("Schema created with Post model:")
    print("  - Post has belongsTo relationship: author -> User")
    print("  - User model does NOT exist in schema")
    print()

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")
    print()

    if not result.valid:
        print("Validation errors:")
        for error in result.errors:
            print(f"  {error}")
            print()


def demo_valid_relationship():
    """Demo 2: Valid relationship with existing target."""
    print_section("Demo 2: Valid Relationship")

    # Create schema with both User and Post models
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
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
                        model="User",  # User model exists!
                        foreign_key="author_id"
                    )
                }
            )
        }
    )

    print("Schema created with User and Post models:")
    print("  - User model exists")
    print("  - Post has belongsTo relationship: author -> User")
    print()

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")
    if not result.valid:
        print("Errors:", result.errors)
    else:
        print("  No errors - relationship target exists!")
    print()


def demo_multiple_relationship_types():
    """Demo 3: Multiple relationship types (belongsTo, hasMany, hasOne)."""
    print_section("Demo 3: Multiple Relationship Types")

    # Create schema with missing targets for different relationship types
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
                        model="Post"  # Missing
                    ),
                    "profile": Relation(
                        type="hasOne",
                        model="Profile"  # Missing
                    )
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User"  # Exists!
                    ),
                    "post": Relation(
                        type="belongsTo",
                        model="Post"  # Missing
                    )
                }
            )
        }
    )

    print("Schema with multiple relationship types:")
    print("  User model:")
    print("    - hasMany: posts -> Post (MISSING)")
    print("    - hasOne: profile -> Profile (MISSING)")
    print("  Comment model:")
    print("    - belongsTo: author -> User (EXISTS)")
    print("    - belongsTo: post -> Post (MISSING)")
    print()

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")
    print(f"Total errors: {len(result.errors)}")
    print()

    if not result.valid:
        print("Validation errors:")
        for i, error in enumerate(result.errors, 1):
            print(f"\nError {i}:")
            print(f"  {error}")


def demo_self_referencing():
    """Demo 4: Self-referencing relationships (valid case)."""
    print_section("Demo 4: Self-Referencing Relationships")

    # Create schema with self-referencing relationship
    schema = SchnitzelSchema(
        models={
            "Category": Model(
                name="Category",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "parent_id": FieldDefinition(type="uuid", optional=True),
                },
                relations={
                    "parent": Relation(
                        type="belongsTo",
                        model="Category",  # Self-reference - valid!
                        foreign_key="parent_id"
                    ),
                    "children": Relation(
                        type="hasMany",
                        model="Category"  # Self-reference - valid!
                    )
                }
            )
        }
    )

    print("Schema with self-referencing relationships:")
    print("  Category model:")
    print("    - belongsTo: parent -> Category (self)")
    print("    - hasMany: children -> Category (self)")
    print()

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")
    if not result.valid:
        print("Errors:", result.errors)
    else:
        print("  No errors - self-referencing relationships are valid!")
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  F011: Relationship Target Validation Demo")
    print("  SchemaValidator verifies relationship targets exist")
    print("=" * 70)

    demo_missing_belongsto_target()
    demo_valid_relationship()
    demo_multiple_relationship_types()
    demo_self_referencing()

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
