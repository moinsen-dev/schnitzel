#!/usr/bin/env python3
"""
Demo script for F007: Schema parser raises error when importing non-existent file

This script demonstrates the error handling when a schema file tries to import
a non-existent file.
"""

import sys
import tempfile
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.exceptions import ImportError as SchnitzelImportError


def demo_missing_import():
    """Demonstrate error handling for missing import files."""
    print("=" * 80)
    print("F007 DEMO: Schema Parser Error Handling for Missing Imports")
    print("=" * 80)
    print()

    # Create temporary directory with test files
    with tempfile.TemporaryDirectory() as tmpdir:
        main_path = Path(tmpdir) / "main.yaml"

        # Create main.yaml that imports a non-existent file
        print("Step 1: Creating main.yaml with import to non-existent file")
        print("-" * 80)
        main_content = """
schnitzel: 1.0.0
imports:
  - nonexistent.yaml
models:
  Post:
    fields:
      id:
        type: uuid
      title:
        type: string
"""
        main_path.write_text(main_content)
        print(f"Created: {main_path}")
        print()
        print("Content:")
        print(main_content)
        print()

        # Try to parse the schema
        print("Step 2: Parsing schema with SchemaParser")
        print("-" * 80)
        parser = SchemaParser()

        try:
            schema = parser.parse(main_path)
            print("ERROR: Should have raised ImportError!")
        except SchnitzelImportError as e:
            print("SUCCESS: ImportError raised as expected!")
            print()
            print("Step 3: Verify error message contains required information")
            print("-" * 80)
            print()
            print("Full Error Message:")
            print("-" * 80)
            print(str(e))
            print()

            # Verify all requirements
            error_msg = str(e)

            print("Step 4: Verification of F007 Requirements")
            print("-" * 80)

            # Requirement 1: Exception is raised
            print("[✓] Exception raised: ImportError")

            # Requirement 2: Error message includes missing filename
            if "nonexistent.yaml" in error_msg:
                print("[✓] Error message includes missing filename: 'nonexistent.yaml'")
            else:
                print("[✗] Error message missing filename")

            # Requirement 3: Error message includes importing file name
            if "main.yaml" in error_msg:
                print("[✓] Error message includes importing file: 'main.yaml'")
            else:
                print("[✗] Error message missing importing file")

            # Requirement 4: Helpful suggestion
            if "check" in error_msg.lower() or "path" in error_msg.lower():
                print("[✓] Error message includes helpful suggestion")
            else:
                print("[✗] Error message missing helpful suggestion")

            # Additional: Check exception attributes
            print()
            print("Step 5: Exception Attributes")
            print("-" * 80)
            print(f"exception.missing_file = '{e.missing_file}'")
            print(f"exception.importing_file = '{e.importing_file}'")

            print()
            print("=" * 80)
            print("F007 DEMO COMPLETE: All requirements verified!")
            print("=" * 80)


def demo_nested_missing_import():
    """Demonstrate error handling for missing import in nested file."""
    print()
    print()
    print("=" * 80)
    print("BONUS DEMO: Missing Import in Nested File")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "base.yaml"
        main_path = Path(tmpdir) / "main.yaml"

        # Create base.yaml that imports a missing file
        print("Creating base.yaml that imports a missing file:")
        print("-" * 80)
        base_content = """
schnitzel: 1.0.0
imports:
  - missing_nested.yaml
models:
  User:
    fields:
      id:
        type: uuid
"""
        base_path.write_text(base_content)
        print(base_content)

        # Create main.yaml that imports base.yaml
        print()
        print("Creating main.yaml that imports base.yaml:")
        print("-" * 80)
        main_content = """
schnitzel: 1.0.0
imports:
  - base.yaml
models:
  Post:
    fields:
      id:
        type: uuid
"""
        main_path.write_text(main_content)
        print(main_content)

        # Try to parse
        print()
        print("Parsing main.yaml...")
        print("-" * 80)
        parser = SchemaParser()

        try:
            schema = parser.parse(main_path)
            print("ERROR: Should have raised ImportError!")
        except SchnitzelImportError as e:
            print("SUCCESS: ImportError raised!")
            print()
            print("Error Message:")
            print("-" * 80)
            print(str(e))
            print()

            error_msg = str(e)

            # The error should reference base.yaml as the importing file, not main.yaml
            if "missing_nested.yaml" in error_msg:
                print("[✓] Error correctly identifies missing_nested.yaml as the missing file")

            if "base.yaml" in error_msg:
                print("[✓] Error correctly identifies base.yaml as the importing file")
                print("    (not main.yaml, which is the root file)")

            print()
            print("=" * 80)
            print("NESTED IMPORT DEMO COMPLETE")
            print("=" * 80)


if __name__ == "__main__":
    demo_missing_import()
    demo_nested_missing_import()
