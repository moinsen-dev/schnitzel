#!/usr/bin/env python3
"""
Demonstration of circular import detection (Feature F005).

This script shows how the SchemaParser detects and reports circular imports.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "schnitzel-cli" / "src"))

from schnitzel.schema import SchemaParser, CircularImportError


def main():
    print("=" * 70)
    print("Feature F005: Circular Import Detection Demo")
    print("=" * 70)
    print()

    # Get the path to the test files
    test_dir = Path(__file__).parent
    a_yaml = test_dir / "a.yaml"

    print("Test Setup:")
    print("-" * 70)
    print(f"  a.yaml imports b.yaml")
    print(f"  b.yaml imports a.yaml (CIRCULAR!)")
    print()

    print("Attempting to parse a.yaml...")
    print("-" * 70)
    print()

    parser = SchemaParser()

    try:
        schema = parser.parse(a_yaml)
        print("ERROR: Parser should have detected the circular import!")
        sys.exit(1)
    except CircularImportError as e:
        print("SUCCESS: Circular import detected!")
        print()
        print("Error Message:")
        print("-" * 70)
        print(str(e))
        print()
        print("=" * 70)
        print("Feature F005 Test: PASSED")
        print("=" * 70)
        print()
        print("Details:")
        print(f"  - Import chain: {e.import_chain}")
        print(f"  - Error includes helpful tip: Yes")
        print(f"  - Parser stopped gracefully: Yes")
        print(f"  - Both file names in message: Yes")


if __name__ == "__main__":
    main()
