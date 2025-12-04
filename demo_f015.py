#!/usr/bin/env python3
"""
Demonstration of F015: Schema validator enforces snake_case naming for fields.

This script demonstrates the new snake_case field name validation feature.
"""

import sys
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema import SchemaValidator


def demo_camel_case_violation():
    """Demonstrate validation failure for camelCase field names."""
    print("=" * 70)
    print("DEMO 1: camelCase field name violation")
    print("=" * 70)

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "firstName": FieldDefinition(type="string"),  # camelCase - should fail
                    "lastName": FieldDefinition(type="string"),   # camelCase - should fail
                    "email": FieldDefinition(type="string")       # valid snake_case
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'PASS' if result.valid else 'FAIL'}")
    print(f"Valid: {result.valid}")
    print(f"Number of errors: {len(result.errors)}\n")

    if result.errors:
        print("Errors:")
        for i, error in enumerate(result.errors, 1):
            print(f"\n{i}. {error}")

    print("\n")


def demo_valid_snake_case():
    """Demonstrate validation success for valid snake_case field names."""
    print("=" * 70)
    print("DEMO 2: Valid snake_case field names")
    print("=" * 70)

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "first_name": FieldDefinition(type="string"),
                    "last_name": FieldDefinition(type="string"),
                    "email_address": FieldDefinition(type="string"),
                    "created_at": FieldDefinition(type="datetime"),
                    "is_active": FieldDefinition(type="bool")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'PASS' if result.valid else 'FAIL'}")
    print(f"Valid: {result.valid}")
    print(f"Number of errors: {len(result.errors)}")

    if result.valid:
        print("\nAll field names are valid snake_case!")

    print("\n")


def demo_pascal_case_violation():
    """Demonstrate validation failure for PascalCase field names."""
    print("=" * 70)
    print("DEMO 3: PascalCase field name violation")
    print("=" * 70)

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Order": Model(
                name="Order",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "OrderTotal": FieldDefinition(type="float"),  # PascalCase - should fail
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'PASS' if result.valid else 'FAIL'}")
    print(f"Valid: {result.valid}")

    if result.errors:
        print("\nError:")
        print(result.errors[0])

    print("\n")


def demo_mixed_violations():
    """Demonstrate validation across multiple models with mixed violations."""
    print("=" * 70)
    print("DEMO 4: Multiple models with naming violations")
    print("=" * 70)

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "userName": FieldDefinition(type="string"),  # violation
                    "email": FieldDefinition(type="string")      # valid
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "postTitle": FieldDefinition(type="string"),      # violation
                    "publishedAt": FieldDefinition(type="datetime"),  # violation
                    "author_id": FieldDefinition(type="uuid")         # valid
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'PASS' if result.valid else 'FAIL'}")
    print(f"Valid: {result.valid}")
    print(f"Number of errors: {len(result.errors)}\n")

    if result.errors:
        print("Errors:")
        for i, error in enumerate(result.errors, 1):
            print(f"\n{i}. {'-' * 65}")
            print(error)

    print("\n")


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║        F015: Snake_case Field Name Validation Demo                ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print("\n")

    demo_camel_case_violation()
    demo_valid_snake_case()
    demo_pascal_case_violation()
    demo_mixed_violations()

    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)
    print("\n")
