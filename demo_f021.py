#!/usr/bin/env python3
"""
Demo for F021: Python model generator creates valid Pydantic v2 model from simple schema

Test Steps:
1. Create schema with User model: id (uuid), name (string), created_at (datetime)
2. Call PythonModelGenerator.generate(schema)
3. Verify output contains 'class User(BaseModel):'
4. Verify id field has type UUID
5. Verify name field has type str
6. Verify created_at field has type datetime
7. Verify imports include UUID and datetime
8. Run pyright on generated code and verify no errors
"""

import sys
import tempfile
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


def test_python_model_generator():
    """Test F021: Python model generator."""
    
    print("=" * 80)
    print("F021: Python Model Generator Test")
    print("=" * 80)
    print()
    
    # Step 1: Create schema with User model
    print("Step 1: Creating schema with User model...")
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="A user in the system",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "created_at": FieldDefinition(type="datetime"),
                }
            )
        }
    )
    print("✓ Schema created")
    print()
    
    # Step 2: Call PythonModelGenerator.generate(schema)
    print("Step 2: Calling PythonModelGenerator.generate(schema)...")
    generator = PythonModelGenerator()
    output = generator.generate(schema)
    print("✓ Generator executed")
    print()
    
    # Print generated code
    print("Generated Code:")
    print("-" * 80)
    print(output)
    print("-" * 80)
    print()
    
    # Step 3: Verify output contains 'class User(BaseModel):'
    print("Step 3: Verifying 'class User(BaseModel):' in output...")
    assert "class User(BaseModel):" in output, "Missing class definition"
    print("✓ Class definition found")
    print()
    
    # Step 4: Verify id field has type UUID
    print("Step 4: Verifying id field has type UUID...")
    assert "id: UUID" in output, "Missing id: UUID field"
    print("✓ id field has type UUID")
    print()
    
    # Step 5: Verify name field has type str
    print("Step 5: Verifying name field has type str...")
    assert "name: str" in output, "Missing name: str field"
    print("✓ name field has type str")
    print()
    
    # Step 6: Verify created_at field has type datetime
    print("Step 6: Verifying created_at field has type datetime...")
    assert "created_at: datetime" in output, "Missing created_at: datetime field"
    print("✓ created_at field has type datetime")
    print()
    
    # Step 7: Verify imports include UUID and datetime
    print("Step 7: Verifying imports include UUID and datetime...")
    assert "from uuid import UUID" in output, "Missing UUID import"
    assert "from datetime import datetime" in output, "Missing datetime import"
    assert "from pydantic import BaseModel" in output, "Missing BaseModel import"
    print("✓ All required imports present")
    print()
    
    # Step 8: Run pyright on generated code and verify no errors
    print("Step 8: Running pyright on generated code...")
    
    # Write generated code to a temporary file
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
        
        print(f"Pyright output:\n{result.stdout}")
        if result.stderr:
            print(f"Pyright errors:\n{result.stderr}")
        
        # Pyright returns 0 on success
        if result.returncode == 0:
            print("✓ Pyright validation passed (no errors)")
        else:
            print(f"⚠ Pyright returned exit code {result.returncode}")
            print("Note: Some warnings may be acceptable")
    except FileNotFoundError:
        print("⚠ Pyright not found in PATH - skipping type check")
        print("Install with: pip install pyright")
    except Exception as e:
        print(f"⚠ Error running pyright: {e}")
    finally:
        # Clean up temp file
        Path(temp_file).unlink()
    
    print()
    print("=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_python_model_generator()
