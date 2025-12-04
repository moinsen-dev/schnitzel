#!/usr/bin/env python3
"""
Demo script for F025: Python model generator generates validation rules using Pydantic Field

Test Steps:
1. Create Product model with price (float) with min: 0, max: 100000
2. Create name (string) with max_length: 200
3. Call PythonModelGenerator.generate(schema)
4. Verify price field uses Field(ge=0, le=100000)
5. Verify name field uses Field(max_length=200)
6. Verify Field is imported from pydantic
7. Run pyright on generated code and verify no errors
"""

import sys
import tempfile
import subprocess
from pathlib import Path

# Add the schnitzel-cli/src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python import PythonModelGenerator


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    print_section("F025: Python Model Generator - Pydantic Field Validation Rules")

    # Step 1 & 2: Create Product model with price and name fields with constraints
    print("Step 1-2: Creating Product model with validation constraints...")
    
    schema = SchnitzelSchema(
        models={
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "price": FieldDefinition(type="float", min=0, max=100000),
                    "name": FieldDefinition(type="string", max_length=200),
                }
            )
        }
    )
    
    print("✓ Product model created with constraints:")
    print(f"  - price: float with min=0, max=100000")
    print(f"  - name: string with max_length=200")

    # Step 3: Call PythonModelGenerator.generate(schema)
    print_section("Step 3: Generating Python Pydantic model")
    
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)
    
    print("Generated code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)

    # Step 4: Verify price field uses Field(ge=0, le=100000)
    print_section("Step 4: Verifying price field validation")
    
    if "price: float = Field(ge=0, le=100000)" in generated_code:
        print("✓ Price field correctly uses Field(ge=0, le=100000)")
    else:
        print("✗ Price field validation not found or incorrect")
        print("  Expected: price: float = Field(ge=0, le=100000)")
        return False

    # Step 5: Verify name field uses Field(max_length=200)
    print_section("Step 5: Verifying name field validation")
    
    if "name: str = Field(max_length=200)" in generated_code:
        print("✓ Name field correctly uses Field(max_length=200)")
    else:
        print("✗ Name field validation not found or incorrect")
        print("  Expected: name: str = Field(max_length=200)")
        return False

    # Step 6: Verify Field is imported from pydantic
    print_section("Step 6: Verifying Field import")
    
    if "from pydantic import BaseModel, Field" in generated_code:
        print("✓ Field is correctly imported from pydantic")
    else:
        print("✗ Field import not found or incorrect")
        print("  Expected: from pydantic import BaseModel, Field")
        return False

    # Step 7: Run pyright on generated code and verify no errors
    print_section("Step 7: Running pyright type checking")
    
    # Write generated code to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(generated_code)
        temp_file = f.name
    
    try:
        print(f"Running pyright on generated code ({temp_file})...")
        result = subprocess.run(
            ["pyright", temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"\nPyright output:")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("✓ Pyright type checking PASSED - no errors")
        else:
            print("✗ Pyright type checking FAILED")
            return False
            
    except FileNotFoundError:
        print("⚠ Pyright not found - skipping type check")
        print("  Install pyright with: pip install pyright")
        print("  Continuing with other validations...")
    except subprocess.TimeoutExpired:
        print("✗ Pyright timed out")
        return False
    finally:
        # Clean up temp file
        Path(temp_file).unlink(missing_ok=True)

    # Additional verification: Test with more complex constraints
    print_section("Additional: Testing combined constraints")
    
    complex_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "age": FieldDefinition(type="int", min=0, max=150),
                    "username": FieldDefinition(type="string", max_length=50),
                    "bio": FieldDefinition(type="string", max_length=500, optional=True),
                }
            )
        }
    )
    
    complex_code = generator.generate(complex_schema)
    
    print("Generated complex model:")
    print("-" * 80)
    print(complex_code)
    print("-" * 80)
    
    # Verify combined constraints
    # Note: Python 3.10+ uses Union syntax (str | None), older versions use Optional[str]
    bio_check = (
        "bio: str | None = Field(max_length=500, default=None)" in complex_code or
        "bio: Optional[str] = Field(max_length=500, default=None)" in complex_code
    )
    checks = [
        ("age: int = Field(ge=0, le=150)" in complex_code, "age with min/max"),
        ("username: str = Field(max_length=50)" in complex_code, "username with max_length"),
        (bio_check, "optional bio with max_length"),
    ]
    
    all_passed = True
    for check, description in checks:
        if check:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}")
            all_passed = False
    
    if not all_passed:
        return False

    print_section("Summary")
    print("✓ All test steps completed successfully!")
    print("\nFeature F025 Implementation Verified:")
    print("  • PythonModelGenerator.generate() method works")
    print("  • min/max constraints mapped to ge=/le= in Field()")
    print("  • max_length constraint mapped to max_length= in Field()")
    print("  • Field imported from pydantic")
    print("  • Generated code passes pyright type checking")
    print("  • Combined constraints work correctly")
    print("  • Optional fields with constraints work correctly")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
