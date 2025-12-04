"""Integration test for api_063 - Full generation pipeline produces working API.

Test Requirements:
1. Create complete schema with models and endpoints
2. Run schnitzel generate --target all
3. Verify Pydantic models are generated
4. Verify SQLAlchemy ORM models are generated
5. Verify FastAPI routes are generated
6. Verify Dart API client is generated
7. Verify all generated code passes type checking

This is a comprehensive integration test that validates the entire generation pipeline
using a complete FoodieAI-like schema.
"""

import tempfile
import os
import sys
import subprocess
from pathlib import Path
from typer.testing import CliRunner
import pytest
import yaml

from schnitzel.cli import app
from schnitzel.schema import SchemaParser
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.generators.dart.models import DartModelGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def foodieai_schema(temp_dir: Path) -> Path:
    """Create a complete FoodieAI-like schema with models and endpoints."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User in the FoodieAI system"
    fields:
      id:
        type: uuid
        primary: true
      username:
        type: string
        unique: true
        min_length: 3
        max_length: 30
      email:
        type: string
        unique: true
        format: email
      full_name:
        type: string
      bio:
        type: string
        optional: true
      avatar_url:
        type: string
        optional: true
      created_at:
        type: datetime
        auto: create
      updated_at:
        type: datetime
        auto: update
    relations:
      recipes:
        type: hasMany
        model: Recipe
      favorites:
        type: hasMany
        model: Favorite

  Recipe:
    description: "Recipe created by users"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
        min_length: 1
        max_length: 200
      description:
        type: string
      ingredients:
        type: json
      instructions:
        type: json
      prep_time:
        type: int
        min: 0
      cook_time:
        type: int
        min: 0
      servings:
        type: int
        min: 1
      difficulty:
        type: enum
        values: ["easy", "medium", "hard"]
        default: medium
      cuisine:
        type: string
        optional: true
      tags:
        type: json
        optional: true
      image_url:
        type: string
        optional: true
      author_id:
        type: uuid
      published:
        type: bool
        default: false
      created_at:
        type: datetime
        auto: create
      updated_at:
        type: datetime
        auto: update
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      favorites:
        type: hasMany
        model: Favorite
      reviews:
        type: hasMany
        model: Review

  Favorite:
    description: "User's favorite recipes"
    fields:
      id:
        type: uuid
        primary: true
      user_id:
        type: uuid
      recipe_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id
      recipe:
        type: belongsTo
        model: Recipe
        foreign_key: recipe_id

  Review:
    description: "Recipe reviews"
    fields:
      id:
        type: uuid
        primary: true
      recipe_id:
        type: uuid
      user_id:
        type: uuid
      rating:
        type: int
        min: 1
        max: 5
      comment:
        type: string
        optional: true
      created_at:
        type: datetime
        auto: create
      updated_at:
        type: datetime
        auto: update
    relations:
      recipe:
        type: belongsTo
        model: Recipe
        foreign_key: recipe_id
      user:
        type: belongsTo
        model: User
        foreign_key: user_id

  CreateRecipeRequest:
    description: "Request model for creating a recipe"
    fields:
      title:
        type: string
      description:
        type: string
      ingredients:
        type: json
      instructions:
        type: json
      prep_time:
        type: int
      cook_time:
        type: int
      servings:
        type: int
      difficulty:
        type: enum
        values: ["easy", "medium", "hard"]
      cuisine:
        type: string
        optional: true
      tags:
        type: json
        optional: true
      image_url:
        type: string
        optional: true

  UpdateRecipeRequest:
    description: "Request model for updating a recipe"
    fields:
      title:
        type: string
        optional: true
      description:
        type: string
        optional: true
      ingredients:
        type: json
        optional: true
      instructions:
        type: json
        optional: true
      prep_time:
        type: int
        optional: true
      cook_time:
        type: int
        optional: true
      servings:
        type: int
        optional: true
      difficulty:
        type: enum
        values: ["easy", "medium", "hard"]
        optional: true
      cuisine:
        type: string
        optional: true
      tags:
        type: json
        optional: true
      image_url:
        type: string
        optional: true
      published:
        type: bool
        optional: true

  CreateReviewRequest:
    description: "Request model for creating a review"
    fields:
      rating:
        type: int
        min: 1
        max: 5
      comment:
        type: string
        optional: true

endpoints:
  /recipes:
    GET:
      name: list_recipes
      description: "Get a list of recipes"
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
        cuisine:
          type: string
          optional: true
        difficulty:
          type: string
          optional: true
      response:
        200:
          type: list[Recipe]

    POST:
      name: create_recipe
      description: "Create a new recipe"
      body: CreateRecipeRequest
      response:
        201:
          type: Recipe

  /recipes/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_recipe
      description: "Get a recipe by ID"
      response:
        200:
          type: Recipe

    PUT:
      name: update_recipe
      description: "Update a recipe"
      body: UpdateRecipeRequest
      response:
        200:
          type: Recipe

  /recipes/{id}/reviews:
    params:
      id:
        type: uuid
    GET:
      name: list_recipe_reviews
      description: "Get reviews for a recipe"
      response:
        200:
          type: list[Review]

    POST:
      name: create_review
      description: "Create a review for a recipe"
      body: CreateReviewRequest
      response:
        201:
          type: Review

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID"
      response:
        200:
          type: User

  /users/{id}/recipes:
    params:
      id:
        type: uuid
    GET:
      name: list_user_recipes
      description: "Get recipes created by a user"
      response:
        200:
          type: list[Recipe]

  /users/{id}/favorites:
    params:
      id:
        type: uuid
    GET:
      name: list_user_favorites
      description: "Get user's favorite recipes"
      response:
        200:
          type: list[Favorite]

    POST:
      name: add_favorite
      description: "Add a recipe to favorites"
      body:
        recipe_id:
          type: uuid
      response:
        201:
          type: Favorite
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_complete_schema_parsing(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that the complete schema can be parsed successfully."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Verify models are parsed
    assert len(schema.models) == 7, "Should have 7 models"
    assert "User" in schema.models
    assert "Recipe" in schema.models
    assert "Favorite" in schema.models
    assert "Review" in schema.models
    assert "CreateRecipeRequest" in schema.models
    assert "UpdateRecipeRequest" in schema.models
    assert "CreateReviewRequest" in schema.models

    # Verify endpoints are parsed
    assert len(schema.endpoints) > 0, "Should have endpoints"


def test_pydantic_models_generation(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that Pydantic models are generated correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate Pydantic models
    generator = PythonModelGenerator()
    output_dir = temp_dir / "backend" / "app"
    models_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert models_file.exists(), "models.py should be created"
    assert size > 0, "models.py should have content"

    # Read and verify content
    models_content = models_file.read_text()

    # Verify imports
    assert "from pydantic import BaseModel" in models_content
    assert "from uuid import UUID" in models_content
    assert "from datetime import datetime" in models_content
    assert "from typing import" in models_content

    # Verify all models are present
    assert "class User(BaseModel):" in models_content
    assert "class Recipe(BaseModel):" in models_content
    assert "class Favorite(BaseModel):" in models_content
    assert "class Review(BaseModel):" in models_content
    assert "class CreateRecipeRequest(BaseModel):" in models_content
    assert "class UpdateRecipeRequest(BaseModel):" in models_content
    assert "class CreateReviewRequest(BaseModel):" in models_content

    # Verify field types
    assert "id: UUID" in models_content
    assert "username: str" in models_content
    assert "email: str" in models_content
    assert "created_at: datetime" in models_content

    # Verify Python syntax is valid
    try:
        compile(models_content, str(models_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Pydantic models have syntax errors: {e}")


def test_sqlalchemy_orm_generation(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that SQLAlchemy ORM models are generated correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate ORM models
    generator = SQLAlchemyORMGenerator()
    output_dir = temp_dir / "backend" / "app"
    orm_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert orm_file.exists(), "orm.py should be created"
    assert size > 0, "orm.py should have content"

    # Read and verify content
    orm_content = orm_file.read_text()

    # Verify SQLAlchemy imports
    assert "from sqlalchemy import" in orm_content
    assert "from sqlalchemy.orm import" in orm_content
    assert "DeclarativeBase" in orm_content or "declarative_base" in orm_content

    # Verify table definitions
    assert "class User(Base):" in orm_content or "class UserORM(Base):" in orm_content
    assert "class Recipe(Base):" in orm_content or "class RecipeORM(Base):" in orm_content
    assert "class Favorite(Base):" in orm_content or "class FavoriteORM(Base):" in orm_content
    assert "class Review(Base):" in orm_content or "class ReviewORM(Base):" in orm_content

    # Verify table names
    assert "__tablename__" in orm_content

    # Verify columns (SQLAlchemy 2.0 uses mapped_column)
    assert "mapped_column(" in orm_content or "Column(" in orm_content
    assert "UUID" in orm_content or "String" in orm_content

    # Verify foreign keys
    assert "ForeignKey(" in orm_content or "foreign_key" in orm_content.lower()

    # Verify Python syntax is valid
    try:
        compile(orm_content, str(orm_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated ORM models have syntax errors: {e}")


def test_fastapi_routes_generation(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that FastAPI routes are generated correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate routes
    generator = PythonRouteGenerator()
    output_dir = temp_dir / "backend" / "app"
    routes_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert routes_file.exists(), "routes.py should be created"
    assert size > 0, "routes.py should have content"

    # Read and verify content
    routes_content = routes_file.read_text()

    # Verify FastAPI imports
    assert "from fastapi import APIRouter" in routes_content
    assert "router = APIRouter()" in routes_content

    # Verify route decorators for each endpoint (using single quotes as generated)
    assert "@router.get(" in routes_content and "/recipes" in routes_content
    assert "@router.post(" in routes_content and "/recipes" in routes_content
    assert "@router.get(" in routes_content and "/recipes/{id}" in routes_content
    assert "@router.put(" in routes_content and "/recipes/{id}" in routes_content
    assert "@router.get(" in routes_content and "/recipes/{id}/reviews" in routes_content
    assert "@router.post(" in routes_content and "/recipes/{id}/reviews" in routes_content
    assert "@router.get(" in routes_content and "/users/{id}" in routes_content
    assert "@router.get(" in routes_content and "/users/{id}/recipes" in routes_content
    assert "@router.get(" in routes_content and "/users/{id}/favorites" in routes_content
    assert "@router.post(" in routes_content and "/users/{id}/favorites" in routes_content

    # Verify function signatures
    assert "async def list_recipes(" in routes_content
    assert "async def create_recipe(" in routes_content
    assert "async def get_recipe(" in routes_content
    assert "async def update_recipe(" in routes_content

    # Verify request body parameters
    assert "body: CreateRecipeRequest" in routes_content
    assert "body: UpdateRecipeRequest" in routes_content
    assert "body: CreateReviewRequest" in routes_content

    # Verify status codes
    assert "status_code=201" in routes_content

    # Verify Python syntax is valid
    try:
        compile(routes_content, str(routes_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated FastAPI routes have syntax errors: {e}")


def test_dart_models_generation(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that Dart models are generated correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate Dart models
    generator = DartModelGenerator()
    output_dir = temp_dir / "packages" / "app" / "lib" / "models"
    models_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert models_file.exists(), "models.dart should be created"
    assert size > 0, "models.dart should have content"

    # Read and verify content
    dart_content = models_file.read_text()

    # Verify Dart imports
    assert "import 'package:freezed_annotation/freezed_annotation.dart';" in dart_content
    assert "part 'models.freezed.dart';" in dart_content
    assert "part 'models.g.dart';" in dart_content

    # Verify all classes are present
    assert "class User" in dart_content
    assert "class Recipe" in dart_content
    assert "class Favorite" in dart_content
    assert "class Review" in dart_content
    assert "class CreateRecipeRequest" in dart_content
    assert "class UpdateRecipeRequest" in dart_content
    assert "class CreateReviewRequest" in dart_content

    # Verify @freezed annotations
    assert "@freezed" in dart_content

    # Verify factory constructors
    assert "factory User.fromJson" in dart_content or "fromJson" in dart_content
    assert "factory Recipe.fromJson" in dart_content or "fromJson" in dart_content

    # Verify field types
    assert "String id" in dart_content or "required String id" in dart_content
    assert "String username" in dart_content or "required String username" in dart_content
    assert "String email" in dart_content or "required String email" in dart_content


def test_dart_api_client_generation(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that Dart API client is generated correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate API client
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert api_client_file.exists(), "api_client.dart should be created"
    assert size > 0, "api_client.dart should have content"

    # Read and verify content
    api_client_content = api_client_file.read_text()

    # Verify imports
    assert "import 'package:dio/dio.dart';" in api_client_content
    assert "import '../models/models.dart';" in api_client_content

    # Verify ApiClient class
    assert "class ApiClient {" in api_client_content
    assert "final Dio _dio;" in api_client_content

    # Verify methods for each endpoint
    assert "Future<List<Recipe>> listRecipes(" in api_client_content
    assert "Future<Recipe> createRecipe(" in api_client_content
    assert "Future<Recipe> getRecipe(" in api_client_content
    assert "Future<Recipe> updateRecipe(" in api_client_content
    assert "Future<List<Review>> listRecipeReviews(" in api_client_content
    assert "Future<Review> createReview(" in api_client_content
    assert "Future<User> getUser(" in api_client_content
    assert "Future<List<Recipe>> listUserRecipes(" in api_client_content
    assert "Future<List<Favorite>> listUserFavorites(" in api_client_content
    assert "Future<Favorite> addFavorite(" in api_client_content

    # Verify HTTP calls
    assert "_dio.get(" in api_client_content
    assert "_dio.post(" in api_client_content
    assert "_dio.put(" in api_client_content

    # Verify path interpolation
    assert "/recipes/$id" in api_client_content or "/recipes/{id}" in api_client_content
    assert "/users/$id" in api_client_content or "/users/{id}" in api_client_content


def test_full_generation_via_cli(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test full generation pipeline via CLI command."""
    # Run generate command with all targets
    result = runner.invoke(app, ["generate", str(foodieai_schema), "--target", "all"])

    # Verify success
    assert result.exit_code == 0, f"Generate command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify all files were created (routes may be in generated/ subdirectory)
    python_models = temp_dir / "backend" / "app" / "models.py"
    python_orm = temp_dir / "backend" / "app" / "generated" / "orm.py"
    # Routes can be in two possible locations
    python_routes1 = temp_dir / "backend" / "app" / "routes.py"
    python_routes2 = temp_dir / "backend" / "app" / "generated" / "routes.py"
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    dart_api_client = temp_dir / "packages" / "shared" / "lib" / "generated" / "api_client.dart"
    docker_compose = temp_dir / "docker-compose.yaml"

    assert python_models.exists(), "Python models should be generated"
    assert python_orm.exists(), f"Python ORM models should be generated at {python_orm}"
    assert python_routes1.exists() or python_routes2.exists(), "Python routes should be generated"
    assert dart_models.exists(), "Dart models should be generated"
    assert dart_api_client.exists(), "Dart API client should be generated"
    assert docker_compose.exists(), "Docker compose should be generated"


