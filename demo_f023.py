#!/usr/bin/env python3
"""
Demo script for F023: Python model generator handles optional fields correctly

Test Steps:
1. Create User model with required field: email and optional field: bio (optional: true)
2. Call PythonModelGenerator.generate(schema)
3. Verify email field has no Optional wrapper
4. Verify bio field has Optional[str] type OR str | None
5. Verify bio field has default value None
6. Verify Pydantic v2 syntax is used (not v1)
"""

import sys
from pathlib import Path

# Add the schnitzel-cli/src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    print_section("F023: Python Model Generator - Optional Fields Handling")

    # Step 1: Create User model with required field: email and optional field: bio
    print("Step 1: Creating User model with required field 'email' and optional field 'bio'...")

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "email": FieldDefinition(type="string"),
                    "bio": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    print("✓ User model created")
    print(f"  - email: type=string, optional=False (required)")
    print(f"  - bio: type=string, optional=True")

    # Step 2: Call PythonModelGenerator.generate(schema)
    print_section("Step 2: Generating Python Pydantic models")

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("Generated code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)

    # Step 3: Verify email field has no Optional wrapper
    print_section("Step 3: Verifying email field has no Optional wrapper")

    if "email: str" in generated_code and "email: str |" not in generated_code:
        print("✓ email field is correctly typed as 'str' (not optional)")
    else:
        print("✗ email field is incorrectly typed")
        return False

    # Step 4: Verify bio field has Optional[str] type OR str | None
    print_section("Step 4: Verifying bio field has str | None type (Pydantic v2)")

    if "bio: str | None" in generated_code:
        print("✓ bio field is correctly typed as 'str | None' (Pydantic v2 syntax)")
    elif "bio: Optional[str]" in generated_code:
        print("⚠ bio field uses Optional[str] (Pydantic v1 syntax)")
        print("  Expected: 'str | None' (Pydantic v2 syntax)")
        return False
    else:
        print("✗ bio field is incorrectly typed")
        return False

    # Step 5: Verify bio field has default value None
    print_section("Step 5: Verifying bio field has default value None")

    if "bio: str | None = None" in generated_code:
        print("✓ bio field has default value None")
    else:
        print("✗ bio field is missing default value None")
        return False

    # Step 6: Verify Pydantic v2 syntax is used (not v1)
    print_section("Step 6: Verifying Pydantic v2 syntax is used")

    # Check for v2 indicators
    uses_union_syntax = " | None" in generated_code
    uses_optional_import = "from typing import Optional" in generated_code

    if uses_union_syntax and not uses_optional_import:
        print("✓ Using Pydantic v2 syntax (| None instead of Optional)")
    elif uses_optional_import:
        print("✗ Using Pydantic v1 syntax (Optional import detected)")
        return False
    else:
        print("✗ Cannot verify Pydantic version syntax")
        return False

    # Additional tests
    print_section("Additional Tests")

    # Test multiple optional fields
    print("Testing model with multiple optional fields...")
    multi_optional_schema = SchnitzelSchema(
        models={
            "Profile": Model(
                name="Profile",
                fields={
                    "username": FieldDefinition(type="string"),
                    "bio": FieldDefinition(type="string", optional=True),
                    "website": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                }
            )
        }
    )

    multi_code = generator.generate(multi_optional_schema)
    print("\nGenerated Profile model:")
    print("-" * 80)
    print(multi_code)
    print("-" * 80)

    # Verify all optional fields
    checks = [
        ("username: str", "username is required"),
        ("bio: str | None = None", "bio is optional string"),
        ("website: str | None = None", "website is optional string"),
        ("age: int | None = None", "age is optional int"),
    ]

    all_passed = True
    for check_str, description in checks:
        if check_str in multi_code:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - NOT FOUND")
            all_passed = False

    if not all_passed:
        return False

    # Test with UUID fields
    print("\nTesting model with UUID and datetime fields...")
    complex_schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "content": FieldDefinition(type="string", optional=True),
                    "published_at": FieldDefinition(type="datetime", optional=True),
                }
            )
        }
    )

    complex_code = generator.generate(complex_schema)
    print("\nGenerated Post model:")
    print("-" * 80)
    print(complex_code)
    print("-" * 80)

    # Verify imports and types
    import_checks = [
        ("from uuid import UUID", "UUID import"),
        ("from datetime import datetime", "datetime import"),
    ]

    type_checks = [
        ("id: UUID", "id is UUID type"),
        ("title: str", "title is required string"),
        ("content: str | None = None", "content is optional string"),
        ("published_at: datetime | None = None", "published_at is optional datetime"),
    ]

    print("\nVerifying imports:")
    for check_str, description in import_checks:
        if check_str in complex_code:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - NOT FOUND")
            all_passed = False

    print("\nVerifying field types:")
    for check_str, description in type_checks:
        if check_str in complex_code:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - NOT FOUND")
            all_passed = False

    if not all_passed:
        return False

    # Summary
    print_section("Summary")
    print("✓ All test steps completed successfully!")
    print("\nFeature F023 Implementation Verified:")
    print("  • PythonModelGenerator class created")
    print("  • Required fields have no Optional wrapper (e.g., 'email: str')")
    print("  • Optional fields use Pydantic v2 syntax (e.g., 'bio: str | None = None')")
    print("  • Default value None is correctly added to optional fields")
    print("  • Imports are generated dynamically based on field types")
    print("  • Multiple optional fields are handled correctly")
    print("  • Complex types (UUID, datetime) work with optional modifier")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
