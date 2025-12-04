#!/usr/bin/env python3
"""Test JSON field type handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema

# Create schema with JSON field
schema = SchnitzelSchema(
    models={
        "Product": Model(
            name="Product",
            description="A product with metadata",
            fields={
                "id": FieldDefinition(type="uuid", primary=True),
                "name": FieldDefinition(type="string"),
                "metadata": FieldDefinition(type="json"),
            }
        )
    }
)

# Generate code
generator = PythonModelGenerator()
output = generator.generate(schema)

print("Generated code:")
print(output)

# Verify json type
assert "metadata: dict[str, Any]" in output, "JSON field should be dict[str, Any]"
assert "from typing import Any" in output, "Should import Any for dict[str, Any]"

print("\n✓ JSON type handling verified")
