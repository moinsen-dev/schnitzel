"""Integration tests for F132 - test_foodieai_example.py validates against real-world schema.

Test Requirements:
- test_foodieai_schema_is_valid: FoodieAI schema validates correctly
- test_foodieai_has_all_models: All 4 models (User, Recipe, Review, Category) present
- test_foodieai_field_types_correct: Field types match specification
- test_foodieai_validation_rules: Validation rules (min/max, format, unique) work
- test_foodieai_relationships_valid: Relationships are correctly defined
- test_foodieai_generates_without_errors: Full generation succeeds
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner

from schnitzel.cli import app
from schnitzel.schema import SchemaParser, SchemaValidator

runner = CliRunner()

# FoodieAI Schema - Real-world complex example
FOODIEAI_SCHEMA = """schnitzel: "1.0"

models:
  User:
    description: "A user who can create recipes and write reviews"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
        format: email
      bio:
        type: string
        optional: true
      created_at:
        type: datetime
        auto: create
    relations:
      recipes:
        type: hasMany
        model: Recipe
      reviews:
        type: hasMany
        model: Review

  Recipe:
    description: "A recipe created by a user"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      description:
        type: string
      ingredients:
        type: list<string>
      prep_time:
        type: int
        min: 0
      difficulty:
        type: enum
        values: ["easy", "medium", "hard"]
      author_id:
        type: uuid
      category_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      category:
        type: belongsTo
        model: Category
        foreign_key: category_id
      reviews:
        type: hasMany
        model: Review

  Review:
    description: "A review of a recipe by a user"
    fields:
      id:
        type: uuid
        primary: true
      rating:
        type: int
        min: 1
        max: 5
      comment:
        type: string
      recipe_id:
        type: uuid
      user_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      recipe:
        type: belongsTo
        model: Recipe
        foreign_key: recipe_id
      user:
        type: belongsTo
        model: User
        foreign_key: user_id

  Category:
    description: "A category for organizing recipes"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        unique: true
      description:
        type: string
      created_at:
        type: datetime
        auto: create
    relations:
      recipes:
        type: hasMany
        model: Recipe
"""


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def foodieai_schema(temp_dir: Path) -> Path:
    """Create FoodieAI schema file."""
    schema_file = temp_dir / "foodieai.schnitzel.yaml"
    schema_file.write_text(FOODIEAI_SCHEMA)
    return schema_file


def test_foodieai_schema_is_valid(foodieai_schema: Path) -> None:
    """Test that FoodieAI schema is valid and passes validation."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    assert schema is not None, "Schema should parse successfully"

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True, f"FoodieAI schema should be valid. Errors: {result.errors}"
    assert len(result.errors) == 0, "Valid schema should have no errors"

    print("\n✓ FoodieAI schema is valid")


def test_foodieai_has_all_models(foodieai_schema: Path) -> None:
    """Test that FoodieAI schema has all 4 expected models."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Verify model count
    assert len(schema.models) == 4, "FoodieAI should have exactly 4 models"

    # Verify all expected models exist
    expected_models = {"User", "Recipe", "Review", "Category"}
    actual_models = set(schema.models.keys())
    assert actual_models == expected_models, f"Should have {expected_models}, got {actual_models}"

    print("\n✓ FoodieAI has all 4 models: User, Recipe, Review, Category")


def test_foodieai_field_types_correct(foodieai_schema: Path) -> None:
    """Test that FoodieAI field types match specification."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Test User fields
    user = schema.models["User"]
    assert "email" in user.fields, "User should have email field"
    assert user.fields["email"].type == "string", "Email should be string type"
    assert user.fields["bio"].optional is True, "Bio should be optional"

    # Test Recipe fields
    recipe = schema.models["Recipe"]
    assert "ingredients" in recipe.fields, "Recipe should have ingredients field"
    assert recipe.fields["ingredients"].type == "list<string>", "Ingredients should be list<string>"
    assert recipe.fields["difficulty"].type == "enum", "Difficulty should be enum"
    assert recipe.fields["difficulty"].values == ["easy", "medium", "hard"], "Difficulty should have 3 values"

    # Test Review fields
    review = schema.models["Review"]
    assert "rating" in review.fields, "Review should have rating field"
    assert review.fields["rating"].type == "int", "Rating should be int"

    # Test Category fields
    category = schema.models["Category"]
    assert "name" in category.fields, "Category should have name field"
    assert category.fields["name"].unique is True, "Category name should be unique"

    print("\n✓ FoodieAI field types are correct")


