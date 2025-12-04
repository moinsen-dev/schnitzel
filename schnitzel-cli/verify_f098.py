#!/usr/bin/env python3
"""Verification script for F098: Python generator includes docstrings.

This script demonstrates that:
1. Models with descriptions generate docstrings
2. Models without descriptions don't generate docstrings
3. Multi-line descriptions are handled correctly
"""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


def demo_docstring_generation():
    """Demonstrate docstring generation from model descriptions."""

    print("=" * 80)
    print("F098: Python Generator Includes Docstrings")
    print("=" * 80)

    # Test 1: Model with description
    print("\n1. Model WITH description:")
    print("-" * 80)

    schema_with_desc = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="User account model with authentication and profile data",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", max_length=255),
                    "name": FieldDefinition(type="string", max_length=100),
                    "active": FieldDefinition(type="bool", default=True),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    code_with_desc = generator.generate(schema_with_desc)
    print(code_with_desc)

    # Test 2: Model without description
    print("\n2. Model WITHOUT description:")
    print("-" * 80)

    schema_without_desc = SchnitzelSchema(
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "price": FieldDefinition(type="float", min=0),
                }
            )
        }
    )

    code_without_desc = generator.generate(schema_without_desc)
    print(code_without_desc)

    # Test 3: Multi-line description
    print("\n3. Model with MULTI-LINE description:")
    print("-" * 80)

    multiline_desc = """Order model for e-commerce system.

This model represents customer orders and includes:
- Order items and quantities
- Payment information
- Shipping details
- Order status tracking"""

    schema_multiline = SchnitzelSchema(
        models={
            "Order": Model(
                name="Order",
                description=multiline_desc,
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "total": FieldDefinition(type="float", min=0),
                    "status": FieldDefinition(
                        type="enum",
                        values=["pending", "processing", "shipped", "delivered"]
                    ),
                }
            )
        }
    )

    code_multiline = generator.generate(schema_multiline)
    print(code_multiline)

    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS:")
    print("=" * 80)

    checks = []

    # Check 1: Model with description has docstring
    has_user_docstring = '"""User account model with authentication and profile data"""' in code_with_desc
    checks.append(("Model with description has docstring", has_user_docstring))

    # Check 2: Model without description has no docstring
    has_product_docstring = '"""' in code_without_desc.split("class Product")[1].split("\n")[1]
    checks.append(("Model without description has NO docstring", not has_product_docstring))

    # Check 3: Multi-line description is preserved
    has_multiline_content = "Order model for e-commerce system" in code_multiline
    checks.append(("Multi-line description is included", has_multiline_content))

    # Check 4: Docstrings use triple quotes
    has_triple_quotes = code_with_desc.count('"""') >= 2
    checks.append(("Docstrings use triple quotes", has_triple_quotes))

    # Print results
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("SUCCESS: All F098 requirements verified!")
    else:
        print("FAILURE: Some requirements not met")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = demo_docstring_generation()
    exit(0 if success else 1)
