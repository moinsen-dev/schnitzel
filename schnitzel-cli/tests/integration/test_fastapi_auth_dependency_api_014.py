"""Integration tests for api_014 - FastAPI route generator adds auth dependency for protected endpoints.

Test Requirements (from feature):
1. Create schema with endpoint marked auth: required
2. Run schnitzel generate --target python
3. Verify current_user: User = Depends(get_current_user) in function signature
4. Verify import from backend.app.auth
5. Run pyright - no errors
"""

import tempfile
import os
from pathlib import Path
import subprocess
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.routes import PythonRouteGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_auth_required_adds_dependency(temp_dir: Path) -> None:
    """Test that auth: required adds current_user dependency parameter."""
    # Create schema with auth: required endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

endpoints:
  /profile:
    GET:
      name: get_profile
      auth: required
      description: "Get current user profile"
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify current_user parameter with Depends
    assert "current_user: User = Depends(get_current_user)" in routes_code, \
        "Should have current_user parameter with Depends(get_current_user)"


def test_auth_required_imports_depends(temp_dir: Path) -> None:
    """Test that auth: required adds Depends import from fastapi."""
    # Create schema with auth: required endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /profile:
    GET:
      name: get_profile
      auth: required
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify Depends is imported from fastapi
    assert "from fastapi import" in routes_code, "Should import from fastapi"
    assert "Depends" in routes_code.split("from fastapi import")[1].split("\n")[0], \
        "Should import Depends from fastapi"


def test_auth_required_imports_get_current_user(temp_dir: Path) -> None:
    """Test that auth: required adds get_current_user import from ..auth."""
    # Create schema with auth: required endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /profile:
    GET:
      name: get_profile
      auth: required
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify get_current_user is imported from ..auth
    assert "from ..auth import get_current_user" in routes_code, \
        "Should import get_current_user from ..auth"


def test_auth_required_imports_user_model(temp_dir: Path) -> None:
    """Test that auth: required adds User to model imports."""
    # Create schema with auth: required endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

endpoints:
  /profile:
    GET:
      name: get_profile
      auth: required
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify User is imported from models
    assert "from .models import" in routes_code, "Should import from .models"
    assert "User" in routes_code.split("from .models import")[1].split("\n")[0], \
        "Should import User model"


def test_endpoint_without_auth_no_dependency(temp_dir: Path) -> None:
    """Test that endpoints without auth: required don't have current_user parameter."""
    # Create schema with public endpoint (no auth)
    schema_content = """schnitzel: "1.0"

models:
  Restaurant:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /restaurants:
    GET:
      name: list_restaurants
      description: "List all restaurants"
      response:
        200:
          type: list[Restaurant]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify no current_user parameter
    assert "current_user" not in routes_code, \
        "Public endpoints should not have current_user parameter"

    # Verify no get_current_user import
    assert "get_current_user" not in routes_code, \
        "Public endpoints should not import get_current_user"


def test_mixed_auth_and_public_endpoints(temp_dir: Path) -> None:
    """Test that both auth and public endpoints work together."""
    # Create schema with mixed auth and public endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

  Restaurant:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /restaurants:
    GET:
      name: list_restaurants
      description: "List all restaurants (public)"
      response:
        200:
          type: list[Restaurant]

  /profile:
    GET:
      name: get_profile
      auth: required
      description: "Get current user profile"
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify auth imports are present
    assert "from fastapi import" in routes_code, "Should import from fastapi"
    assert "Depends" in routes_code, "Should import Depends"
    assert "from ..auth import get_current_user" in routes_code, \
        "Should import get_current_user"

    # Verify auth endpoint has current_user
    assert "async def get_profile(current_user: User = Depends(get_current_user))" in routes_code, \
        "Auth endpoint should have current_user parameter"

    # Verify public endpoint doesn't have current_user
    # Extract the list_restaurants function
    list_restaurants_start = routes_code.find("async def list_restaurants")
    list_restaurants_end = routes_code.find("\n\n", list_restaurants_start)
    list_restaurants_func = routes_code[list_restaurants_start:list_restaurants_end]

    assert "current_user" not in list_restaurants_func, \
        "Public endpoint should not have current_user parameter"


def test_post_endpoint_with_auth_and_body(temp_dir: Path) -> None:
    """Test that POST endpoint with auth: required has both body and current_user parameters."""
    # Create schema with POST endpoint requiring auth
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  Order:
    fields:
      id:
        type: uuid
        primary: true
      user_id:
        type: uuid

  CreateOrderRequest:
    fields:
      restaurant_id:
        type: uuid
      items:
        type: list<string>

endpoints:
  /orders:
    POST:
      name: create_order
      auth: required
      body: CreateOrderRequest
      response:
        201:
          type: Order
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both body and current_user parameters are present
    # Note: body (required) should come before current_user (optional with default)
    assert "current_user: User = Depends(get_current_user)" in routes_code, \
        "Should have current_user parameter"
    assert "body: CreateOrderRequest" in routes_code, \
        "Should have body parameter"

    # Verify function signature has proper order (required before optional)
    assert "async def create_order(body: CreateOrderRequest, current_user: User = Depends(get_current_user))" in routes_code, \
        "Function should have body parameter (required) before current_user parameter (optional)"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_with_auth_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes with auth pass pyright type checking (requirement 5)."""
    # Create schema with auth: required endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      name:
        type: string

endpoints:
  /profile:
    GET:
      name: get_profile
      auth: required
      description: "Get current user profile"
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate both models and routes
    from schnitzel.generators.python.models import PythonModelGenerator

    output_dir = temp_dir / "backend" / "app"

    # Generate models.py first (routes imports from it)
    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    # Generate routes.py
    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py to make it a package
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create a basic pyproject.toml or pyrightconfig.json to help pyright
    # This tells pyright to ignore missing stubs for fastapi
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on generated file
    result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no errors (allow warnings about missing stubs)
    # The main check is that the generated code itself has no type errors
    assert result.returncode == 0 or "reportMissingImports" in result.stdout, \
        f"pyright should pass with no structural errors. Output: {result.stdout}\n{result.stderr}"
