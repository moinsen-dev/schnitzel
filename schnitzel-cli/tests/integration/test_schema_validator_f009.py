"""
Integration test for F009: Schema validator accepts valid model with all supported field types.

Test steps:
1. Create schema with model containing: string, uuid, int, float, bool, datetime, json fields
2. Call SchemaValidator.validate(schema)
3. Verify validation passes with no errors
4. Verify all field types are recognized
5. Verify validator returns empty error list
6. Verify schema is marked as valid
"""

from pathlib import Path

from schnitzel.schema import SchemaParser, SchemaValidator, ValidationResult


def test_validate_all_supported_field_types():
    """
    Test F009: Schema validator accepts valid model with all supported field types.

    This test verifies that SchemaValidator correctly validates a schema containing
    all supported field types: string, uuid, int, float, bool, datetime, json,
    enum, vector, and list<T> types.
    """
    # Step 1: Create schema with all supported field types
    test_file = Path(__file__).parent / "fixtures" / "all_field_types_schema.yaml"
    parser = SchemaParser()
    schema = parser.parse(test_file)

    # Verify schema was parsed correctly
    assert "CompleteModel" in schema.models, "Schema should contain CompleteModel"
    model = schema.models["CompleteModel"]

    # Verify all expected fields are present
    expected_fields = {
        "id", "name", "age", "height", "is_active", "created_at",
        "metadata", "status", "embedding", "tags", "scores", "weights"
    }
    assert set(model.fields.keys()) == expected_fields, (
        f"Model should have all expected fields. "
        f"Expected: {expected_fields}, Got: {set(model.fields.keys())}"
    )

    # Step 2: Call SchemaValidator.validate(schema)
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Step 3: Verify validation passes with no errors
    assert isinstance(result, ValidationResult), "Validator should return ValidationResult"

    # Step 4: Verify all field types are recognized (no errors means they're recognized)
    # Step 5: Verify validator returns empty error list
    assert result.errors == [], (
        f"Validation should pass with no errors. Got errors: {result.errors}"
    )

    # Step 6: Verify schema is marked as valid
    assert result.valid is True, "Validation result should be marked as valid"

    print("\n✓ Test F009 passed: Schema validator accepts all supported field types")


def test_field_types_recognized():
    """
    Verify that each individual field type is recognized by the validator.
    """
    test_file = Path(__file__).parent / "fixtures" / "all_field_types_schema.yaml"
    parser = SchemaParser()
    schema = parser.parse(test_file)
    model = schema.models["CompleteModel"]

    # Verify field types
    assert model.fields["id"].type == "uuid"
    assert model.fields["name"].type == "string"
    assert model.fields["age"].type == "int"
    assert model.fields["height"].type == "float"
    assert model.fields["is_active"].type == "bool"
    assert model.fields["created_at"].type == "datetime"
    assert model.fields["metadata"].type == "json"
    assert model.fields["status"].type == "enum"
    assert model.fields["embedding"].type == "vector"
    assert model.fields["tags"].type == "list<string>"
    assert model.fields["scores"].type == "list<int>"
    assert model.fields["weights"].type == "list<float>"

    # Validate with SchemaValidator
    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True
    assert result.errors == []

    print("\n✓ All field types are recognized by validator")


def test_validator_returns_validation_result():
    """
    Verify that validator returns a ValidationResult object with the correct structure.
    """
    test_file = Path(__file__).parent / "fixtures" / "all_field_types_schema.yaml"
    parser = SchemaParser()
    schema = parser.parse(test_file)

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify result structure
    assert hasattr(result, "valid"), "ValidationResult should have 'valid' attribute"
    assert hasattr(result, "errors"), "ValidationResult should have 'errors' attribute"
    assert isinstance(result.valid, bool), "'valid' should be a boolean"
    assert isinstance(result.errors, list), "'errors' should be a list"

    print("\n✓ Validator returns correctly structured ValidationResult")


def test_unsupported_field_type_returns_error():
    """
    Verify that unsupported field types result in validation errors (not valid).
    This is a negative test to ensure the validator is actually checking types.
    """
    from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition

    # Create schema with unsupported type
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "invalid_field": FieldDefinition(type="unsupported_type")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should have validation errors
    assert result.valid is False, "Validation should fail for unsupported type"
    assert len(result.errors) > 0, "Should have at least one error"
    assert any("unsupported_type" in error.lower() for error in result.errors), (
        "Error should mention the unsupported type"
    )

    print("\n✓ Validator correctly rejects unsupported field types")


def test_list_type_with_unsupported_inner_type():
    """
    Verify that list types with unsupported inner types are rejected.
    """
    from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition

    # Create schema with unsupported list inner type
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "invalid_list": FieldDefinition(type="list<invalid_type>")
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should have validation errors
    assert result.valid is False, "Validation should fail for list with unsupported inner type"
    assert len(result.errors) > 0, "Should have at least one error"

    print("\n✓ Validator correctly rejects list types with unsupported inner types")


if __name__ == "__main__":
    # Run all tests
    test_validate_all_supported_field_types()
    test_field_types_recognized()
    test_validator_returns_validation_result()
    test_unsupported_field_type_returns_error()
    test_list_type_with_unsupported_inner_type()
    print("\n" + "="*60)
    print("✓ All F009 tests passed!")
    print("="*60)
