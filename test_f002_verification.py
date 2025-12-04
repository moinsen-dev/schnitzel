#!/usr/bin/env python3
"""
Direct verification of F002 test steps.

F002: Schema parser raises clear error for invalid YAML syntax

Test Steps from F002:
1. Create a YAML file with invalid syntax (unclosed brackets, invalid indentation)
2. Call SchemaParser.parse(filepath)
3. Verify YAMLParseError is raised
4. Verify error message includes line number and description
5. Verify error message is human-readable
6. Verify parser doesn't crash
"""

import sys
import tempfile
from pathlib import Path

# Add the schnitzel package to the path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema import SchemaParser, YAMLParseError


def verify_f002():
    """Verify all F002 test steps."""
    print("="*80)
    print("F002 VERIFICATION: Schema parser raises clear error for invalid YAML syntax")
    print("="*80)

    # Step 1: Create a YAML file with invalid syntax
    print("\n[STEP 1] Create a YAML file with invalid syntax (unclosed brackets)")
    yaml_content = """project_name: test_project
version: 1.0.0
models:
  User:
    fields:
      id: {type: uuid
      name: {type: string}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    print(f"  ✓ Created test file: {temp_path}")
    print(f"\n  File content:")
    for i, line in enumerate(yaml_content.split('\n'), 1):
        print(f"    {i:2}: {line}")

    try:
        # Step 2: Call SchemaParser.parse(filepath)
        print("\n[STEP 2] Call SchemaParser.parse(filepath)")
        parser = SchemaParser()
        print(f"  ✓ Created SchemaParser instance")
        print(f"  → Calling parser.parse('{temp_path}')")

        schema = parser.parse(temp_path)

        # If we get here, the parser didn't raise an error
        print("\n  ✗ FAIL: Parser did not raise YAMLParseError")
        return False

    except YAMLParseError as e:
        # Step 3: Verify YAMLParseError is raised
        print(f"  ✓ YAMLParseError raised as expected")

        # Step 4: Verify error message includes line number and description
        print("\n[STEP 3] Verify YAMLParseError is raised")
        print(f"  ✓ Exception type: {type(e).__name__}")

        print("\n[STEP 4] Verify error message includes line number and description")
        print(f"  - Has line number: {e.line is not None}")
        print(f"    → Line: {e.line}")
        print(f"  - Has column number: {e.column is not None}")
        print(f"    → Column: {e.column}")
        print(f"  - Has filename: {e.filename is not None}")
        print(f"    → Filename: {e.filename}")
        print(f"  - Has line content: {e.line_content is not None}")
        if e.line_content:
            print(f"    → Line content: '{e.line_content}'")

        if e.line is None:
            print("  ✗ FAIL: Error does not include line number")
            return False
        print("  ✓ Error includes line number")

        # Step 5: Verify error message is human-readable
        print("\n[STEP 5] Verify error message is human-readable")
        error_str = str(e)
        print(f"\n  Full error message:")
        print("  " + "-"*76)
        for line in error_str.split('\n'):
            print(f"  {line}")
        print("  " + "-"*76)

        checks = {
            "Contains 'Invalid YAML syntax'": "Invalid YAML syntax" in error_str,
            "Contains 'line' reference": "line" in error_str.lower(),
            "Contains 'Reason:'": "Reason:" in error_str,
            "Message length > 20 chars": len(error_str) > 20,
            "Not just a stack trace": "Traceback" not in error_str,
        }

        all_checks_pass = True
        print("\n  Human-readable checks:")
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"    {status} {check}")
            if not passed:
                all_checks_pass = False

        if not all_checks_pass:
            print("  ✗ FAIL: Error message is not human-readable")
            return False
        print("  ✓ Error message is human-readable")

        # Step 6: Verify parser doesn't crash
        print("\n[STEP 6] Verify parser doesn't crash")
        print("  ✓ Parser handled error gracefully (no crash)")
        print("  ✓ Exception was properly raised and caught")
        print("  ✓ Error details are accessible")

        return True

    except Exception as e:
        print(f"\n  ✗ FAIL: Unexpected exception type: {type(e).__name__}")
        print(f"  Error: {e}")
        return False

    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()


def verify_f002_invalid_indentation():
    """Verify F002 with invalid indentation."""
    print("\n\n" + "="*80)
    print("F002 VERIFICATION (Variant): Invalid Indentation")
    print("="*80)

    # Step 1: Create a YAML file with invalid indentation (tabs)
    print("\n[STEP 1] Create a YAML file with invalid indentation (mixed tabs)")
    yaml_content = """project_name: test_project
version: 1.0.0
models:
\tUser:
    fields:
      id: {type: uuid}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    print(f"  ✓ Created test file: {temp_path}")

    try:
        # Step 2: Call SchemaParser.parse(filepath)
        print("\n[STEP 2] Call SchemaParser.parse(filepath)")
        parser = SchemaParser()
        parser.parse(temp_path)

        print("\n  ✗ FAIL: Parser did not raise YAMLParseError")
        return False

    except YAMLParseError as e:
        print(f"  ✓ YAMLParseError raised")
        print(f"  ✓ Line: {e.line}, Column: {e.column}")
        print(f"  ✓ Error: {str(e).split(chr(10))[0]}")
        return True

    except Exception as e:
        print(f"\n  ✗ FAIL: Unexpected exception: {type(e).__name__}: {e}")
        return False

    finally:
        if temp_path.exists():
            temp_path.unlink()


def main():
    """Run F002 verification."""
    print("\n")

    result1 = verify_f002()
    result2 = verify_f002_invalid_indentation()

    print("\n" + "="*80)
    print("FINAL RESULT")
    print("="*80)

    if result1 and result2:
        print("\n✓✓✓ F002 VERIFICATION PASSED ✓✓✓")
        print("\nAll test steps completed successfully:")
        print("  ✓ Step 1: YAML file with invalid syntax created")
        print("  ✓ Step 2: SchemaParser.parse(filepath) called")
        print("  ✓ Step 3: YAMLParseError raised")
        print("  ✓ Step 4: Error message includes line number and description")
        print("  ✓ Step 5: Error message is human-readable")
        print("  ✓ Step 6: Parser doesn't crash")
        print("\n" + "="*80 + "\n")
        return 0
    else:
        print("\n✗✗✗ F002 VERIFICATION FAILED ✗✗✗")
        print("\nSome test steps did not pass. Review the output above.")
        print("\n" + "="*80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
