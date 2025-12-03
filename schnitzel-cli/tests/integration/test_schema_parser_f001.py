"""Integration test for F001: Schema parser can load a valid YAML file with basic model definition."""

from pathlib import Path

from schnitzel.schema import SchemaParser, SchnitzelSchema


def test_parse_minimal_user_schema():
    """
    Test F001: Schema parser can load a valid YAML file with basic model definition.

    Test steps:
    1. Create a minimal YAML schema file with one model (User) and two fields (id: uuid, name: string)
    2. Call SchemaParser.parse(filepath) with the test file
    3. Verify parser returns a SchnitzelSchema object
    4. Verify schema.models contains exactly one model
    5. Verify model.name equals 'User'
    6. Verify model has two fields with correct names and types
    7. Verify no parse errors are raised
    """
    # Arrange
    test_file = Path(__file__).parent / "fixtures" / "minimal_user_schema.yaml"
    parser = SchemaParser()

    # Act - Step 2: Call SchemaParser.parse(filepath)
    schema = parser.parse(test_file)

    # Assert - Step 3: Verify parser returns a SchnitzelSchema object
    assert isinstance(schema, SchnitzelSchema), "Parser should return a SchnitzelSchema object"

    # Assert - Step 4: Verify schema.models contains exactly one model
    assert len(schema.models) == 1, f"Expected 1 model, got {len(schema.models)}"

    # Assert - Step 5: Verify model.name equals 'User'
    assert "User" in schema.models, "Schema should contain a model named 'User'"
    user_model = schema.models["User"]
    assert user_model.name == "User", f"Model name should be 'User', got '{user_model.name}'"

    # Assert - Step 6: Verify model has two fields with correct names and types
    assert len(user_model.fields) == 2, f"User model should have 2 fields, got {len(user_model.fields)}"

    # Verify 'id' field
    assert "id" in user_model.fields, "User model should have an 'id' field"
    id_field = user_model.fields["id"]
    assert id_field.type == "uuid", f"id field should be type 'uuid', got '{id_field.type}'"
    assert id_field.primary is True, "id field should be primary key"

    # Verify 'name' field
    assert "name" in user_model.fields, "User model should have a 'name' field"
    name_field = user_model.fields["name"]
    assert name_field.type == "string", f"name field should be type 'string', got '{name_field.type}'"

    # Step 7: No parse errors were raised (implicit - test would fail if errors occurred)
    print("\n✓ Test F001 passed: Schema parser successfully loaded valid YAML file")


def test_schema_has_version():
    """Verify the schema has the schnitzel version."""
    test_file = Path(__file__).parent / "fixtures" / "minimal_user_schema.yaml"
    parser = SchemaParser()
    schema = parser.parse(test_file)

    assert schema.schnitzel == "1.0", "Schema should have schnitzel version '1.0'"


def test_model_has_description():
    """Verify the model description is parsed correctly."""
    test_file = Path(__file__).parent / "fixtures" / "minimal_user_schema.yaml"
    parser = SchemaParser()
    schema = parser.parse(test_file)

    user_model = schema.models["User"]
    assert user_model.description == "A simple user model for testing"


if __name__ == "__main__":
    # Allow running test directly for quick verification
    test_parse_minimal_user_schema()
    test_schema_has_version()
    test_model_has_description()
    print("\n✓ All F001 tests passed!")
