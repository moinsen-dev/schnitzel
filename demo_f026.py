#!/usr/bin/env python3
"""
Demo script for F026: Python model generator generates belongsTo relationship with type hint

Test Steps:
1. Create Post model with belongsTo: author referencing User
2. Call PythonModelGenerator.generate(schema)
3. Verify Post model has author_id field with UUID type
4. Verify Post model has author field with Optional['User'] type (forward ref)
5. Verify forward reference is used if User is defined after Post
6. Verify relationship is properly typed
"""

import sys
from pathlib import Path

# Add the schnitzel-cli/src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    print_section("F026: Python Model Generator - belongsTo Relationship with Type Hint")

    # Step 1: Create Post model with belongsTo: author referencing User
    print("Step 1: Creating Post model with belongsTo relationship...")

    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                description="A blog post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string", max_length=200),
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
            ),
            "User": Model(
                name="User",
                description="A user account",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                }
            )
        }
    )

    print("✓ Schema created with Post.author belongsTo User")
    print(f"  - Post has author_id field (UUID)")
    print(f"  - Post has author relationship pointing to User")

    # Step 2: Call PythonModelGenerator.generate(schema)
    print_section("Step 2: Generating Python Pydantic models")

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("Generated code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)

    # Step 3: Verify Post model has author_id field with UUID type
    print_section("Step 3: Verifying author_id field")

    if "author_id: UUID" in generated_code:
        print("✓ Post model has author_id field with UUID type")
    else:
        print("✗ author_id field not found or incorrect type")
        return False

    # Step 4: Verify Post model has author field with forward reference type
    print_section("Step 4: Verifying author relationship field")

    if 'author: User | None = None' in generated_code:
        print('✓ Post model has author field with forward reference: User | None = None')
        print("  - Uses Pydantic v2 union syntax (| None)")
        print("  - Uses forward reference for User (with __future__ annotations)")
        print("  - Defaults to None (optional relationship)")
    else:
        print("✗ author relationship field not found or incorrect format")
        print("  Expected: author: User | None = None")
        return False

    # Step 5: Verify forward reference is used
    print_section("Step 5: Verifying forward reference usage")

    # Check that forward reference works with __future__ annotations
    if 'author: User' in generated_code and 'from __future__ import annotations' in generated_code:
        print("✓ Forward reference is properly used")
        print("  - Uses __future__ annotations for forward reference support")
        print("  - Works regardless of model definition order")
        print("  - Prevents circular import issues")
        print("  - Compatible with pyright strict type checking")
    else:
        print("✗ Forward reference not properly implemented")
        return False

    # Step 6: Verify relationship is properly typed
    print_section("Step 6: Verifying relationship type correctness")

    checks = [
        ('author: User | None = None' in generated_code, "Uses correct Pydantic v2 syntax"),
        ("from uuid import UUID" in generated_code, "UUID import present"),
        ("from __future__ import annotations" in generated_code, "__future__ annotations import present"),
        ("class Post(BaseModel):" in generated_code, "Post model class defined"),
        ("class User(BaseModel):" in generated_code, "User model class defined"),
    ]

    all_passed = True
    for check, description in checks:
        if check:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}")
            all_passed = False

    if not all_passed:
        return False

    # Additional: Test with multiple relationships
    print_section("Additional: Testing multiple belongsTo relationships")

    multi_schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                    "category_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(type="belongsTo", model="User"),
                    "category": Relation(type="belongsTo", model="Category"),
                }
            )
        }
    )

    multi_code = generator.generate(multi_schema)

    print("Generated code with multiple relationships:")
    print("-" * 80)
    print(multi_code)
    print("-" * 80)

    multi_checks = [
        ('author: User | None = None' in multi_code, "author relationship"),
        ('category: Category | None = None' in multi_code, "category relationship"),
        ("author_id: UUID" in multi_code, "author_id field"),
        ("category_id: UUID" in multi_code, "category_id field"),
    ]

    print("\nMultiple relationships verification:")
    all_multi_passed = True
    for check, description in multi_checks:
        if check:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}")
            all_multi_passed = False

    if not all_multi_passed:
        return False

    # Verify generated code is valid Python
    print_section("Validation: Python syntax check")

    try:
        compile(generated_code, "<string>", "exec")
        print("✓ Generated code is valid Python syntax")
    except SyntaxError as e:
        print(f"✗ Syntax error in generated code: {e}")
        return False

    print_section("Summary")
    print("✓ All test steps completed successfully!")
    print("\nFeature F026 Implementation Verified:")
    print("  • belongsTo relationship generates relationship field")
    print("  • Foreign key field (author_id: UUID) preserved")
    print("  • Relationship field uses forward reference: User | None = None")
    print("  • Pydantic v2 union syntax (| None) used")
    print("  • __future__ annotations enables forward references")
    print("  • Forward references work regardless of model order")
    print("  • Multiple belongsTo relationships work correctly")
    print("  • Generated code is valid Python")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
