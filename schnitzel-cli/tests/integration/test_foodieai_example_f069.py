"""Integration tests for F069 - FoodieAI example schema with full generation pipeline.

Test Requirements:
- test_foodieai_schema_parses - schema is valid YAML
- test_foodieai_schema_validates - passes validation
- test_foodieai_generates_python - creates Python models
- test_foodieai_generates_dart - creates Dart models
- test_foodieai_python_has_all_models - all 4 models present
- test_foodieai_has_relationships - relationships generate correctly

FoodieAI Schema includes:
- User: id, name, email, bio
- Recipe: id, title, description, ingredients (list<string>), prep_time (int), difficulty (enum)
- Review: id, rating (int with min/max), comment, recipe_id, user_id
- Category: id, name, description
- Relationships: Recipe belongsTo User, Review belongsTo Recipe, Review belongsTo User
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app
from schnitzel.schema import SchemaParser, SchemaValidator

runner = CliRunner()

# FoodieAI Schema Definition
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
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def foodieai_schema_file(temp_dir: Path) -> Path:
    """Create FoodieAI schema file in temp directory."""
    schema_file = temp_dir / "foodieai.schnitzel.yaml"
    schema_file.write_text(FOODIEAI_SCHEMA)
    return schema_file


def test_foodieai_schema_parses(foodieai_schema_file: Path) -> None:
    """Test that FoodieAI schema is valid YAML and parses successfully."""
    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema_file)

    # Verify schema parsed successfully
    assert schema is not None, "Schema should parse successfully"
    assert schema.schnitzel == "1.0", "Schema version should be 1.0"
    assert len(schema.models) == 4, "Schema should contain exactly 4 models"

    # Verify all expected models are present
    expected_models = {"User", "Recipe", "Review", "Category"}
    assert set(schema.models.keys()) == expected_models, "All models should be present"

    print("\n✓ FoodieAI schema parses successfully")


def test_foodieai_schema_validates(foodieai_schema_file: Path) -> None:
    """Test that FoodieAI schema passes validation."""
    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema_file)

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passes
    assert result.valid is True, f"Schema validation should pass. Errors: {result.errors}"
    assert len(result.errors) == 0, "Valid schema should have no validation errors"

    print("\n✓ FoodieAI schema passes validation")


def test_foodieai_generates_python(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that FoodieAI schema generates Python models correctly."""
    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Generating Python models" in result.stdout
    assert "4 models" in result.stdout or "(4 models)" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify models.py was created
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists(), "Python models.py should be created"

    # Read generated Python models
    models_content = models_file.read_text()

    # Verify file structure
    assert "Generated by Schnitzel Framework" in models_content
    assert "from __future__ import annotations" in models_content
    assert "from pydantic import BaseModel" in models_content
    assert "from uuid import UUID" in models_content

    print("\n✓ FoodieAI schema generates Python models")


