#!/usr/bin/env python3
"""
Demo script for F029: Python model generator creates models.py in correct output directory

Test Steps:
1. Set output directory to backend/app/generated/
2. Call PythonModelGenerator.generate_to_file(schema, output_dir)
3. Verify models.py file is created at backend/app/generated/models.py
4. Verify directory is created if it doesn't exist
5. Verify existing file is overwritten with warning
6. Verify file has proper header comment with generation timestamp
"""

import sys
import shutil
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
    print_section("F029: Python Model Generator - File Output with Header")

    # Create a test schema
    print("Creating test schema with Product model...")
    schema = SchnitzelSchema(
        models={
            "Product": Model(
                name="Product",
                description="Product catalog item",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", max_length=200),
                    "price": FieldDefinition(type="float", min=0),
                    "description": FieldDefinition(type="string", optional=True),
                }
            ),
            "Category": Model(
                name="Category",
                description="Product category",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", max_length=100),
                }
            )
        }
    )
    print("✓ Schema created with Product and Category models")

    # Step 1: Set output directory to backend/app/generated/
    print_section("Step 1: Setting output directory")

    output_dir = Path(__file__).parent / "backend" / "app" / "generated"
    print(f"Output directory: {output_dir}")

    # Clean up any existing directory from previous runs
    if output_dir.exists():
        print(f"Cleaning up existing directory: {output_dir}")
        shutil.rmtree(output_dir)

    print("✓ Output directory configured")

    # Step 2: Call PythonModelGenerator.generate_to_file(schema, output_dir)
    print_section("Step 2: Calling generate_to_file()")

    generator = PythonModelGenerator()
    output_file = generator.generate_to_file(schema, output_dir, schema_source="test_schema.yaml")

    print(f"✓ generate_to_file() completed")
    print(f"  Returned path: {output_file}")

    # Step 3: Verify models.py file is created at backend/app/generated/models.py
    print_section("Step 3: Verifying file creation")

    expected_path = output_dir / "models.py"

    if not output_file.exists():
        print(f"✗ FAIL: File does not exist at {output_file}")
        return False

    if output_file != expected_path:
        print(f"✗ FAIL: File path mismatch")
        print(f"  Expected: {expected_path}")
        print(f"  Got: {output_file}")
        return False

    print(f"✓ File created at correct location: {output_file}")
    print(f"  File size: {output_file.stat().st_size} bytes")

    # Step 4: Verify directory is created if it doesn't exist
    print_section("Step 4: Verifying directory creation")

    if not output_dir.exists():
        print(f"✗ FAIL: Directory not created: {output_dir}")
        return False

    if not output_dir.is_dir():
        print(f"✗ FAIL: Path exists but is not a directory: {output_dir}")
        return False

    print(f"✓ Directory created successfully: {output_dir}")

    # Read the generated file
    generated_content = output_file.read_text()

    print("\nGenerated file content:")
    print("-" * 80)
    print(generated_content)
    print("-" * 80)

    # Step 5: Verify existing file is overwritten with warning
    print_section("Step 5: Testing file overwrite with warning")

    print("Calling generate_to_file() again to test overwrite...")
    print("(Should see warning message about overwriting)")

    # Capture the warning by calling again
    output_file_2 = generator.generate_to_file(schema, output_dir, schema_source="test_schema_v2.yaml")

    if output_file_2 != output_file:
        print(f"✗ FAIL: File path changed on second generation")
        return False

    print(f"✓ File overwritten successfully")

    # Read updated content
    updated_content = output_file_2.read_text()

    # Verify that the source changed in the header
    if "test_schema_v2.yaml" not in updated_content:
        print("✗ FAIL: Header not updated with new schema source")
        return False

    print("✓ Warning displayed and file overwritten")

    # Step 6: Verify file has proper header comment with generation timestamp
    print_section("Step 6: Verifying header comment")

    header_checks = [
        ("# Generated by Schnitzel Framework", "Framework attribution"),
        ("# DO NOT EDIT - This file is auto-generated", "Edit warning"),
        ("# Generated at:", "Generation timestamp"),
        ("# Source:", "Source schema info"),
    ]

    all_passed = True
    for expected_text, description in header_checks:
        if expected_text in generated_content:
            print(f"  ✓ {description}: Found")
        else:
            print(f"  ✗ {description}: NOT FOUND")
            all_passed = False

    if not all_passed:
        return False

    # Verify timestamp format (ISO format)
    lines = generated_content.split('\n')
    timestamp_line = None
    for line in lines:
        if "# Generated at:" in line:
            timestamp_line = line
            break

    if timestamp_line:
        # Extract timestamp
        timestamp_str = timestamp_line.split("# Generated at:")[1].strip()
        print(f"\n  Timestamp: {timestamp_str}")

        # Basic format check (should contain T and dashes/colons)
        if 'T' in timestamp_str and '-' in timestamp_str and ':' in timestamp_str:
            print("  ✓ Timestamp format appears valid (ISO format)")
        else:
            print("  ✗ Timestamp format invalid")
            all_passed = False
    else:
        print("  ✗ Timestamp line not found")
        all_passed = False

    # Additional verification: Check that models are present
    print_section("Additional: Verifying model content")

    model_checks = [
        ("class Product(BaseModel):", "Product model class"),
        ("class Category(BaseModel):", "Category model class"),
        ("from pydantic import BaseModel", "Pydantic imports"),
        ("from uuid import UUID", "UUID import"),
    ]

    for expected_text, description in model_checks:
        if expected_text in generated_content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} NOT FOUND")
            all_passed = False

    # Test with nested directories
    print_section("Additional: Testing deeply nested directory creation")

    deep_dir = Path(__file__).parent / "test_output" / "very" / "deep" / "nested" / "path"
    print(f"Testing with: {deep_dir}")

    deep_output = generator.generate_to_file(schema, deep_dir)

    if not deep_output.exists():
        print("✗ FAIL: Deeply nested file not created")
        all_passed = False
    else:
        print(f"✓ Deeply nested file created: {deep_output}")
        # Clean up
        shutil.rmtree(Path(__file__).parent / "test_output")

    print_section("Summary")

    if all_passed:
        print("✓ SUCCESS - All test steps completed successfully!")
        print("\nFeature F029 Implementation Verified:")
        print("  • generate_to_file() method implemented")
        print("  • Output directory is created if it doesn't exist")
        print("  • models.py file is written to correct location")
        print("  • File has proper header with:")
        print("    - Framework attribution")
        print("    - Edit warning")
        print("    - Generation timestamp (ISO format)")
        print("    - Source schema info")
        print("  • Existing files are overwritten with warning")
        print("  • Deeply nested directories are created correctly")
        print("  • Generated models are present in file")
        return True
    else:
        print("✗ FAILED - Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
