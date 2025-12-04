#!/usr/bin/env python3
"""
Demonstration script for F016: Schema validator detects circular dependency in relationships.

This script demonstrates the circular dependency detection feature in the SchemaValidator.
It creates two schemas:
1. A schema with a circular dependency (A -> B -> A)
2. A valid schema with no circular dependencies
"""

import sys
sys.path.insert(0, 'schnitzel-cli/src')

from schnitzel.schema.models import FieldDefinition, Model, Relation, SchnitzelSchema
from schnitzel.schema.validator import SchemaValidator


def demo_circular_dependency():
    """Demonstrate detection of circular dependency."""
    print("="*70)
    print("DEMO: Circular Dependency Detection")
    print("="*70)
    print()

    print("Creating schema with circular dependency:")
    print("  Model A has belongsTo relationship to Model B")
    print("  Model B has belongsTo relationship to Model A")
    print()

    # Create schema with circular dependency
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "b": Relation(
                        type="belongsTo",
                        model="B",
                        foreign_key="b_id"
                    )
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "a_id": FieldDefinition(type="uuid"),
                    "value": FieldDefinition(type="int"),
                },
                relations={
                    "a": Relation(
                        type="belongsTo",
                        model="A",
                        foreign_key="a_id"
                    )
                }
            )
        }
    )

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print("Validation Result:")
    print(f"  Valid: {result.valid}")
    print(f"  Number of errors: {len(result.errors)}")
    print()

    if result.errors:
        print("Errors detected:")
        for i, error in enumerate(result.errors, 1):
            print(f"\nError {i}:")
            for line in error.split('\n'):
                print(f"  {line}")

    print()
    print("="*70)
    print()


def demo_valid_bidirectional():
    """Demonstrate valid bidirectional relationship."""
    print("="*70)
    print("DEMO: Valid Bidirectional Relationship")
    print("="*70)
    print()

    print("Creating schema with valid bidirectional relationship:")
    print("  User hasMany Posts")
    print("  Post belongsTo User")
    print("  (This is valid - hasMany doesn't create circular dependencies)")
    print()

    # Create schema with valid bidirectional relationship
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
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
                    "content": FieldDefinition(type="string"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    )
                }
            )
        }
    )

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print("Validation Result:")
    print(f"  Valid: {result.valid}")
    print(f"  Number of errors: {len(result.errors)}")
    print()

    if result.valid:
        print("  SUCCESS: Valid bidirectional relationship accepted!")
    else:
        print("Errors detected:")
        for i, error in enumerate(result.errors, 1):
            print(f"\nError {i}:")
            for line in error.split('\n'):
                print(f"  {line}")

    print()
    print("="*70)
    print()


def demo_three_way_cycle():
    """Demonstrate three-way circular dependency."""
    print("="*70)
    print("DEMO: Three-Way Circular Dependency")
    print("="*70)
    print()

    print("Creating schema with three-way circular dependency:")
    print("  Model A -> Model B -> Model C -> Model A")
    print()

    # Create schema with three-way cycle
    schema = SchnitzelSchema(
        schnitzel="1.0.0",
        models={
            "A": Model(
                name="A",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "b_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "b": Relation(type="belongsTo", model="B", foreign_key="b_id")
                }
            ),
            "B": Model(
                name="B",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "c_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "c": Relation(type="belongsTo", model="C", foreign_key="c_id")
                }
            ),
            "C": Model(
                name="C",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "a_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "a": Relation(type="belongsTo", model="A", foreign_key="a_id")
                }
            )
        }
    )

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    print("Validation Result:")
    print(f"  Valid: {result.valid}")
    print(f"  Number of errors: {len(result.errors)}")
    print()

    if result.errors:
        print("Errors detected:")
        for i, error in enumerate(result.errors, 1):
            print(f"\nError {i}:")
            for line in error.split('\n'):
                print(f"  {line}")

    print()
    print("="*70)
    print()


if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  F016: Circular Dependency Detection in Relationships".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")

    # Run demonstrations
    demo_circular_dependency()
    demo_valid_bidirectional()
    demo_three_way_cycle()

    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  All demonstrations complete!".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
