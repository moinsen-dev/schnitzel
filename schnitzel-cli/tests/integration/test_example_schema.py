"""Test parsing the FoodieAI example schema."""

from pathlib import Path

from schnitzel.schema import SchemaParser


def test_parse_foodieai_restaurants_schema():
    """Test parsing the FoodieAI restaurants feature schema."""
    # Get path to example schema
    schema_path = Path(__file__).parent.parent.parent.parent / "examples" / "foodie-ai" / "features" / "restaurants" / "schema.yaml"

    if not schema_path.exists():
        print(f"⚠ Skipping test: example schema not found at {schema_path}")
        return

    parser = SchemaParser()
    schema = parser.parse(schema_path)

    # Verify it parsed successfully
    assert schema is not None
    assert len(schema.models) > 0

    # Verify Restaurant model exists
    assert "Restaurant" in schema.models
    restaurant = schema.models["Restaurant"]

    # Verify some key fields
    assert "id" in restaurant.fields
    assert "name" in restaurant.fields
    assert restaurant.fields["id"].type == "uuid"
    assert restaurant.fields["name"].type == "string"

    print(f"✓ Successfully parsed FoodieAI restaurants schema with {len(schema.models)} models")


if __name__ == "__main__":
    test_parse_foodieai_restaurants_schema()
