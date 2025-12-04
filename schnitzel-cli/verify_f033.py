#!/usr/bin/env python
"""Verification script for F033: Dart Freezed optional/nullable fields.

This script demonstrates the DartModelGenerator handling optional fields correctly.
"""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


def main():
    print("=" * 80)
    print("F033 Feature Verification: Dart Freezed Optional/Nullable Fields")
    print("=" * 80)
    print()

    # Create a sample schema with mixed required and optional fields
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    # Required fields
                    "id": FieldDefinition(type="string", optional=False),
                    "name": FieldDefinition(type="string", optional=False),
                    
                    # Optional fields
                    "bio": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                }
            )
        }
    )

    # Generate Dart code
    generator = DartModelGenerator()
    generated_code = generator.generate(schema)

    print("Generated Dart Freezed Model:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)
    print()

    # Verify key features
    print("Feature Verification:")
    print()
    
    checks = [
        ("required String id," in generated_code, 
         "✓ Required field 'id' has 'required' keyword"),
        ("required String name," in generated_code,
         "✓ Required field 'name' has 'required' keyword"),
        ("String? bio," in generated_code,
         "✓ Optional field 'bio' has nullable type (String?)"),
        ("int? age," in generated_code,
         "✓ Optional field 'age' has nullable type (int?)"),
        ("@freezed" in generated_code,
         "✓ Uses @freezed annotation"),
        ("part 'models.freezed.dart';" in generated_code,
         "✓ Has freezed part directive"),
        ("fromJson" in generated_code,
         "✓ Has JSON serialization support"),
    ]

    all_passed = True
    for check, message in checks:
        if check:
            print(f"  {message}")
        else:
            print(f"  ✗ {message.replace('✓', '')}")
            all_passed = False

    print()
    print("=" * 80)
    if all_passed:
        print("✓ All F033 features verified successfully!")
    else:
        print("✗ Some features failed verification")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