def test_foodieai_validation_rules(foodieai_schema: Path) -> None:
    """Test that FoodieAI validation rules are correctly defined."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Test min/max constraints
    recipe = schema.models["Recipe"]
    prep_time = recipe.fields["prep_time"]
    assert prep_time.min == 0, "prep_time should have min=0"

    review = schema.models["Review"]
    rating = review.fields["rating"]
    assert rating.min == 1, "rating should have min=1"
    assert rating.max == 5, "rating should have max=5"

    # Test format constraints
    user = schema.models["User"]
    email = user.fields["email"]
    assert email.format == "email", "email should have format=email"

    # Test unique constraints
    assert email.unique is True, "email should be unique"

    category = schema.models["Category"]
    category_name = category.fields["name"]
    assert category_name.unique is True, "category name should be unique"

    print("\n✓ FoodieAI validation rules are correct")


def test_foodieai_relationships_valid(foodieai_schema: Path) -> None:
    """Test that FoodieAI relationships are correctly defined."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Test User relationships
    user = schema.models["User"]
    assert "recipes" in user.relations, "User should have recipes relation"
    assert user.relations["recipes"].type == "hasMany", "recipes should be hasMany"
    assert user.relations["recipes"].model == "Recipe", "recipes should point to Recipe"

    assert "reviews" in user.relations, "User should have reviews relation"
    assert user.relations["reviews"].type == "hasMany", "reviews should be hasMany"

    # Test Recipe relationships
    recipe = schema.models["Recipe"]
    assert "author" in recipe.relations, "Recipe should have author relation"
    assert recipe.relations["author"].type == "belongsTo", "author should be belongsTo"
    assert recipe.relations["author"].model == "User", "author should point to User"
    assert recipe.relations["author"].foreign_key == "author_id", "author should use author_id"

    assert "category" in recipe.relations, "Recipe should have category relation"
    assert recipe.relations["category"].type == "belongsTo", "category should be belongsTo"

    # Test Review relationships
    review = schema.models["Review"]
    assert "recipe" in review.relations, "Review should have recipe relation"
    assert review.relations["recipe"].type == "belongsTo", "recipe should be belongsTo"
    assert review.relations["recipe"].foreign_key == "recipe_id", "recipe should use recipe_id"

    assert "user" in review.relations, "Review should have user relation"
    assert review.relations["user"].type == "belongsTo", "user should be belongsTo"

    # Test Category relationships
    category = schema.models["Category"]
    assert "recipes" in category.relations, "Category should have recipes relation"
    assert category.relations["recipes"].type == "hasMany", "recipes should be hasMany"

    print("\n✓ FoodieAI relationships are valid")


def test_foodieai_generates_without_errors(foodieai_schema: Path, temp_dir: Path) -> None:
    """Test that FoodieAI schema generates all targets without errors."""
    # Generate all targets
    result = runner.invoke(app, ["generate", str(foodieai_schema)])

    # Should succeed
    assert result.exit_code == 0, f"Generation failed: {result.stdout}"
    assert "Generation complete" in result.stdout

    # Verify all outputs exist
    python_models = temp_dir / "backend" / "app" / "models.py"
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose = temp_dir / "docker-compose.yaml"

    assert python_models.exists(), "Python models should be generated"
    assert dart_models.exists(), "Dart models should be generated"
    assert docker_compose.exists(), "Docker compose should be generated"

    print("\n✓ FoodieAI generates all targets without errors")


