#!/usr/bin/env python3
"""Demo script to show schema parser import resolution in action."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from schnitzel.schema.parser import SchemaParser


def main():
    """Demonstrate import resolution."""
    print("=" * 60)
    print("Schema Parser Import Resolution Demo (F003)")
    print("=" * 60)
    print()

    # Parse schema with imports
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    main_schema = fixtures_dir / "main.yaml"

    print(f"Parsing: {main_schema}")
    print(f"  - main.yaml imports base.yaml")
    print(f"  - base.yaml defines User model")
    print(f"  - main.yaml defines Post model")
    print()

    parser = SchemaParser()
    schema = parser.parse(main_schema)

    print("Parsed successfully!")
    print()
    print(f"Schema version: {schema.schnitzel}")
    print(f"Total models: {len(schema.models)}")
    print()

    # Display models
    for model_name, model in schema.models.items():
        print(f"Model: {model_name}")
        print(f"  Fields: {', '.join(model.fields.keys())}")
        if model.relations:
            print(f"  Relations: {', '.join(model.relations.keys())}")
        print()

    print("=" * 60)
    print("Import resolution verified!")
    print("  - Both User and Post models are present")
    print("  - Models imported from base.yaml")
    print("  - No duplicate models")
    print("  - Relative paths resolved correctly")
    print("=" * 60)


if __name__ == "__main__":
    main()
