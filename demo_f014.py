#!/usr/bin/env python3
"""
Demo script for F014: Schema validator enforces PascalCase naming for models

This script demonstrates the model naming convention validation feature.
"""

from schnitzel.schema import SchemaValidator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


def demo_invalid_snake_case():
    """Demonstrate validation failure for snake_case model name."""
    print("\n" + "="*70)
    print("Demo 1: Invalid snake_case model name")
    print("="*70)

    schema = SchnitzelSchema(
        models={
            "user_profile": Model(
                name="user_profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nModel name: 'user_profile'")
    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")

    if not result.valid:
        print("\nError messages:")
        for error in result.errors:
            print(f"\n{error}")


def demo_invalid_kebab_case():
    """Demonstrate validation failure for kebab-case model name."""
    print("\n" + "="*70)
    print("Demo 2: Invalid kebab-case model name")
    print("="*70)

    schema = SchnitzelSchema(
        models={
            "user-profile": Model(
                name="user-profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nModel name: 'user-profile'")
    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")

    if not result.valid:
        print("\nError messages:")
        for error in result.errors:
            print(f"\n{error}")


def demo_invalid_camel_case():
    """Demonstrate validation failure for camelCase model name."""
    print("\n" + "="*70)
    print("Demo 3: Invalid camelCase model name")
    print("="*70)

    schema = SchnitzelSchema(
        models={
            "userProfile": Model(
                name="userProfile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nModel name: 'userProfile'")
    print(f"Validation result: {'PASS' if result.valid else 'FAIL'}")

    if not result.valid:
        print("\nError messages:")
        for error in result.errors:
            print(f"\n{error}")


def demo_valid_pascal_case():
    """Demonstrate validation success for valid PascalCase model names."""
    print("\n" + "="*70)
    print("Demo 4: Valid PascalCase model names")
    print("="*70)

    valid_names = ["User", "UserProfile", "OrderItem", "HTTPServer"]

    for model_name in valid_names:
        schema = SchnitzelSchema(
            models={
                model_name: Model(
                    name=model_name,
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Check that there's no naming convention error for this model
        has_naming_error = any(
            f"Model name '{model_name}' violates" in error
            for error in result.errors
        )

        print(f"\nModel name: '{model_name}' -> {'PASS' if not has_naming_error else 'FAIL'}")


def demo_multiple_errors():
    """Demonstrate validation with multiple model naming errors."""
    print("\n" + "="*70)
    print("Demo 5: Multiple models with naming errors")
    print("="*70)

    schema = SchnitzelSchema(
        models={
            "user_profile": Model(
                name="user_profile",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            ),
            "order_item": Model(
                name="order_item",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            ),
            "Product": Model(  # This one is correct
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation result: {'PASS' if result.valid else 'FAIL'}")
    print(f"Number of errors: {len(result.errors)}")

    if not result.valid:
        print("\nAll error messages:")
        for i, error in enumerate(result.errors, 1):
            print(f"\n--- Error {i} ---")
            print(error)


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("F014: Schema Validator Enforces PascalCase Naming for Models")
    print("="*70)

    demo_invalid_snake_case()
    demo_invalid_kebab_case()
    demo_invalid_camel_case()
    demo_valid_pascal_case()
    demo_multiple_errors()

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Features:")
    print("  - Validates that model names follow PascalCase convention")
    print("  - Provides clear error messages with naming convention rules")
    print("  - Suggests correct names based on the invalid input")
    print("  - Handles snake_case, kebab-case, camelCase, and other formats")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
