#!/usr/bin/env python3
"""
Verification script for F009: Schema validator accepts valid model with all supported field types.

This script demonstrates:
1. Creating a schema with all supported field types
2. Validating the schema using SchemaValidator
3. Showing that validation passes with no errors
"""

from pathlib import Path
from schnitzel.schema import SchemaParser, SchemaValidator

def main():
    print("="*70)
    print("F009 Feature Verification: Schema Validator")
    print("="*70)
    print()

    # Test 1: Load and validate schema with all field types
    print("Test 1: Validating schema with all supported field types")
    print("-" * 70)

    test_file = Path(__file__).parent / "tests" / "integration" / "fixtures" / "all_field_types_schema.yaml"

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(test_file)
    print(f"✓ Parsed schema from: {test_file.name}")
    print(f"✓ Found model: {list(schema.models.keys())[0]}")

    model = schema.models["CompleteModel"]
    print(f"✓ Model has {len(model.fields)} fields:")
    for field_name, field_def in model.fields.items():
        print(f"    - {field_name}: {field_def.type}")

    print()

    # Validate the schema
    print("Validating schema...")
    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"✓ Validation result:")
    print(f"    - Valid: {result.valid}")
    print(f"    - Errors: {result.errors if result.errors else '(none)'}")

    print()

    if result.valid:
        print("SUCCESS: All field types are recognized and validated!")
    else:
        print("FAILURE: Validation found errors:")
        for error in result.errors:
            print(f"  - {error}")

    print()
    print("="*70)
    print("F009 Verification Complete!")
    print("="*70)

if __name__ == "__main__":
    main()
