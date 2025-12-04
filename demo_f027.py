#!/usr/bin/env python3
"""Demo script for F027: Python model generator hasMany relationship support.

This script demonstrates:
1. Creating a User model with hasMany posts
2. Generating Python Pydantic models
3. Verifying the generated code structure
"""

import sys
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


def main():
    print("=" * 80)
    print("F027 Demo: Python Model Generator - hasMany Relationships")
    print("=" * 80)
    print()

    # Step 1: Create schema with User -> Posts relationship
    print("Step 1: Creating schema with User hasMany Posts...")
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="User model with posts relationship",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
                }
            ),
            "Post": Model(
                name="Post",
                description="Post model",
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
                    ),
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
                }
            ),
            "Comment": Model(
                name="Comment",
                description="Comment model",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string"),
                    "post_id": FieldDefinition(type="uuid"),
                }
            )
        }
    )
    print("✓ Schema created successfully")
    print()

    # Step 2: Generate Python models
    print("Step 2: Generating Python Pydantic models...")
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)
    print("✓ Models generated successfully")
    print()

    # Step 3: Display generated code
    print("Step 3: Generated Python code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)
    print()

    # Step 4: Verify key features
    print("Step 4: Verifying key features...")

    checks = [
        ('posts: list["Post"] = []', "hasMany posts relationship"),
        ('comments: list["Comment"] = []', "hasMany comments relationship"),
        ('author: "User" | None = None', "belongsTo author relationship"),
        ("class User(BaseModel):", "User model class"),
        ("class Post(BaseModel):", "Post model class"),
        ("class Comment(BaseModel):", "Comment model class"),
        ("from pydantic import BaseModel", "Pydantic BaseModel import"),
        ("from uuid import UUID", "UUID import"),
    ]

    all_passed = True
    for check_str, description in checks:
        if check_str in generated_code:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - MISSING!")
            all_passed = False

    print()

    # Step 5: Verify code is valid Python
    print("Step 5: Verifying generated code is valid Python...")
    try:
        compile(generated_code, "<string>", "exec")
        print("  ✓ Generated code compiles successfully")
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        all_passed = False

    print()
    print("=" * 80)
    if all_passed:
        print("✓ All checks passed! F027 implementation is working correctly.")
    else:
        print("✗ Some checks failed!")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
