"""
Integration test for API versioning consistency validation.
Feature ID: 1091b6ca-2f1a-4ddb-b843-d0c7aca3bb8a

Test Steps:
1. Create schema with consistent versioning (no version prefix)
2. Validate - should pass with no warnings
3. Create schema with consistent versioning (/api/v1)
4. Validate - should pass with no warnings
5. Create schema with inconsistent versioning (mixed)
6. Validate - should pass with warnings
7. Create schema with different version numbers (/api/v1 vs /api/v2)
8. Validate - should pass with warnings
"""

from schnitzel.schema.models import Model, FieldDefinition, SchnitzelSchema
from schnitzel.schema.validator import SchemaValidator


def test_consistent_versioning_no_prefix():
    """Test that endpoints without version prefixes pass validation without warnings."""
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/users": {
                "GET": {"name": "listUsers", "response": {"200": {"type": "list<User>"}}}
            },
            "/users/{id}": {
                "GET": {"name": "getUser", "response": {"200": {"type": "User"}}}
            },
            "/orders": {
                "GET": {"name": "listOrders"}
            },
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid, f"Validation should pass. Errors: {result.errors}"

    # Should have no versioning warnings since all endpoints are consistent
    versioning_warnings = [w for w in result.warnings if "versioning" in w.lower()]
    assert len(versioning_warnings) == 0, f"Should have no versioning warnings: {versioning_warnings}"

    print("\n✓ Test passed: Consistent endpoints (no versioning) - no warnings")


def test_consistent_versioning_api_v1():
    """Test that endpoints all using /api/v1 prefix pass validation without warnings."""
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/api/v1/users": {
                "GET": {"name": "listUsers"}
            },
            "/api/v1/users/{id}": {
                "GET": {"name": "getUser"}
            },
            "/api/v1/orders": {
                "GET": {"name": "listOrders"}
            },
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid, f"Validation should pass. Errors: {result.errors}"

    # Should have no versioning warnings
    versioning_warnings = [w for w in result.warnings if "versioning" in w.lower()]
    assert len(versioning_warnings) == 0, f"Should have no versioning warnings: {versioning_warnings}"

    print("✓ Test passed: Consistent endpoints (all /api/v1) - no warnings")


def test_consistent_versioning_v2():
    """Test that endpoints all using /v2 prefix pass validation without warnings."""
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/v2/users": {
                "GET": {"name": "listUsers"}
            },
            "/v2/users/{id}": {
                "GET": {"name": "getUser"}
            },
            "/v2/orders": {
                "POST": {"name": "createOrder"}
            },
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid, f"Validation should pass. Errors: {result.errors}"

    # Should have no versioning warnings
    versioning_warnings = [w for w in result.warnings if "versioning" in w.lower()]
    assert len(versioning_warnings) == 0, f"Should have no versioning warnings: {versioning_warnings}"

    print("✓ Test passed: Consistent endpoints (all /v2) - no warnings")


def test_inconsistent_versioning_mixed():
    """Test that mixed versioning triggers a warning."""
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/api/v1/users": {
                "GET": {"name": "listUsers"}
            },
            "/v2/orders": {
                "GET": {"name": "listOrders"}
            },
            "/products": {
                "GET": {"name": "listProducts"}
            },
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid, f"Validation should pass (warnings only). Errors: {result.errors}"

    # Should have versioning warnings
    versioning_warnings = [w for w in result.warnings if "versioning" in w.lower()]
    assert len(versioning_warnings) > 0, "Should have versioning inconsistency warnings"

    # Verify warning content
    warning = versioning_warnings[0]
    assert "Inconsistent API versioning" in warning, "Warning should mention inconsistent versioning"
    assert "/api/v1" in warning, "Warning should mention /api/v1"
    assert "/v2" in warning, "Warning should mention /v2"
    assert "No version prefix" in warning, "Warning should mention no version prefix"

    print("✓ Test passed: Inconsistent endpoints (mixed versioning) - warning detected")


def test_inconsistent_versioning_different_versions():
    """Test that different version numbers trigger a warning."""
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                }
            )
        },
        endpoints={
            "/api/v1/users": {
                "GET": {"name": "listUsers"}
            },
            "/api/v1/orders": {
                "GET": {"name": "listOrders"}
            },
            "/api/v2/products": {
                "GET": {"name": "listProducts"}
            },
            "/api/v2/categories": {
                "GET": {"name": "listCategories"}
            },
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid, f"Validation should pass (warnings only). Errors: {result.errors}"

    # Should have versioning warnings
    versioning_warnings = [w for w in result.warnings if "versioning" in w.lower()]
    assert len(versioning_warnings) > 0, "Should have versioning inconsistency warnings"

    # Verify warning content
    warning = versioning_warnings[0]
    assert "Inconsistent API versioning" in warning, "Warning should mention inconsistent versioning"
    assert "/api/v1" in warning, "Warning should mention /api/v1"
    assert "/api/v2" in warning, "Warning should mention /api/v2"
    assert "2 endpoints" in warning or "endpoints)" in warning, "Warning should mention endpoint counts"

    print("✓ Test passed: Inconsistent endpoints (v1 vs v2) - warning detected")


def test_version_prefix_extraction():
    """Test that version prefix extraction works correctly."""
    from schnitzel.schema.validator import SchemaValidator

    validator = SchemaValidator()

    # Test various patterns
    assert validator._extract_version_prefix("/api/v1/users") == "/api/v1"
    assert validator._extract_version_prefix("/api/v2/orders") == "/api/v2"
    assert validator._extract_version_prefix("/v1/users") == "/v1"
    assert validator._extract_version_prefix("/v3/products") == "/v3"
    assert validator._extract_version_prefix("/users") == ""
    assert validator._extract_version_prefix("/products/{id}") == ""
    assert validator._extract_version_prefix("/api/users") == ""
    assert validator._extract_version_prefix("/API/V1/users") == "/API/V1"  # Case sensitive on 'api' but pattern matches

    print("✓ Test passed: Version prefix extraction works correctly")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("API VERSIONING CONSISTENCY VALIDATION - Integration Tests")
    print("Feature ID: 1091b6ca-2f1a-4ddb-b843-d0c7aca3bb8a")
    print("="*70 + "\n")

    try:
        test_consistent_versioning_no_prefix()
        test_consistent_versioning_api_v1()
        test_consistent_versioning_v2()
        test_inconsistent_versioning_mixed()
        test_inconsistent_versioning_different_versions()
        test_version_prefix_extraction()

        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nFeature Summary:")
        print("✓ API versioning consistency validation is working")
        print("✓ Detects inconsistent version prefixes across endpoints")
        print("✓ Supports /api/vN, /vN, and no-version patterns")
        print("✓ Warnings are displayed via validate command")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
