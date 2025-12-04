#!/usr/bin/env python3
"""
Demo script for F020: Schema validator validates format constraints for string fields

Test Steps:
1. Create User model with email field (string) with format: email
2. Create another field: phone with format: phone
3. Call SchemaValidator.validate(schema)
4. Verify validation passes
5. Verify format constraints are recognized
6. Verify supported formats are validated
"""

import sys
from pathlib import Path

# Add the schnitzel-cli/src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema import SchemaValidator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    print_section("F020: Format Validation for String Fields")

    # Step 1 & 2: Create User model with email and phone fields with format constraints
    print("Step 1-2: Creating User model with email (format: email) and phone (format: phone) fields...")

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email"),
                    "phone": FieldDefinition(type="string", format="phone"),
                }
            )
        }
    )

    print("✓ User model created with format constraints")
    print(f"  - email field: type=string, format=email")
    print(f"  - phone field: type=string, format=phone")

    # Step 3: Call SchemaValidator.validate(schema)
    print_section("Step 3: Validating schema with SchemaValidator")

    validator = SchemaValidator()
    result = validator.validate(schema)

    print(f"Validation result: {'PASSED' if result.valid else 'FAILED'}")
    if result.errors:
        print(f"Errors: {result.errors}")
    else:
        print("No validation errors")

    # Step 4: Verify validation passes
    print_section("Step 4: Verifying validation passes")

    if result.valid:
        print("✓ Validation PASSED as expected")
    else:
        print("✗ Validation FAILED unexpectedly")
        print(f"  Errors: {result.errors}")
        return False

    # Step 5: Verify format constraints are recognized
    print_section("Step 5: Verifying format constraints are recognized")

    # Test that unsupported format is rejected
    print("Testing unsupported format 'e-mail' (should be 'email')...")
    invalid_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "email": FieldDefinition(type="string", format="e-mail"),
                }
            )
        }
    )

    result_invalid = validator.validate(invalid_schema)

    if not result_invalid.valid:
        print("✓ Unsupported format correctly rejected")
        print(f"  Error message preview: {result_invalid.errors[0][:100]}...")
    else:
        print("✗ Unsupported format was NOT rejected (unexpected)")
        return False

    # Step 6: Verify supported formats are validated
    print_section("Step 6: Verifying all supported formats")

    supported_formats = [
        "email", "phone", "url", "uri", "uuid",
        "date", "time", "datetime", "ip", "ipv4", "ipv6"
    ]

    print(f"Testing {len(supported_formats)} supported formats...")

    all_passed = True
    for format_type in supported_formats:
        test_schema = SchnitzelSchema(
            models={
                "TestModel": Model(
                    name="TestModel",
                    fields={
                        "field": FieldDefinition(type="string", format=format_type),
                    }
                )
            }
        )

        test_result = validator.validate(test_schema)

        if test_result.valid:
            print(f"  ✓ {format_type:12} - VALID")
        else:
            print(f"  ✗ {format_type:12} - INVALID (unexpected)")
            all_passed = False

    if all_passed:
        print("\n✓ All supported formats validated successfully")
    else:
        print("\n✗ Some supported formats failed validation")
        return False

    # Additional test: Format on non-string field should fail
    print_section("Additional: Format constraint only on string fields")

    print("Testing format constraint on non-string field (should fail)...")
    non_string_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "age": FieldDefinition(type="int", format="email"),  # Invalid
                }
            )
        }
    )

    non_string_result = validator.validate(non_string_schema)

    if not non_string_result.valid:
        print("✓ Format on non-string field correctly rejected")
        print(f"  Error indicates: Format constraints only for string fields")
    else:
        print("✗ Format on non-string field was NOT rejected (unexpected)")
        return False

    print_section("Summary")
    print("✓ All test steps completed successfully!")
    print("\nFeature F020 Implementation Verified:")
    print("  • FieldDefinition model has 'format' field")
    print("  • 11 supported formats defined")
    print("  • Validator rejects unsupported formats with helpful errors")
    print("  • Validator enforces format constraints only on string fields")
    print("  • All supported formats are correctly validated")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