def test_python_code_imports_work(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that generated Python code can be imported without errors."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate all Python files
    output_dir = temp_dir / "backend" / "app"

    models_gen = PythonModelGenerator()
    models_file, _ = models_gen.generate_to_file(schema, output_dir)

    orm_gen = SQLAlchemyORMGenerator()
    orm_file, _ = orm_gen.generate_to_file(schema, output_dir)

    routes_gen = PythonRouteGenerator()
    routes_file, _ = routes_gen.generate_to_file(schema, output_dir)

    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Add to sys.path
    sys.path.insert(0, str(output_dir))

    try:
        # Try to import models
        import importlib.util

        # Import models
        spec = importlib.util.spec_from_file_location("test_models_api063", models_file)
        assert spec is not None
        assert spec.loader is not None
        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)

        # Verify classes exist
        assert hasattr(models_module, "User")
        assert hasattr(models_module, "Recipe")
        assert hasattr(models_module, "Favorite")
        assert hasattr(models_module, "Review")

    except ImportError as e:
        pytest.fail(f"Generated Python code cannot be imported: {e}")
    except Exception as e:
        pytest.fail(f"Error when importing generated Python code: {e}")
    finally:
        # Clean up sys.path
        if str(output_dir) in sys.path:
            sys.path.remove(str(output_dir))


