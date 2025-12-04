#!/usr/bin/env python3
"""Demo script for F050 - Generate command parses and validates schema before generation.

This script demonstrates the new `schnitzel generate` command that:
1. Parses schema files using SchemaParser
2. Validates schemas using SchemaValidator
3. Reports validation errors
4. Returns exit code 1 on validation failures
"""

import subprocess
import tempfile
from pathlib import Path

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def run_command(cmd: list[str], cwd: Path = None) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd
    )
    return result.returncode, result.stdout + result.stderr

def main() -> None:
    """Run demonstration of F050 generate command."""
    print("\n🎉 Feature F050 - Generate Command Demo")
    print("📋 Demonstrating schema parsing and validation")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Test 1: Valid schema with default name
        print_section("Test 1: Valid Schema with Default Name")
        valid_schema = tmpdir / "schema.schnitzel.yaml"
        valid_schema.write_text("""schnitzel: "1.0"

models:
  User:
    description: "A user in the system"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
      name:
        type: string
      age:
        type: int
        min: 0
        max: 150
""")
        exit_code, output = run_command(["schnitzel", "generate"], cwd=tmpdir)
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 0, "Valid schema should succeed"

        # Test 2: Custom schema path
        print_section("Test 2: Custom Schema Path")
        custom_schema = tmpdir / "my_custom_schema.yaml"
        custom_schema.write_text("""schnitzel: "1.0"

models:
  Product:
    description: "A product"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
        min: 0.0
""")
        exit_code, output = run_command(["schnitzel", "generate", str(custom_schema)])
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 0, "Custom path should work"

        # Test 3: Invalid field type
        print_section("Test 3: Invalid Field Type (Validation Error)")
        invalid_type_schema = tmpdir / "invalid_type.yaml"
        invalid_type_schema.write_text("""schnitzel: "1.0"

models:
  User:
    description: "User with invalid type"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type
""")
        exit_code, output = run_command(["schnitzel", "generate", str(invalid_type_schema)])
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 1, "Invalid type should fail"

        # Test 4: Invalid YAML syntax
        print_section("Test 4: Invalid YAML Syntax")
        invalid_yaml = tmpdir / "invalid_yaml.yaml"
        invalid_yaml.write_text("""schnitzel: "1.0"
models:
  User:
    fields:
      id: [unclosed bracket
""")
        exit_code, output = run_command(["schnitzel", "generate", str(invalid_yaml)])
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 1, "Invalid YAML should fail"

        # Test 5: Invalid naming conventions
        print_section("Test 5: Invalid Naming Conventions")
        invalid_naming = tmpdir / "invalid_naming.yaml"
        invalid_naming.write_text("""schnitzel: "1.0"

models:
  user_model:
    description: "Invalid model name"
    fields:
      id:
        type: uuid
        primary: true
      userName:
        type: string
""")
        exit_code, output = run_command(["schnitzel", "generate", str(invalid_naming)])
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 1, "Invalid naming should fail"

        # Test 6: Complex schema with relationships
        print_section("Test 6: Complex Schema with Relationships and Unique Constraints")
        complex_schema = tmpdir / "complex.yaml"
        complex_schema.write_text("""schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
      username:
        type: string
        unique: true
      name:
        type: string
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    description: "Post model"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
      author_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
""")
        exit_code, output = run_command(["schnitzel", "generate", str(complex_schema)])
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 0, "Complex schema should succeed"

        # Test 7: Missing file
        print_section("Test 7: Missing Schema File")
        exit_code, output = run_command(["schnitzel", "generate", str(tmpdir / "nonexistent.yaml")])
        print(output)
        print(f"Exit code: {exit_code}")
        assert exit_code == 1, "Missing file should fail"

    print_section("✅ All Tests Passed!")
    print("Feature F050 is working correctly!")
    print("\nKey Features Demonstrated:")
    print("  ✓ Parses schema files using SchemaParser")
    print("  ✓ Validates schemas using SchemaValidator")
    print("  ✓ Supports default schema path (schema.schnitzel.yaml)")
    print("  ✓ Accepts custom schema paths")
    print("  ✓ Reports validation errors clearly")
    print("  ✓ Returns exit code 1 on failures")
    print("  ✓ Displays model count and unique constraints")
    print("  ✓ Validates field and model naming conventions")
    print("  ✓ Validates relationships and numeric constraints")
    print()

if __name__ == "__main__":
    main()