def test_foodieai_python_has_correct_types(foodieai_schema: Path, temp_dir: Path) -> None:
    """Test that generated Python code has correct types for FoodieAI."""
    # Generate Python
    result = runner.invoke(app, ["generate", str(foodieai_schema), "--target", "python"])
    assert result.exit_code == 0

    # Read generated code
    python_models = temp_dir / "backend" / "app" / "models.py"
    content = python_models.read_text()

    # Verify User fields
    assert "email: str" in content, "User email should be str"
    assert "bio: str | None = None" in content, "Bio should be optional"

    # Verify Recipe fields
    assert "ingredients: list[str]" in content, "Ingredients should be list[str]"
    assert 'difficulty: Literal["easy", "medium", "hard"]' in content, "Difficulty should be Literal enum"

    # Verify Review constraints
    assert "Field(ge=1, le=5" in content, "Rating should have min=1, max=5"

    # Verify Recipe constraints
    assert "Field(ge=0" in content, "prep_time should have min=0"

    print("\n✓ FoodieAI Python code has correct types")


def test_foodieai_python_compiles(foodieai_schema: Path, temp_dir: Path) -> None:
    """Test that generated FoodieAI Python code is syntactically valid."""
    # Generate Python
    result = runner.invoke(app, ["generate", str(foodieai_schema), "--target", "python"])
    assert result.exit_code == 0

    # Read and compile
    python_models = temp_dir / "backend" / "app" / "models.py"
    content = python_models.read_text()

    try:
        compile(content, str(python_models), "exec")
        print("\n✓ FoodieAI Python code compiles successfully")
    except SyntaxError as e:
        pytest.fail(f"Generated Python has syntax errors: {e}")


def test_foodieai_represents_real_world_complexity(foodieai_schema: Path) -> None:
    """Test that FoodieAI demonstrates real-world schema complexity."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Count various features to show complexity
    total_fields = sum(len(model.fields) for model in schema.models.values())
    total_relations = sum(len(model.relations) if model.relations else 0 for model in schema.models.values())

    # Count special field types
    enum_fields = sum(1 for model in schema.models.values()
                     for field in model.fields.values() if field.type == "enum")
    list_fields = sum(1 for model in schema.models.values()
                     for field in model.fields.values() if field.type.startswith("list<"))
    constrained_fields = sum(1 for model in schema.models.values()
                            for field in model.fields.values() if field.min is not None or field.max is not None)

    # FoodieAI should demonstrate complexity
    assert total_fields >= 20, f"Real-world schema should have many fields (has {total_fields})"
    assert total_relations >= 8, f"Real-world schema should have relationships (has {total_relations})"
    assert enum_fields >= 1, f"Should have enum fields (has {enum_fields})"
    assert list_fields >= 1, f"Should have list fields (has {list_fields})"
    assert constrained_fields >= 2, f"Should have constrained fields (has {constrained_fields})"

    print(f"\n✓ FoodieAI represents real-world complexity:")
    print(f"  - {len(schema.models)} models")
    print(f"  - {total_fields} fields")
    print(f"  - {total_relations} relationships")
    print(f"  - {enum_fields} enum fields")
    print(f"  - {list_fields} list fields")
    print(f"  - {constrained_fields} constrained fields")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F132: FoodieAI example validates real-world schema")
    print("=" * 70)

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        temp_path = Path(tmpdir)

        # Create schema file
        schema_file = temp_path / "foodieai.schnitzel.yaml"
        schema_file.write_text(FOODIEAI_SCHEMA)

        try:
            print("\n1. Testing FoodieAI schema validity...")
            test_foodieai_schema_is_valid(schema_file)

            print("\n2. Testing FoodieAI has all models...")
            test_foodieai_has_all_models(schema_file)

            print("\n3. Testing field types...")
            test_foodieai_field_types_correct(schema_file)

            print("\n4. Testing validation rules...")
            test_foodieai_validation_rules(schema_file)

            print("\n5. Testing relationships...")
            test_foodieai_relationships_valid(schema_file)

            print("\n6. Testing generation without errors...")
            test_foodieai_generates_without_errors(schema_file, temp_path)

            print("\n7. Testing Python types...")
            test_foodieai_python_has_correct_types(schema_file, temp_path)

            print("\n8. Testing Python compilation...")
            test_foodieai_python_compiles(schema_file, temp_path)

            print("\n9. Testing real-world complexity...")
            test_foodieai_represents_real_world_complexity(schema_file)

            print("\n" + "=" * 70)
            print("✓ All F132 tests passed!")
            print("=" * 70)

        finally:
            os.chdir(original_cwd)
