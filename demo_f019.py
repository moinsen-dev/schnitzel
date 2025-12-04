#!/usr/bin/env python3
"""
Demo script for F019: Schema validator validates min/max constraints for numeric fields.

This script demonstrates:
1. Creating a Product model with numeric constraints
2. Validating min/max constraints on int and float fields
3. Showing constraint validation errors
4. Verifying constraints are stored for code generation
"""

import sys
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_valid_constraints():
    """Demo: Valid numeric constraints on int and float fields."""
    print_section("1. Valid Numeric Constraints")

    # Create Product model with price and stock constraints
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "price": FieldDefinition(type="float", min=0, max=1000000),
                    "stock_quantity": FieldDefinition(type="int", min=0, max=10000),
                    "discount_percent": FieldDefinition(type="int", min=0, max=100)
                }
            )
        }
    )

    print("\nSchema:")
    print("  Product:")
    print("    - id: uuid (primary)")
    print("    - name: string")
    print("    - price: float (min: 0, max: 1000000)")
    print("    - stock_quantity: int (min: 0, max: 10000)")
    print("    - discount_percent: int (min: 0, max: 100)")

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'✓ PASSED' if result.valid else '✗ FAILED'}")

    if result.valid:
        print("\nConstraints stored in FieldDefinition:")
        product = schema.models["Product"]
        print(f"  price.min = {product.fields['price'].min}")
        print(f"  price.max = {product.fields['price'].max}")
        print(f"  stock_quantity.min = {product.fields['stock_quantity'].min}")
        print(f"  stock_quantity.max = {product.fields['stock_quantity'].max}")
        print(f"  discount_percent.min = {product.fields['discount_percent'].min}")
        print(f"  discount_percent.max = {product.fields['discount_percent'].max}")
        print("\n✓ These constraints are available for code generation!")


def demo_invalid_type_constraints():
    """Demo: Min/max constraints on non-numeric types fail validation."""
    print_section("2. Invalid: Constraints on Non-Numeric Types")

    # Try to add constraints to a string field (invalid)
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", min=0, max=100)  # ✗ Invalid
                }
            )
        }
    )

    print("\nSchema:")
    print("  Product:")
    print("    - id: uuid (primary)")
    print("    - name: string (min: 0, max: 100)  ← Invalid!")

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'✓ PASSED' if result.valid else '✗ FAILED (as expected)'}")

    if not result.valid:
        print("\nValidation Errors:")
        for error in result.errors:
            print(f"\n{error}")


def demo_min_greater_than_max():
    """Demo: Min > max constraint fails validation."""
    print_section("3. Invalid: Min > Max")

    # Create field with min > max (invalid)
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "price": FieldDefinition(type="float", min=1000, max=100)  # ✗ Invalid
                }
            )
        }
    )

    print("\nSchema:")
    print("  Product:")
    print("    - id: uuid (primary)")
    print("    - price: float (min: 1000, max: 100)  ← Invalid!")

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'✓ PASSED' if result.valid else '✗ FAILED (as expected)'}")

    if not result.valid:
        print("\nValidation Errors:")
        for error in result.errors:
            print(f"\n{error}")


def demo_partial_constraints():
    """Demo: Fields can have only min or only max."""
    print_section("4. Partial Constraints (Min Only or Max Only)")

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Measurement": Model(
                name="Measurement",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "temperature": FieldDefinition(type="float", min=-273.15),  # Min only
                    "humidity_percent": FieldDefinition(type="int", max=100),  # Max only
                    "pressure": FieldDefinition(type="float")  # No constraints
                }
            )
        }
    )

    print("\nSchema:")
    print("  Measurement:")
    print("    - id: uuid (primary)")
    print("    - temperature: float (min: -273.15, no max)")
    print("    - humidity_percent: int (max: 100, no min)")
    print("    - pressure: float (no constraints)")

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'✓ PASSED' if result.valid else '✗ FAILED'}")

    if result.valid:
        measurement = schema.models["Measurement"]
        print("\nConstraints stored:")
        print(f"  temperature: min={measurement.fields['temperature'].min}, max={measurement.fields['temperature'].max}")
        print(f"  humidity_percent: min={measurement.fields['humidity_percent'].min}, max={measurement.fields['humidity_percent'].max}")
        print(f"  pressure: min={measurement.fields['pressure'].min}, max={measurement.fields['pressure'].max}")


def demo_real_world_example():
    """Demo: Real-world e-commerce schema with various constraints."""
    print_section("5. Real-World Example: E-Commerce Schema")

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "price": FieldDefinition(type="float", min=0.01, max=999999.99),
                    "cost": FieldDefinition(type="float", min=0),
                    "stock": FieldDefinition(type="int", min=0),
                    "discount_percent": FieldDefinition(type="int", min=0, max=100),
                    "rating": FieldDefinition(type="float", min=0.0, max=5.0),
                    "review_count": FieldDefinition(type="int", min=0)
                }
            ),
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", unique=True),
                    "age": FieldDefinition(type="int", min=13, max=150),
                    "credit_score": FieldDefinition(type="int", min=300, max=850)
                }
            )
        }
    )

    print("\nSchema:")
    print("\n  Product:")
    print("    - id: uuid (primary)")
    print("    - name: string")
    print("    - price: float (min: 0.01, max: 999999.99)")
    print("    - cost: float (min: 0)")
    print("    - stock: int (min: 0)")
    print("    - discount_percent: int (min: 0, max: 100)")
    print("    - rating: float (min: 0.0, max: 5.0)")
    print("    - review_count: int (min: 0)")
    print("\n  User:")
    print("    - id: uuid (primary)")
    print("    - email: string (unique)")
    print("    - age: int (min: 13, max: 150)")
    print("    - credit_score: int (min: 300, max: 850)")

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"\nValidation Result: {'✓ PASSED' if result.valid else '✗ FAILED'}")

    if result.valid:
        print("\n✓ All constraints validated successfully!")
        print("✓ Ready for code generation with proper validation rules!")


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print("  Feature F019 Demo: Min/Max Constraints for Numeric Fields")
    print("█" * 70)

    demo_valid_constraints()
    demo_invalid_type_constraints()
    demo_min_greater_than_max()
    demo_partial_constraints()
    demo_real_world_example()

    print("\n" + "█" * 70)
    print("  Demo Complete!")
    print("█" * 70)
    print()


if __name__ == "__main__":
    main()
