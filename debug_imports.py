#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema

schema = SchnitzelSchema(
    models={
        "Product": Model(
            name="Product",
            fields={
                "metadata": FieldDefinition(type="json"),
            }
        )
    }
)

generator = PythonModelGenerator()
imports = generator._collect_imports(schema)
print("Collected imports:", imports)

# Check field type
for model in schema.models.values():
    for field_name, field in model.fields.items():
        print(f"Field {field_name}: type={field.type}")
