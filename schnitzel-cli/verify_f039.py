#!/usr/bin/env python3
"""Verification script for F039: Dart Analyze Compliance

Quick verification that the Dart model generator produces valid code.
"""

import sys
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


def verify_syntax_balance(code: str) -> bool:
    """Verify all braces and parentheses are balanced."""
    return (
        code.count('{') == code.count('}') and
        code.count('(') == code.count(')')
    )


def verify_imports(code: str) -> bool:
    """Verify imports are properly formatted."""
    imports = [l for l in code.split('\n') if l.startswith('import')]
    return all(
        imp.endswith(';') and "'" in imp
        for imp in imports
    )


def verify_annotations(code: str) -> bool:
    """Verify annotations are present and formatted correctly."""
    return (
        '@freezed' in code and
        "import 'package:freezed_annotation/freezed_annotation.dart';" in code and
        "import 'package:json_annotation/json_annotation.dart';" in code
    )


def verify_factories(code: str) -> bool:
    """Verify factory constructors are properly formatted."""
    return (
        'const factory' in code and
        '=>' in code  # Fat arrow for fromJson
    )


def main():
    print("F039: Dart Analyze Compliance - Verification Script")
    print("=" * 60)

    # Create test schema
    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "id": FieldDefinition(type="string"),
                    "userName": FieldDefinition(type="string"),
                    "count": FieldDefinition(type="int", default=0),
                    "isActive": FieldDefinition(type="bool", default=True),
                }
            )
        }
    )

    # Generate code
    generator = DartModelGenerator()
    code = generator.generate(schema)

    # Run checks
    checks = [
        ("Syntax Balance", verify_syntax_balance(code)),
        ("Import Statements", verify_imports(code)),
        ("Annotations", verify_annotations(code)),
        ("Factory Constructors", verify_factories(code)),
    ]

    # Display results
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("✅ All verification checks passed!")
        print("\nGenerated code sample:")
        print("-" * 60)
        print(code[:500] + "..." if len(code) > 500 else code)
        print("-" * 60)
        return 0
    else:
        print("❌ Some verification checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
