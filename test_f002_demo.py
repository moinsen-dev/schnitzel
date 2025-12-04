#!/usr/bin/env python3
"""
Demo script for F002: Schema parser raises clear error for invalid YAML syntax

This script demonstrates the error handling capabilities of the SchemaParser
when encountering invalid YAML syntax.
"""

import sys
from pathlib import Path
import tempfile

# Add the schnitzel package to the path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema import SchemaParser, YAMLParseError


def test_case_1_unclosed_bracket():
    """Test Case 1: Unclosed bracket in YAML."""
    print("\n" + "="*70)
    print("TEST CASE 1: Unclosed Bracket")
    print("="*70)

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
        temp_path = f.name

    try:
        parser = SchemaParser()
        print(f"\nParsing file: {temp_path}")
        print("\nYAML Content:")
        print("-" * 70)
        print(yaml_content)
        print("-" * 70)

        parser.parse(temp_path)
        print("\n[FAIL] Parser should have raised YAMLParseError!")
        return False

    except YAMLParseError as e:
        print("\n[SUCCESS] YAMLParseError raised as expected!")
        print("\nError Details:")
        print(f"  - Line: {e.line}")
        print(f"  - Column: {e.column}")
        print(f"  - Filename: {e.filename}")
        if e.line_content:
            print(f"  - Line Content: '{e.line_content}'")

        print("\nFull Error Message:")
        print("-" * 70)
        print(str(e))
        print("-" * 70)
        return True

    finally:
        Path(temp_path).unlink()


def test_case_2_invalid_indentation():
    """Test Case 2: Invalid indentation with tabs."""
    print("\n" + "="*70)
    print("TEST CASE 2: Mixed Tabs and Spaces (Invalid YAML)")
    print("="*70)

    # YAML doesn't allow tabs for indentation in certain contexts
    yaml_content = """project_name: test_project
version: 1.0.0
models:
\tUser:
    fields:
      id: {type: uuid}
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        parser = SchemaParser()
        print(f"\nParsing file: {temp_path}")
        print("\nYAML Content:")
        print("-" * 70)
        print(yaml_content)
        print("-" * 70)

        parser.parse(temp_path)
        print("\n[FAIL] Parser should have raised YAMLParseError!")
        return False

    except YAMLParseError as e:
        print("\n[SUCCESS] YAMLParseError raised as expected!")
        print("\nError Details:")
        print(f"  - Line: {e.line}")
        print(f"  - Column: {e.column}")
        print(f"  - Filename: {e.filename}")
        if e.line_content:
            print(f"  - Line Content: '{e.line_content}'")

        print("\nFull Error Message:")
        print("-" * 70)
        print(str(e))
        print("-" * 70)
        return True

    finally:
        Path(temp_path).unlink()


def test_case_3_parser_no_crash():
    """Test Case 3: Parser doesn't crash on various invalid inputs."""
    print("\n" + "="*70)
    print("TEST CASE 3: Parser Handles Multiple Errors Gracefully")
    print("="*70)

    test_cases = [
        ("Unclosed brace", "models: { User: fields:"),
        ("Tab mixing", "models:\n\t  User: test"),
        ("Missing colon", "models\n  User fields"),
    ]

    all_handled = True

    for name, yaml_content in test_cases:
        print(f"\n  Testing: {name}")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            parser = SchemaParser()
            parser.parse(temp_path)
            print(f"    [FAIL] Should have raised YAMLParseError")
            all_handled = False

        except YAMLParseError as e:
            print(f"    [SUCCESS] Handled gracefully - Line {e.line}")

        except Exception as e:
            print(f"    [FAIL] Unexpected error: {type(e).__name__}")
            all_handled = False

        finally:
            Path(temp_path).unlink()

    return all_handled


def test_case_4_error_message_format():
    """Test Case 4: Error message follows required format."""
    print("\n" + "="*70)
    print("TEST CASE 4: Error Message Format Validation")
    print("="*70)

    yaml_content = """project_name: test
version: 1.0.0
models:
  User
    fields:
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        parser = SchemaParser()
        parser.parse(temp_path)
        print("\n[FAIL] Parser should have raised YAMLParseError!")
        return False

    except YAMLParseError as e:
        error_str = str(e)
        print("\nError Message:")
        print("-" * 70)
        print(error_str)
        print("-" * 70)

        checks = {
            "Contains 'Invalid YAML syntax'": "Invalid YAML syntax" in error_str,
            "Contains 'line' reference": "line" in error_str.lower(),
            "Contains 'Reason:'": "Reason:" in error_str,
            "Is human-readable": len(error_str) > 20,
            "Has line number": e.line is not None,
            "Has column number": e.column is not None,
        }

        print("\nFormat Checks:")
        all_passed = True
        for check, result in checks.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {check}")
            if not result:
                all_passed = False

        return all_passed

    finally:
        Path(temp_path).unlink()


def main():
    """Run all test cases."""
    print("\n" + "="*70)
    print("F002 FEATURE VERIFICATION")
    print("Schema parser raises clear error for invalid YAML syntax")
    print("="*70)

    results = []

    results.append(("Unclosed Bracket", test_case_1_unclosed_bracket()))
    results.append(("Invalid Indentation", test_case_2_invalid_indentation()))
    results.append(("No Crash on Errors", test_case_3_parser_no_crash()))
    results.append(("Error Message Format", test_case_4_error_message_format()))

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n✓ All tests passed! F002 is working correctly.\n")
        return 0
    else:
        print("\n✗ Some tests failed. Review the output above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