def test_foodieai_generates_dart(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that FoodieAI schema generates Dart models correctly."""
    # Run generate command with --target flutter
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Generating Dart models" in result.stdout
    assert "4 models" in result.stdout or "(4 models)" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify Dart models file was created
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists(), "Dart models file should be created"

    # Read generated Dart models
    dart_content = dart_models_file.read_text()

    # Verify file structure
    assert "Generated by Schnitzel Framework" in dart_content
    assert "import 'package:freezed_annotation/freezed_annotation.dart'" in dart_content
    assert "@freezed" in dart_content

    print("\n✓ FoodieAI schema generates Dart models")


def test_foodieai_python_has_all_models(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that generated Python models contain all 4 FoodieAI models."""
    # Generate Python models
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated models
    models_file = temp_dir / "backend" / "app" / "models.py"
    models_content = models_file.read_text()

    # Verify all 4 models are present
    assert "class User(BaseModel):" in models_content, "User model should be generated"
    assert "class Recipe(BaseModel):" in models_content, "Recipe model should be generated"
    assert "class Review(BaseModel):" in models_content, "Review model should be generated"
    assert "class Category(BaseModel):" in models_content, "Category model should be generated"

    # Verify User fields
    assert "name: str" in models_content
    assert "email: str" in models_content
    assert "bio: str | None = None" in models_content, "Bio should be optional"

    # Verify Recipe fields
    assert "title: str" in models_content
    assert "description: str" in models_content
    assert "ingredients: list[str]" in models_content, "Ingredients should be list<string>"
    assert "prep_time: int" in models_content
    assert 'difficulty: Literal["easy", "medium", "hard"]' in models_content, "Difficulty should be enum (Literal in Python)"

    # Verify Recipe constraints
    assert "Field(ge=0" in models_content, "prep_time should have min constraint"

    # Verify Review fields
    assert "rating: int" in models_content
    assert "comment: str" in models_content

    # Verify Review constraints
    assert "Field(ge=1, le=5" in models_content, "rating should have min=1, max=5 constraints"

    # Verify Category fields
    assert "name: str" in models_content  # Category name field

    print("\n✓ Python models contain all 4 FoodieAI models with correct fields")


def test_foodieai_has_relationships(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that FoodieAI relationships generate correctly in Python and Dart."""
    # Generate Python models
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read Python models
    models_file = temp_dir / "backend" / "app" / "models.py"
    models_content = models_file.read_text()

    # Verify Recipe belongsTo User relationship
    assert "author: User | None = None" in models_content, "Recipe should have belongsTo User (author)"

    # Verify Recipe belongsTo Category relationship
    assert "category: Category | None = None" in models_content, "Recipe should have belongsTo Category"

    # Verify Review belongsTo Recipe relationship
    assert "recipe: Recipe | None = None" in models_content, "Review should have belongsTo Recipe"

    # Verify Review belongsTo User relationship
    assert "user: User | None = None" in models_content, "Review should have belongsTo User"

    # Verify User hasMany recipes relationship
    assert "recipes: list[Recipe] = []" in models_content, "User should have hasMany Recipe"

    # Verify User hasMany reviews relationship
    assert "reviews: list[Review] = []" in models_content, "User should have hasMany Review"

    # Verify Recipe hasMany reviews relationship
    # Note: This might conflict with the reviews field on User, so check context
    review_count = models_content.count("reviews: list[Review] = []")
    assert review_count >= 2, "Both User and Recipe should have reviews relationship"

    # Verify Category hasMany recipes relationship
    # Note: This might conflict with User's recipes, check for proper context
    recipes_count = models_content.count("recipes: list[Recipe] = []")
    assert recipes_count >= 2, "Both User and Category should have recipes relationship"

    print("\n✓ Relationships generate correctly")


def test_foodieai_dart_has_all_models(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that generated Dart models contain all 4 FoodieAI models."""
    # Generate Dart models
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "flutter"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated Dart models
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    dart_content = dart_models_file.read_text()

    # Verify all 4 models are present
    assert "class User" in dart_content, "User model should be generated"
    assert "class Recipe" in dart_content, "Recipe model should be generated"
    assert "class Review" in dart_content, "Review model should be generated"
    assert "class Category" in dart_content, "Category model should be generated"

    # Count @freezed decorators (should be 4)
    freezed_count = dart_content.count("@freezed")
    assert freezed_count == 4, "Should have 4 @freezed models"

    print("\n✓ Dart models contain all 4 FoodieAI models")


def test_foodieai_python_is_valid_syntax(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that generated Python code is syntactically valid."""
    # Generate Python models
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated models
    models_file = temp_dir / "backend" / "app" / "models.py"
    models_content = models_file.read_text()

    # Verify Python syntax by compiling
    try:
        compile(models_content, str(models_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code has syntax errors: {e}")

    print("\n✓ Generated Python code is syntactically valid")


def test_foodieai_full_pipeline(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test the complete generation pipeline: parse -> validate -> generate both targets."""
    # Step 1: Parse schema
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema_file)
    assert schema is not None

    # Step 2: Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)
    assert result.valid is True, f"Validation failed: {result.errors}"

    # Step 3: Generate Python models
    python_result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])
    assert python_result.exit_code == 0, f"Python generation failed: {python_result.stdout}"

    # Step 4: Generate Dart models
    dart_result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "flutter"])
    assert dart_result.exit_code == 0, f"Dart generation failed: {dart_result.stdout}"

    # Step 5: Verify both output files exist
    python_models = temp_dir / "backend" / "app" / "models.py"
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"

    assert python_models.exists(), "Python models should exist"
    assert dart_models.exists(), "Dart models should exist"

    # Step 6: Verify Python models can be imported and instantiated
    # Read and exec the generated code to avoid module caching issues
    models_code = python_models.read_text()

    # Create namespace with required imports
    namespace = {}
    try:
        exec(models_code, namespace)

        # Verify all models are accessible
        assert "User" in namespace, "User class should exist"
        assert "Recipe" in namespace, "Recipe class should exist"
        assert "Review" in namespace, "Review class should exist"
        assert "Category" in namespace, "Category class should exist"

        # Get classes from namespace
        User = namespace["User"]
        Recipe = namespace["Recipe"]
        Review = namespace["Review"]
        Category = namespace["Category"]

        # Rebuild models with forward references (needed when using exec())
        User.model_rebuild(_types_namespace=namespace)
        Recipe.model_rebuild(_types_namespace=namespace)
        Review.model_rebuild(_types_namespace=namespace)
        Category.model_rebuild(_types_namespace=namespace)

        # Try creating an instance of each model
        from uuid import uuid4
        from datetime import datetime

        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            created_at=datetime.now()
        )
        assert user.name == "Test User"
        assert user.bio is None  # optional field

        recipe = Recipe(
            id=uuid4(),
            title="Test Recipe",
            description="A test recipe",
            ingredients=["flour", "sugar", "eggs"],
            prep_time=30,
            difficulty="easy",
            author_id=user.id,
            category_id=uuid4(),
            created_at=datetime.now()
        )
        assert recipe.ingredients == ["flour", "sugar", "eggs"]
        assert recipe.prep_time == 30
        assert recipe.difficulty == "easy"

        review = Review(
            id=uuid4(),
            rating=5,
            comment="Excellent recipe!",
            recipe_id=recipe.id,
            user_id=user.id,
            created_at=datetime.now()
        )
        assert review.rating == 5
        assert 1 <= review.rating <= 5  # Validate constraints

        category = Category(
            id=uuid4(),
            name="Desserts",
            description="Sweet treats",
            created_at=datetime.now()
        )
        assert category.name == "Desserts"

    except Exception as e:
        pytest.fail(f"Generated Python code cannot be imported: {e}")

    print("\n✓ Full FoodieAI generation pipeline works end-to-end")


