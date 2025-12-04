#!/usr/bin/env python3
"""
Verification script for F011: Schema validator verifies belongsTo relationship target exists

This script executes the exact test steps from the feature requirements to verify
the implementation is correct.
"""

import sys
from pathlib import Path

# Add schnitzel-cli to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema import SchemaValidator
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation


def verify_f011():
    """Execute all test steps from F011 requirements."""
    print("=" * 70)
    print("F011 VERIFICATION: Relationship Target Validation")
    print("=" * 70)
    print()

    # Step 1: Create schema with Post model having belongsTo: author pointing to User
    print("Step 1: Create schema with Post model having belongsTo: author -> User")

    # Step 2: Create schema WITHOUT User model
    print("Step 2: Create schema WITHOUT User model")

    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="author_id"
                    )
                }
            )
        }
    )

    print("  ✓ Schema created with Post model")
    print("  ✓ Post has belongsTo relationship 'author' -> 'User'")
    print("  ✓ User model does NOT exist in schema")
    print()

    # Step 3: Call SchemaValidator.validate(schema)
    print("Step 3: Call SchemaValidator.validate(schema)")
    validator = SchemaValidator()
    result = validator.validate(schema)
    print("  ✓ Validator called successfully")
    print()

    # Step 4: Verify validation fails
    print("Step 4: Verify validation fails")
    assert result.valid is False, "FAILED: Validation should fail"
    print("  ✓ Validation failed as expected")
    print()

    # Step 5: Verify error indicates User model doesn't exist
    print("Step 5: Verify error indicates User model doesn't exist")
    error_message = "\n".join(result.errors)
    assert "User" in error_message, "FAILED: Error should mention 'User'"
    assert "not exist" in error_message.lower() or "does not exist" in error_message.lower(), \
        "FAILED: Error should indicate model doesn't exist"
    print("  ✓ Error indicates User model doesn't exist")
    print()

    # Step 6: Verify error shows the relationship definition
    print("Step 6: Verify error shows the relationship definition")
    assert "author" in error_message, "FAILED: Error should mention relationship 'author'"
    assert "belongsTo" in error_message, "FAILED: Error should show relationship type"
    print("  ✓ Error shows relationship definition")
    print()

    # Step 7: Verify error includes both model names (Post and User)
    print("Step 7: Verify error includes both model names (Post and User)")
    assert "Post" in error_message, "FAILED: Error should mention model 'Post'"
    assert "User" in error_message, "FAILED: Error should mention model 'User'"
    print("  ✓ Error includes both model names")
    print()

    # Print the actual error for inspection
    print("=" * 70)
    print("ACTUAL ERROR MESSAGE:")
    print("=" * 70)
    print(error_message)
    print("=" * 70)
    print()

    # Final verification
    print("=" * 70)
    print("VERIFICATION RESULT: ALL STEPS PASSED ✓")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Created schema with missing relationship target")
    print("  - Validator detected the error")
    print("  - Error message is clear and helpful")
    print("  - All 7 test steps verified successfully")
    print()


if __name__ == "__main__":
    try:
        verify_f011()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ VERIFICATION FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
