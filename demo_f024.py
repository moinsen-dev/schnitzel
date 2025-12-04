#!/usr/bin/env python3
"""
Demo script for F024: Python model generator handles default values correctly.

This script demonstrates:
1. Creating User model with status field (string) with default: 'active'
2. Creating count field (int) with default: 0
3. Calling PythonModelGenerator.generate(schema)
4. Verifying status field has default='active' in field definition
5. Verifying count field has default=0
6. Verifying defaults are properly quoted for strings
7. Verifying defaults are unquoted for numbers
"""

import sys
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_defaults():
    """Demo: String and numeric defaults."""
    print_section("1. Basic Default Values")

    # Create User model with default values
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "status": FieldDefinition(type="string", default="active"),
                    "count": FieldDefinition(type="int", default=0),
                    "is_active": FieldDefinition(type="bool", default=True),
                }
            )
        }
    )

    print("\nSchema:")
    print("  User:")
    print("    - id: uuid (primary)")
    print("    - status: string (default: 'active')")
    print("    - count: int (default: 0)")
    print("    - is_active: bool (default: True)")

    # Generate Python code
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python Code:")
    print("-" * 70)
    print(generated_code)
    print("-" * 70)

    # Verify requirements
    print("\nVerification:")
    print("-" * 70)

    # Check that status has quoted default
    if 'status: str = "active"' in generated_code or 'status: str = Field(default="active")' in generated_code:
        print("[✓] status field has default='active' with double quotes")
    elif "status: str = 'active'" in generated_code:
        print("[~] status field has default='active' with single quotes (acceptable)")
    else:
        print("[✗] status field default not found or incorrect")

    # Check that count has unquoted default
    if 'count: int = 0' in generated_code or 'count: int = Field(default=0)' in generated_code:
        print("[✓] count field has default=0 (unquoted)")
    else:
        print("[✗] count field default not found or incorrect")

    # Check that boolean has unquoted default
    if 'is_active: bool = True' in generated_code or 'is_active: bool = Field(default=True)' in generated_code:
        print("[✓] is_active field has default=True (unquoted)")
    else:
        print("[✗] is_active field default not found or incorrect")

    # Verify strings are quoted
    if '"active"' in generated_code or "'active'" in generated_code:
        print("[✓] String defaults are quoted")
    else:
        print("[✗] String defaults are not properly quoted")

    # Verify numbers are unquoted
    if "= 0" in generated_code and "count" in generated_code:
        print("[✓] Numeric defaults are unquoted")
    else:
        print("[✗] Numeric defaults are not properly unquoted")


def demo_optional_with_defaults():
    """Demo: Optional fields with explicit defaults."""
    print_section("2. Optional Fields with Explicit Defaults")

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "description": FieldDefinition(
                        type="string",
                        optional=True,
                        default="No description"
                    ),
                    "stock": FieldDefinition(
                        type="int",
                        optional=True,
                        default=0
                    ),
                }
            )
        }
    )

    print("\nSchema:")
    print("  Product:")
    print("    - id: uuid (primary)")
    print("    - name: string (required)")
    print("    - description: string (optional, default: 'No description')")
    print("    - stock: int (optional, default: 0)")

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python Code:")
    print("-" * 70)
    print(generated_code)
    print("-" * 70)

    print("\nVerification:")
    print("-" * 70)

    # Check that description has the explicit default, not None
    if ('= "No description"' in generated_code or "= 'No description'" in generated_code or
        'default="No description"' in generated_code or "default='No description'" in generated_code):
        print("[✓] description field uses explicit default, not None")
    elif "description: Optional[str] = None" in generated_code or "description: str | None = None" in generated_code:
        print("[✗] description field incorrectly defaults to None instead of 'No description'")
    else:
        print("[?] description field default unclear")

    # Check that stock has explicit default 0
    if ('stock:' in generated_code and '= 0' in generated_code) or ('stock' in generated_code and 'default=0' in generated_code):
        print("[✓] stock field uses explicit default 0")
    else:
        print("[✗] stock field default not found or incorrect")


def demo_optional_without_defaults():
    """Demo: Optional fields without explicit defaults get None."""
    print_section("3. Optional Fields Without Explicit Defaults")

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string"),
                    "phone": FieldDefinition(type="string", optional=True),
                    "bio": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    print("\nSchema:")
    print("  User:")
    print("    - id: uuid (primary)")
    print("    - email: string (required)")
    print("    - phone: string (optional, no default)")
    print("    - bio: string (optional, no default)")

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python Code:")
    print("-" * 70)
    print(generated_code)
    print("-" * 70)

    print("\nVerification:")
    print("-" * 70)

    # Check that optional fields without defaults get None
    if "phone:" in generated_code and ("= None" in generated_code or "default=None" in generated_code):
        print("[✓] Optional fields without explicit defaults get None")
    else:
        print("[✗] Optional fields not properly defaulting to None")


def demo_mixed_types():
    """Demo: All supported field types with defaults."""
    print_section("4. All Field Types with Defaults")

    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "Example": Model(
                name="Example",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", default="unnamed"),
                    "age": FieldDefinition(type="int", default=0),
                    "price": FieldDefinition(type="float", default=9.99),
                    "active": FieldDefinition(type="bool", default=False),
                    "tags": FieldDefinition(type="json", default={}),
                }
            )
        }
    )

    print("\nSchema:")
    print("  Example:")
    print("    - id: uuid (primary)")
    print("    - name: string (default: 'unnamed')")
    print("    - age: int (default: 0)")
    print("    - price: float (default: 9.99)")
    print("    - active: bool (default: False)")
    print("    - tags: json (default: {})")

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python Code:")
    print("-" * 70)
    print(generated_code)
    print("-" * 70)

    print("\nVerification:")
    print("-" * 70)

    # Verify each type
    checks = [
        ('"unnamed"' in generated_code or "'unnamed'" in generated_code,
         "String default is quoted"),
        ("= 0" in generated_code,
         "Int default is unquoted"),
        ("= 9.99" in generated_code,
         "Float default is unquoted"),
        ("= False" in generated_code,
         "Boolean default is unquoted and capitalized"),
    ]

    for passed, description in checks:
        print(f"[{'✓' if passed else '✗'}] {description}")


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print("  Feature F024 Demo: Python Model Generator Default Values")
    print("█" * 70)

    demo_basic_defaults()
    demo_optional_with_defaults()
    demo_optional_without_defaults()
    demo_mixed_types()

    print("\n" + "█" * 70)
    print("  Demo Complete!")
    print("█" * 70)
    print()


if __name__ == "__main__":
    main()