def test_foodieai_enum_field_generation(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that enum field (difficulty) generates correctly."""
    # Generate Python models
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read models
    models_file = temp_dir / "backend" / "app" / "models.py"
    models_content = models_file.read_text()

    # Verify difficulty field is generated as Literal (proper enum handling in Pydantic)
    assert 'difficulty: Literal["easy", "medium", "hard"]' in models_content
    assert "from typing import Literal" in models_content

    print("\n✓ Enum field generates correctly as Literal type")


def test_foodieai_list_field_generation(foodieai_schema_file: Path, temp_dir: Path) -> None:
    """Test that list<string> field (ingredients) generates correctly."""
    # Generate Python models
    result = runner.invoke(app, ["generate", str(foodieai_schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read models
    models_file = temp_dir / "backend" / "app" / "models.py"
    models_content = models_file.read_text()

    # Verify ingredients field is list[str]
    assert "ingredients: list[str]" in models_content

    print("\n✓ List field generates correctly")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F069: FoodieAI example schema integration test")
    print("=" * 70)

    import sys
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        temp_path = Path(tmpdir)

        # Create schema file
        schema_file = temp_path / "foodieai.schnitzel.yaml"
        schema_file.write_text(FOODIEAI_SCHEMA)

        try:
            print("\n1. Testing schema parsing...")
            test_foodieai_schema_parses(schema_file)

            print("\n2. Testing schema validation...")
            test_foodieai_schema_validates(schema_file)

            print("\n3. Testing Python generation...")
            test_foodieai_generates_python(schema_file, temp_path)

            print("\n4. Testing Dart generation...")
            test_foodieai_generates_dart(schema_file, temp_path)

            print("\n5. Testing Python models completeness...")
            test_foodieai_python_has_all_models(schema_file, temp_path)

            print("\n6. Testing relationships...")
            test_foodieai_has_relationships(schema_file, temp_path)

            print("\n7. Testing Dart models completeness...")
            test_foodieai_dart_has_all_models(schema_file, temp_path)

            print("\n8. Testing Python syntax validity...")
            test_foodieai_python_is_valid_syntax(schema_file, temp_path)

            print("\n9. Testing full pipeline...")
            test_foodieai_full_pipeline(schema_file, temp_path)

            print("\n10. Testing enum field generation...")
            test_foodieai_enum_field_generation(schema_file, temp_path)

            print("\n11. Testing list field generation...")
            test_foodieai_list_field_generation(schema_file, temp_path)

            print("\n" + "=" * 70)
            print("✓ All F069 tests passed!")
            print("=" * 70)

        finally:
            os.chdir(original_cwd)
