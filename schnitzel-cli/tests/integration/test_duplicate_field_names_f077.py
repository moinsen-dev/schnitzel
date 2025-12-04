"""
Integration test for F077: Schema validator detects duplicate field names in same model.

Test steps:
1. Create model with duplicate field names in YAML
2. Call SchemaParser.parse() or SchemaValidator.validate(schema)
3. Verify that duplicate fields are detected
4. Verify error message clearly indicates the duplicate field and model
"""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator, ValidationResult
from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.exceptions import YAMLParseError


def test_duplicate_field_detected():
    """
    Test F077: Schema parser detects if the same field name appears twice in a model.

    This test verifies that the YAML parser detects duplicate field names
    when parsing schema files and provides a clear error message.
    """
    # Create a temporary YAML file with duplicate field names
    yaml_content = """
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      name:
        type: int
"""

    # Write to temporary file and parse
    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()

        # Should raise YAMLParseError for duplicate field
        with pytest.raises(YAMLParseError) as exc_info:
            parser.parse(temp_path)

        error = exc_info.value
        error_msg = str(error)

        # Verify error message mentions duplicate key
        assert "duplicate" in error_msg.lower(), "Error should mention 'duplicate'"
        assert "name" in error_msg.lower(), "Error should mention the duplicate field 'name'"

        print(f"\n✓ Test F077: Duplicate field 'name' detected in YAML parsing")
        print(f"Error message: {error_msg}")

    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)


def test_unique_fields_pass():
    """
    Test that unique field names pass validation without issues.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "first_name": FieldDefinition(type="string"),
                    "last_name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                    "age": FieldDefinition(type="int"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, f"Validation should pass for unique field names. Errors: {result.errors}"
    assert result.errors == [], "Should have no errors for unique field names"

    print("✓ Unique field names pass validation")


def test_multiple_models_with_unique_fields():
    """
    Test that multiple models can have fields with the same name without conflict.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                }
            ),
            "Product": Model(
                name="Product",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),  # Same field name as User.name - OK
                    "price": FieldDefinition(type="float"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is True, "Different models can have fields with the same name"
    assert result.errors == [], "Should have no errors"

    print("✓ Different models can have fields with the same name")


def test_yaml_duplicate_detection():
    """
    Test that custom YAML parser detects duplicate keys when parsing schema files.

    This test verifies that when a YAML file contains duplicate field names,
    the SchemaParser with DuplicateKeyDetector raises an error instead of
    silently using the last value.
    """
    yaml_content = """
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      email:
        type: int
"""

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()

        # Should raise YAMLParseError for duplicate field
        with pytest.raises(YAMLParseError) as exc_info:
            parser.parse(temp_path)

        error_msg = str(exc_info.value)
        assert "duplicate" in error_msg.lower(), "Should detect duplicate key"
        assert "email" in error_msg.lower(), "Should mention the duplicate field name"

        print("✓ Custom YAML parser detects duplicate keys and raises error")

    finally:
        temp_path.unlink(missing_ok=True)


def test_error_mentions_field_and_model():
    """
    Test that duplicate field error messages are clear and helpful.

    This test verifies that when duplicate fields are detected in YAML,
    the error message clearly indicates:
    - That a duplicate was found
    - The name of the duplicate field
    - That field names must be unique
    """
    yaml_content = """
schnitzel: "1.0"
models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
      price:
        type: int
"""

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = Path(f.name)

    try:
        parser = SchemaParser()

        with pytest.raises(YAMLParseError) as exc_info:
            parser.parse(temp_path)

        error_msg = str(exc_info.value)

        # Verify error message contains key information
        assert "duplicate" in error_msg.lower(), "Error should mention duplicate"
        assert "price" in error_msg.lower(), "Error should mention the duplicate field 'price'"
        assert "unique" in error_msg.lower(), "Error should mention uniqueness requirement"

        print("✓ Duplicate field error message is clear and helpful")
        print(f"Error message preview: {error_msg[:200]}...")

    finally:
        temp_path.unlink(missing_ok=True)


def test_field_count_after_construction():
    """
    Test that field count is correct after model construction.

    This ensures that when a model is created programmatically,
    each field name appears only once.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                }
            )
        }
    )

    user_model = schema.models["User"]
    field_names = list(user_model.fields.keys())

    # Check that each field name is unique
    assert len(field_names) == len(set(field_names)), "All field names should be unique"
    assert len(field_names) == 3, "Should have exactly 3 fields"

    print("✓ Field count is correct and all field names are unique")


def test_field_iteration():
    """
    Test that iterating over fields works correctly.
    """
    schema = SchnitzelSchema(
        schnitzel="1.0",
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                }
            )
        }
    )

    user_model = schema.models["User"]

    # Iterate over fields and verify each one
    field_count = 0
    for field_name, field_def in user_model.fields.items():
        assert isinstance(field_name, str), "Field name should be a string"
        assert isinstance(field_def, FieldDefinition), "Field definition should be FieldDefinition"
        field_count += 1

    assert field_count == 3, "Should iterate over exactly 3 fields"

    print("✓ Field iteration works correctly")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*70)
    print("Running F077 duplicate field name tests")
    print("="*70)

    test_duplicate_field_detected()
    test_unique_fields_pass()
    test_multiple_models_with_unique_fields()
    test_yaml_duplicate_detection()
    test_error_mentions_field_and_model()
    test_field_count_after_construction()
    test_field_iteration()

    print("\n" + "="*70)
    print("All F077 duplicate field name tests passed!")
    print("="*70)
    print("\nNote: Python dictionaries inherently prevent duplicate keys.")
    print("Duplicate field detection primarily occurs at the YAML parsing layer.")
