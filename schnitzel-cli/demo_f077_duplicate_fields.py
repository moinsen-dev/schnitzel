#!/usr/bin/env python3
"""
Demo for F077: Schema validator detects duplicate field names in same model.

This script demonstrates how the SchemaParser detects duplicate field names
when parsing YAML schema files, providing clear error messages to help users
identify and fix the issue.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile
from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.exceptions import YAMLParseError


def demo_duplicate_field_detection():
    """Demonstrate duplicate field detection in YAML parsing."""
    print("=" * 70)
    print("F077 Demo: Duplicate Field Name Detection")
    print("=" * 70)
    print()

    # Example 1: YAML with duplicate field names
    print("Example 1: Schema with duplicate 'name' field")
    print("-" * 70)

    yaml_with_duplicate = """
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
      name:
        type: int
"""

    print("YAML Content:")
    print(yaml_with_duplicate)

    # Write to temporary file
    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_with_duplicate)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()
        print("Parsing schema...")
        schema = parser.parse(temp_path)
        print("✗ Unexpected: Schema parsed successfully (should have failed)")
    except YAMLParseError as e:
        print("✓ Duplicate field detected!")
        print()
        print("Error Message:")
        print(str(e))
    finally:
        temp_path.unlink(missing_ok=True)

    print()
    print()

    # Example 2: Valid schema with unique fields
    print("Example 2: Valid schema with unique field names")
    print("-" * 70)

    yaml_valid = """
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      first_name:
        type: string
      last_name:
        type: string
      email:
        type: string
"""

    print("YAML Content:")
    print(yaml_valid)

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_valid)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()
        print("Parsing schema...")
        schema = parser.parse(temp_path)
        print("✓ Schema parsed successfully!")
        print()
        print(f"Models: {list(schema.models.keys())}")
        print(f"User fields: {list(schema.models['User'].fields.keys())}")
    except YAMLParseError as e:
        print(f"✗ Unexpected error: {e}")
    finally:
        temp_path.unlink(missing_ok=True)

    print()
    print()

    # Example 3: Multiple models can have fields with the same name
    print("Example 3: Different models can have fields with the same name")
    print("-" * 70)

    yaml_multiple_models = """
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
"""

    print("YAML Content:")
    print(yaml_multiple_models)

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_multiple_models)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()
        print("Parsing schema...")
        schema = parser.parse(temp_path)
        print("✓ Schema parsed successfully!")
        print()
        print(f"Models: {list(schema.models.keys())}")
        print(f"User fields: {list(schema.models['User'].fields.keys())}")
        print(f"Product fields: {list(schema.models['Product'].fields.keys())}")
        print()
        print("Note: Both User and Product have a 'name' field - this is valid")
        print("      because they are in different models.")
    except YAMLParseError as e:
        print(f"✗ Unexpected error: {e}")
    finally:
        temp_path.unlink(missing_ok=True)

    print()
    print()

    # Example 4: Duplicate field with different types
    print("Example 4: Duplicate field 'price' with different types")
    print("-" * 70)

    yaml_type_mismatch = """
schnitzel: "1.0"
models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
      price:
        type: int
"""

    print("YAML Content:")
    print(yaml_type_mismatch)

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_type_mismatch)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()
        print("Parsing schema...")
        schema = parser.parse(temp_path)
        print("✗ Unexpected: Schema parsed successfully (should have failed)")
    except YAMLParseError as e:
        print("✓ Duplicate field detected!")
        print()
        print("Error Message:")
        print(str(e))
    finally:
        temp_path.unlink(missing_ok=True)

    print()
    print("=" * 70)
    print("F077 Demo Complete")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("1. Duplicate field names within a model are detected and reported")
    print("2. Clear error messages help users identify the issue")
    print("3. Different models can have fields with the same name")
    print("4. Detection happens at YAML parsing time, not validation time")


if __name__ == "__main__":
    demo_duplicate_field_detection()