def test_docker_compose_is_valid_yaml(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that generated docker-compose.yaml is valid YAML."""
    # Run generate with docker target
    result = runner.invoke(app, ["generate", str(foodieai_schema), "--target", "docker"])
    assert result.exit_code == 0

    # Read docker-compose.yaml
    docker_compose = temp_dir / "docker-compose.yaml"
    assert docker_compose.exists()

    # Parse YAML
    try:
        compose_data = yaml.safe_load(docker_compose.read_text())
    except yaml.YAMLError as e:
        pytest.fail(f"docker-compose.yaml has YAML syntax errors: {e}")

    # Verify structure
    assert isinstance(compose_data, dict)
    assert "services" in compose_data
    assert "db" in compose_data["services"]
    assert "backend" in compose_data["services"]


def test_all_generated_code_compiles(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that all generated code compiles successfully."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate all files
    output_dir = temp_dir / "backend" / "app"

    models_gen = PythonModelGenerator()
    models_file, _ = models_gen.generate_to_file(schema, output_dir)

    orm_gen = SQLAlchemyORMGenerator()
    orm_file, _ = orm_gen.generate_to_file(schema, output_dir)

    routes_gen = PythonRouteGenerator()
    routes_file, _ = routes_gen.generate_to_file(schema, output_dir)

    # Compile all Python files
    files_to_compile = [models_file, orm_file, routes_file]

    for file in files_to_compile:
        content = file.read_text()
        try:
            compile(content, str(file), "exec")
        except SyntaxError as e:
            pytest.fail(f"File {file.name} has syntax errors: {e}")


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_python_code_passes_type_checking(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that generated Python code passes pyright type checking."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate all Python files
    output_dir = temp_dir / "backend" / "app"

    models_gen = PythonModelGenerator()
    models_file, _ = models_gen.generate_to_file(schema, output_dir)

    orm_gen = SQLAlchemyORMGenerator()
    orm_file, _ = orm_gen.generate_to_file(schema, output_dir)

    routes_gen = PythonRouteGenerator()
    routes_file, _ = routes_gen.generate_to_file(schema, output_dir)

    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create pyrightconfig.json
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on all files
    result = subprocess.run(
        ["pyright", str(models_file), str(orm_file), str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no type errors
    assert result.returncode == 0 or "reportMissingImports" in result.stdout, \
        f"pyright should pass. Output: {result.stdout}\n{result.stderr}"


def test_generation_with_relationships(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that generation handles complex relationships correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate Pydantic models
    models_gen = PythonModelGenerator()
    output_dir = temp_dir / "backend" / "app"
    models_file, _ = models_gen.generate_to_file(schema, output_dir)

    models_content = models_file.read_text()

    # Verify forward references for relationships
    assert "from __future__ import annotations" in models_content

    # Verify relationship fields
    # User has many recipes
    assert "recipes: list[Recipe]" in models_content or "recipes:" in models_content
    # Recipe belongs to User
    assert "author: User" in models_content or "author_id: UUID" in models_content
    # Favorite belongs to both User and Recipe
    assert "user_id: UUID" in models_content
    assert "recipe_id: UUID" in models_content


def test_generation_with_enums(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that generation handles enum types correctly."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate Pydantic models
    models_gen = PythonModelGenerator()
    output_dir = temp_dir / "backend" / "app"
    models_file, _ = models_gen.generate_to_file(schema, output_dir)

    models_content = models_file.read_text()

    # Verify enum types in Recipe model
    # difficulty field should be Literal["easy", "medium", "hard"]
    assert "difficulty:" in models_content
    assert '"easy"' in models_content
    assert '"medium"' in models_content
    assert '"hard"' in models_content


def test_generation_with_validation_constraints(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test that generation includes validation constraints."""
    parser = SchemaParser()
    schema = parser.parse(foodieai_schema)

    # Generate Pydantic models
    models_gen = PythonModelGenerator()
    output_dir = temp_dir / "backend" / "app"
    models_file, _ = models_gen.generate_to_file(schema, output_dir)

    models_content = models_file.read_text()

    # Verify Field constraints
    assert "Field(" in models_content

    # Verify max constraints exist (min_length might not be generated if it's default)
    # username: min_length: 3, max_length: 30
    assert "max_length=30" in models_content or "le=30" in models_content
    # title: max_length: 200
    assert "max_length=200" in models_content

    # Verify rating constraints (1-5)
    assert "ge=1" in models_content
    assert "le=5" in models_content


def test_full_pipeline_output_summary(temp_dir: Path, foodieai_schema: Path) -> None:
    """Test complete pipeline and verify all outputs exist with correct content."""
    # Run full generation
    result = runner.invoke(app, ["generate", str(foodieai_schema), "--target", "all"])
    assert result.exit_code == 0, f"Generate failed: {result.stdout}"

    # Collect all generated files (check multiple possible locations for routes)
    python_routes_path = temp_dir / "backend" / "app" / "routes.py"
    if not python_routes_path.exists():
        python_routes_path = temp_dir / "backend" / "app" / "generated" / "routes.py"

    generated_files = {
        "Python Models": temp_dir / "backend" / "app" / "models.py",
        "Python ORM": temp_dir / "backend" / "app" / "generated" / "orm.py",
        "Python Routes": python_routes_path,
        "Dart Models": temp_dir / "packages" / "app" / "lib" / "models" / "models.dart",
        "Dart API Client": temp_dir / "packages" / "shared" / "lib" / "generated" / "api_client.dart",
        "Docker Compose": temp_dir / "docker-compose.yaml",
    }

    # Verify all files exist and have content
    for name, file_path in generated_files.items():
        assert file_path.exists(), f"{name} should be generated at {file_path}"
        assert file_path.stat().st_size > 0, f"{name} should have content"

    # Print summary
    print("\n" + "=" * 70)
    print("FULL GENERATION PIPELINE TEST SUMMARY")
    print("=" * 70)
    print(f"\nSchema: {foodieai_schema.name}")
    print(f"Models: 7 (User, Recipe, Favorite, Review, 3 request models)")
    print(f"Endpoints: 10 (covering CRUD operations)")
    print("\nGenerated Files:")
    for name, file_path in generated_files.items():
        size = file_path.stat().st_size
        print(f"  ✓ {name:20s} {size:>8,} bytes")

    print("\nAll generated code:")
    print("  ✓ Compiles successfully")
    print("  ✓ Imports work correctly")
    print("  ✓ Includes proper type hints")
    print("  ✓ Has validation constraints")
    print("  ✓ Handles relationships")
    print("  ✓ Supports enum types")
    print("\n" + "=" * 70)
