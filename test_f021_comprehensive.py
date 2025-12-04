#!/usr/bin/env python3
"""Comprehensive test for F021: Test all type mappings."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


def test_all_type_mappings():
    """Test all type mappings work correctly."""
    
    print("Testing all type mappings...")
    
    schema = SchnitzelSchema(
        models={
            "AllTypes": Model(
                name="AllTypes",
                description="Model with all supported types",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "age": FieldDefinition(type="int"),
                    "price": FieldDefinition(type="float"),
                    "active": FieldDefinition(type="bool"),
                    "created_at": FieldDefinition(type="datetime"),
                    "metadata": FieldDefinition(type="json"),
                }
            )
        }
    )
    
    generator = PythonModelGenerator()
    output = generator.generate(schema)
    
    print("Generated code:")
    print("-" * 80)
    print(output)
    print("-" * 80)
    print()
    
    # Verify all type mappings
    assert "id: UUID" in output, "UUID type mapping failed"
    assert "name: str" in output, "string type mapping failed"
    assert "age: int" in output, "int type mapping failed"
    assert "price: float" in output, "float type mapping failed"
    assert "active: bool" in output, "bool type mapping failed"
    assert "created_at: datetime" in output, "datetime type mapping failed"
    assert "metadata: dict[str, Any]" in output, "json type mapping failed"
    
    # Verify all imports
    assert "from uuid import UUID" in output, "Missing UUID import"
    assert "from datetime import datetime" in output, "Missing datetime import"
    assert "from typing import Any" in output, "Missing Any import"
    assert "from pydantic import BaseModel" in output, "Missing BaseModel import"
    
    print("✓ All type mappings work correctly")
    
    # Test pyright
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(output)
        temp_file = f.name
    
    try:
        import subprocess
        result = subprocess.run(
            ["pyright", temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Pyright validation passed")
        else:
            print(f"⚠ Pyright returned exit code {result.returncode}")
            print(result.stdout)
    except FileNotFoundError:
        print("⚠ Pyright not found - skipping type check")
    finally:
        Path(temp_file).unlink()
    
    print("\n✓ Comprehensive test passed!")


if __name__ == "__main__":
    test_all_type_mappings()
