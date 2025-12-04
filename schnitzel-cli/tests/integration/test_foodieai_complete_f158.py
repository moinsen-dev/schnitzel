"""Integration tests for F158 - FoodieAI schema complete integration test.

Test Requirements:
- test_foodieai_schema_parses - FoodieAI schema parses successfully
- test_foodieai_all_models_present - All 4 models are generated
- test_foodieai_relationships_correct - Relationships work correctly
- test_foodieai_validation_rules - Validation rules are applied
- test_foodieai_enum_support - Enum fields work correctly
- test_foodieai_complete_python - Python generation complete
- test_foodieai_complete_dart - Dart generation complete

FoodieAI Schema includes:
- User: id, name, email, bio, created_at
- Recipe: id, title, description, ingredients (list<string>), prep_time, difficulty (enum)
- Review: id, rating (1-5), comment, created_at
- Category: id, name, description
- Relationships: Recipe belongsTo User, Recipe belongsTo Category, Review belongsTo Recipe/User
"""

import tempfile
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app
from schnitzel.schema import SchemaParser
from schnitzel.generators.python import PythonModelGenerator
from schnitzel.generators.dart import DartModelGenerator

runner = CliRunner()

# Complete FoodieAI Schema
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
        type: text
        optional: true
      created_at:
        type: datetime
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
        max_length: 200
      description:
        type: text
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
        type: text
      recipe_id:
        type: uuid
      user_id:
        type: uuid
      created_at:
        type: datetime
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
        max_length: 100
      description:
        type: text
        optional: true
    relations:
      recipes:
        type: hasMany
        model: Recipe
"""


def test_foodieai_schema_parses() -> None:
    """Test that FoodieAI schema parses successfully."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Should parse successfully
        assert schema is not None
        assert schema.schnitzel in ["1.0", "1.0.0"]
        assert len(schema.models) == 4

    finally:
        schema_path.unlink()


def test_foodieai_all_models_present() -> None:
    """Test that all 4 FoodieAI models are present."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Check all models are present
        assert "User" in schema.models
        assert "Recipe" in schema.models
        assert "Review" in schema.models
        assert "Category" in schema.models

        # Check each model has expected fields
        assert "email" in schema.models["User"].fields
        assert "ingredients" in schema.models["Recipe"].fields
        assert "rating" in schema.models["Review"].fields
        assert "name" in schema.models["Category"].fields

    finally:
        schema_path.unlink()


def test_foodieai_relationships_correct() -> None:
    """Test that FoodieAI relationships are correctly defined."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # User has recipes and reviews
        user_relations = schema.models["User"].relations
        assert "recipes" in user_relations
        assert "reviews" in user_relations
        assert user_relations["recipes"].type == "hasMany"

        # Recipe belongs to User and Category
        recipe_relations = schema.models["Recipe"].relations
        assert "author" in recipe_relations
        assert "category" in recipe_relations
        assert recipe_relations["author"].type == "belongsTo"

        # Review belongs to Recipe and User
        review_relations = schema.models["Review"].relations
        assert "recipe" in review_relations
        assert "user" in review_relations

    finally:
        schema_path.unlink()


def test_foodieai_validation_rules() -> None:
    """Test that FoodieAI validation rules are applied."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Check rating validation (1-5)
        assert "ge=1" in code, "Rating should have min=1"
        assert "le=5" in code, "Rating should have max=5"

        # Check prep_time validation (min=0)
        assert "ge=0" in code, "Prep time should have min=0"

        # Check string length validation
        assert "max_length=200" in code, "Title should have max_length=200"
        assert "max_length=100" in code, "Category name should have max_length=100"

    finally:
        schema_path.unlink()


def test_foodieai_enum_support() -> None:
    """Test that difficulty enum is correctly generated."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should import Literal for enum
        assert "from typing import Literal" in code

        # Should have Literal type for difficulty
        assert 'Literal["easy", "medium", "hard"]' in code

    finally:
        schema_path.unlink()


def test_foodieai_complete_python() -> None:
    """Test that complete Python code is generated for FoodieAI."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # All models should be present
        assert "class User(BaseModel):" in code
        assert "class Recipe(BaseModel):" in code
        assert "class Review(BaseModel):" in code
        assert "class Category(BaseModel):" in code

        # Should have required imports
        assert "from pydantic import BaseModel" in code
        assert "from uuid import UUID" in code
        assert "from datetime import datetime" in code
        assert "from typing import Literal" in code

        # Should have relationships with forward references
        assert "from __future__ import annotations" in code
        assert "list[Recipe]" in code or "Recipe | None" in code

        # Should have list fields
        assert "list[str]" in code  # ingredients

    finally:
        schema_path.unlink()


def test_foodieai_complete_dart() -> None:
    """Test that complete Dart code is generated for FoodieAI."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All models should be present
        assert "class User with" in code
        assert "class Recipe with" in code
        assert "class Review with" in code
        assert "class Category with" in code

        # Should have @freezed annotations
        assert code.count("@freezed") == 4

        # Should have imports
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code

        # Should have part directives
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code

        # Should have factory constructors
        assert "const factory User(" in code
        assert "const factory Recipe(" in code

        # Should have fromJson
        assert ".fromJson(Map<String, dynamic> json)" in code

    finally:
        schema_path.unlink()


def test_foodieai_cli_integration() -> None:
    """Test FoodieAI schema through CLI commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "foodieai.yaml"
        schema_path.write_text(FOODIEAI_SCHEMA)

        # Test validate
        result = runner.invoke(app, ["validate", str(schema_path)])
        assert result.exit_code == 0, f"Validate failed: {result.stdout}"

        # Test generate Python
        result = runner.invoke(app, ["generate", str(schema_path), "--target", "python"])
        assert result.exit_code == 0, f"Generate Python failed: {result.stdout}"

        # Test generate Dart
        result = runner.invoke(app, ["generate", str(schema_path), "--target", "dart"])
        assert result.exit_code == 0, f"Generate Dart failed: {result.stdout}"


def test_foodieai_list_fields() -> None:
    """Test that list fields work correctly in FoodieAI schema."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Check that ingredients field is list<string>
        recipe = schema.models["Recipe"]
        assert "ingredients" in recipe.fields
        assert recipe.fields["ingredients"].type.lower() == "list<string>"

        # Python generation
        python_gen = PythonModelGenerator()
        python_code = python_gen.generate(schema)
        assert "ingredients: list[str]" in python_code

        # Dart generation
        dart_gen = DartModelGenerator()
        dart_code = dart_gen.generate(schema)
        assert "List<String>" in dart_code

    finally:
        schema_path.unlink()


def test_foodieai_descriptions() -> None:
    """Test that model and field descriptions are preserved."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(FOODIEAI_SCHEMA)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Python
        python_gen = PythonModelGenerator()
        python_code = python_gen.generate(schema)

        # Should have model descriptions as docstrings
        assert '"""A user who can create recipes and write reviews"""' in python_code
        assert '"""A recipe created by a user"""' in python_code
        assert '"""A review of a recipe by a user"""' in python_code

        # Dart
        dart_gen = DartModelGenerator()
        dart_code = dart_gen.generate(schema)

        # Should have model descriptions as doc comments
        assert "/// A user who can create recipes and write reviews" in dart_code
        assert "/// A recipe created by a user" in dart_code

    finally:
        schema_path.unlink()
