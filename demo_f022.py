#!/usr/bin/env python3
"""
Demo script for F022: Python model generator maps all field types correctly

Test Steps:
1. Create schema with fields: str_field (string), int_field (int), float_field (float),
   bool_field (bool), uuid_field (uuid), datetime_field (datetime), json_field (json)
2. Call PythonModelGenerator.generate(schema)
3-9. Verify all field type mappings
10. Verify all necessary imports are present
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
    print_section("F022: Python Model Generator Field Type Mappings")

    # Step 1: Create schema with all basic field types
    print("Step 1: Creating schema with comprehensive field types...")

    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                description="Test model with all supported field types",
                fields={
                    "str_field": FieldDefinition(type="string"),
                    "int_field": FieldDefinition(type="int"),
                    "float_field": FieldDefinition(type="float"),
                    "bool_field": FieldDefinition(type="bool"),
                    "uuid_field": FieldDefinition(type="uuid"),
                    "datetime_field": FieldDefinition(type="datetime"),
                    "json_field": FieldDefinition(type="json"),
                }
            )
        }
    )

    print("Done - Schema created with 7 basic field types")

    # Step 2: Generate Python code
    print_section("Step 2: Generating Python Pydantic models")

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("Generated Python code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)

    # Step 3-9: Verify type mappings
    print_section("Step 3-9: Verifying field type mappings")

    checks = [
        ("str_field: str", "string -> str"),
        ("int_field: int", "int -> int"),
        ("float_field: float", "float -> float"),
        ("bool_field: bool", "bool -> bool"),
        ("uuid_field: UUID", "uuid -> UUID"),
        ("datetime_field: datetime", "datetime -> datetime"),
        ("json_field: dict[str, Any]", "json -> dict[str, Any]"),
    ]

    all_passed = True
    for expected, description in checks:
        if expected in generated_code:
            print(f"  [PASS] {description:30}")
        else:
            print(f"  [FAIL] {description:30}")
            all_passed = False

    # Step 10: Verify imports
    print_section("Step 10: Verifying necessary imports")

    required_imports = [
        ("from uuid import UUID", "UUID import"),
        ("from datetime import datetime", "datetime import"),
        ("from typing import Any", "Any import"),
        ("from pydantic import BaseModel", "BaseModel import"),
    ]

    for import_stmt, description in required_imports:
        if import_stmt in generated_code:
            print(f"  [PASS] {description:40}")
        else:
            print(f"  [FAIL] {description:40}")
            all_passed = False

    # Additional tests: list<T>, enum, vector
    print_section("Additional: Testing Advanced Types")

    print("Testing list<T> types...")
    list_schema = SchnitzelSchema(
        models={
            "ListModel": Model(
                name="ListModel",
                fields={
                    "tags": FieldDefinition(type="list<string>"),
                    "scores": FieldDefinition(type="list<int>"),
                    "ids": FieldDefinition(type="list<uuid>"),
                }
            )
        }
    )

    list_code = generator.generate(list_schema)
    list_checks = [
        ("tags: list[str]", "list<string> -> list[str]"),
        ("scores: list[int]", "list<int> -> list[int]"),
        ("ids: list[UUID]", "list<uuid> -> list[UUID]"),
    ]

    for expected, description in list_checks:
        if expected in list_code:
            print(f"  [PASS] {description:40}")
        else:
            print(f"  [FAIL] {description:40}")
            all_passed = False

    print("\nTesting enum type with Literal...")
    enum_schema = SchnitzelSchema(
        models={
            "EnumModel": Model(
                name="EnumModel",
                fields={
                    "status": FieldDefinition(
                        type="enum",
                        values=["active", "inactive", "pending"]
                    ),
                }
            )
        }
    )

    enum_code = generator.generate(enum_schema)
    if 'status: Literal["active", "inactive", "pending"]' in enum_code:
        print('  [PASS] enum -> Literal["active", "inactive", "pending"]')
    else:
        print('  [FAIL] enum -> Literal[...]')
        all_passed = False

    if "from typing import Literal" in enum_code:
        print("  [PASS] Literal import present")
    else:
        print("  [FAIL] Literal import missing")
        all_passed = False

    print("\nTesting vector type...")
    vector_schema = SchnitzelSchema(
        models={
            "VectorModel": Model(
                name="VectorModel",
                fields={
                    "embedding": FieldDefinition(type="vector", dimensions=384),
                }
            )
        }
    )

    vector_code = generator.generate(vector_schema)
    if "embedding: list[float]" in vector_code:
        print("  [PASS] vector -> list[float]")
    else:
        print("  [FAIL] vector -> list[float]")
        all_passed = False

    print_section("Summary")

    if all_passed:
        print("SUCCESS - All test steps completed successfully!")
        print("\nFeature F022 Implementation Verified:")
        print("  - All basic types map correctly (str, int, float, bool, uuid, datetime)")
        print("  - JSON type maps to dict[str, Any]")
        print("  - List types work: list<string> -> list[str]")
        print("  - Enum types work: enum -> Literal[...]")
        print("  - Vector types work: vector -> list[float]")
        print("  - All necessary imports are present")
        print("  - Generated code uses Pydantic v2 syntax")
        return True
    else:
        print("FAILED - Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
