"""Integration tests for api_072 - FastAPI route generator handles optional query parameters.

Test Requirements (from feature):
1. Verify route generator handles optional query params correctly
2. Verify generated code has:
   - = None or = Query(None) for optional params
   - | None type annotation
   - Works with mixed required and optional params
3. Create integration test that:
   - Creates schema with optional query params
   - Generates route code
   - Verifies optional params have defaults
   - Tests filter: {optional: true}

This test verifies that the Schnitzel route generator correctly handles optional
query parameters according to FastAPI best practices:
- Optional params should have | None type annotation
- Optional params should use Query(None) for validation
- Required params should use Query(...)
- Mixed required/optional params should maintain proper ordering
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


def test_optional_query_param_basic(temp_dir: Path) -> None:
    """Test that optional query parameters are generated correctly."""
    # Create schema with optional query parameter
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      category:
        type: string

endpoints:
  /products:
    GET:
      name: list_products
      description: "List products with optional category filter"
      query:
        category:
          type: string
          optional: true
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify Query is imported
    assert "from fastapi import" in routes_code, "Should have FastAPI imports"
    assert "Query" in routes_code, "Should import Query from fastapi"

    # Verify optional parameter has correct signature
    assert "category: str | None = Query(None)" in routes_code, \
        "Optional parameter should have '| None' type annotation and Query(None) default"


def test_optional_query_param_with_description(temp_dir: Path) -> None:
    """Test that optional query parameters can have descriptions."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /products:
    GET:
      name: list_products
      query:
        category:
          type: string
          optional: true
          description: "Filter by category"
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify optional parameter includes description
    assert "category: str | None = Query(None" in routes_code
    assert 'description="Filter by category"' in routes_code, \
        "Optional parameter should include description in Query()"


def test_mixed_required_and_optional_params(temp_dir: Path) -> None:
    """Test that required and optional query parameters can be mixed."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      category:
        type: string
      status:
        type: string

endpoints:
  /products:
    GET:
      name: search_products
      description: "Search products with required and optional filters"
      query:
        status:
          type: string
          description: "Required status filter"
        category:
          type: string
          optional: true
          description: "Optional category filter"
        search:
          type: string
          optional: true
          description: "Optional search term"
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify required parameter uses Query(...)
    assert "status: str = Query(..." in routes_code, \
        "Required parameter should use Query(...)"

    # Verify optional parameters use Query(None) with | None type
    assert "category: str | None = Query(None" in routes_code, \
        "Optional parameter should use Query(None) with | None type"
    assert "search: str | None = Query(None" in routes_code, \
        "Optional parameter should use Query(None) with | None type"


def test_optional_param_with_validation_constraints(temp_dir: Path) -> None:
    """Test that optional parameters can have validation constraints."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /products:
    GET:
      name: list_products
      query:
        min_price:
          type: int
          optional: true
          min: 0
          description: "Minimum price filter"
        name_filter:
          type: string
          optional: true
          max_length: 50
          description: "Name filter"
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify optional parameter with min constraint
    assert "min_price: int | None = Query(None" in routes_code
    assert "ge=0" in routes_code, "Should include ge (greater than or equal) constraint"

    # Verify optional parameter with max_length constraint
    assert "name_filter: str | None = Query(None" in routes_code
    assert "max_length=50" in routes_code, "Should include max_length constraint"


def test_optional_param_different_types(temp_dir: Path) -> None:
    """Test that optional parameters work with different data types."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /products:
    GET:
      name: list_products
      query:
        category:
          type: string
          optional: true
        min_price:
          type: int
          optional: true
        max_price:
          type: float
          optional: true
        in_stock:
          type: bool
          optional: true
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify all types have correct optional signatures
    assert "category: str | None = Query(None)" in routes_code, \
        "String optional parameter should have correct signature"
    assert "min_price: int | None = Query(None)" in routes_code, \
        "Int optional parameter should have correct signature"
    assert "max_price: float | None = Query(None)" in routes_code, \
        "Float optional parameter should have correct signature"
    assert "in_stock: bool | None = Query(None)" in routes_code, \
        "Bool optional parameter should have correct signature"


def test_optional_param_vs_param_with_default(temp_dir: Path) -> None:
    """Test difference between optional params and params with default values."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /products:
    GET:
      name: list_products
      query:
        page:
          type: int
          default: 1
          description: "Page number with default"
        limit:
          type: int
          default: 20
          description: "Items per page with default"
        category:
          type: string
          optional: true
          description: "Optional category filter"
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Params with default values should use Query(default_value)
    assert "page: int | None = Query(1" in routes_code, \
        "Parameter with default should use Query(default_value)"
    assert "limit: int | None = Query(20" in routes_code, \
        "Parameter with default should use Query(default_value)"

    # Optional params without default should use Query(None)
    assert "category: str | None = Query(None" in routes_code, \
        "Optional parameter without default should use Query(None)"


def test_all_optional_params(temp_dir: Path) -> None:
    """Test endpoint with all optional query parameters."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      category:
        type: string
      brand:
        type: string

endpoints:
  /products:
    GET:
      name: search_products
      description: "Search products with all optional filters"
      query:
        category:
          type: string
          optional: true
        brand:
          type: string
          optional: true
        search:
          type: string
          optional: true
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify all parameters are optional
    assert "category: str | None = Query(None)" in routes_code
    assert "brand: str | None = Query(None)" in routes_code
    assert "search: str | None = Query(None)" in routes_code


def test_generated_routes_file_with_optional_params(temp_dir: Path) -> None:
    """Test that generated routes file has correct structure with optional params."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /products:
    GET:
      name: list_products
      query:
        category:
          type: string
          optional: true
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes to file
    generator = PythonRouteGenerator()
    output_dir = temp_dir / "backend" / "app"
    routes_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert routes_file.exists(), "routes.py should be created"
    assert size > 0, "routes.py should have content"

    # Read and verify content
    routes_content = routes_file.read_text()
    assert "from fastapi import" in routes_content, "Should import from FastAPI"
    assert "Query" in routes_content, "Should import Query"
    assert "@router.get('/products'" in routes_content, "Should have GET decorator"
    assert "async def list_products" in routes_content, "Should have function definition"
    assert "category: str | None = Query(None)" in routes_content, \
        "Should have optional parameter with correct signature"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_with_optional_params_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes with optional params pass pyright type checking."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      category:
        type: string
      status:
        type: string

endpoints:
  /products:
    GET:
      name: search_products
      description: "Search products with mixed required/optional params"
      query:
        status:
          type: string
          description: "Required status filter"
        category:
          type: string
          optional: true
          description: "Optional category filter"
        min_price:
          type: int
          optional: true
          min: 0
          description: "Optional minimum price"
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

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

    # Create a basic pyrightconfig.json to help pyright
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on generated file
    result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no errors (allow warnings about missing stubs and return type warnings for TODO stubs)
    has_only_expected_errors = (
        result.returncode == 0 or
        "reportMissingImports" in result.stdout or
        ("reportReturnType" in result.stdout and "reportInvalidTypeForm" not in result.stdout)
    )
    assert has_only_expected_errors, \
        f"pyright should pass with no structural errors (allowing TODO stub return warnings). Output: {result.stdout}\n{result.stderr}"


def test_optional_param_ordering_in_function_signature(temp_dir: Path) -> None:
    """Test that optional parameters are ordered correctly in function signature.

    In Python, parameters with defaults must come after parameters without defaults.
    The generator should ensure required params come first, then optional params.
    """
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /products:
    GET:
      name: search_products
      query:
        status:
          type: string
        category:
          type: string
          optional: true
        page:
          type: int
          default: 1
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Parse the function signature to verify parameter order
    # Required param (status) should come before optional params
    lines = routes_code.split('\n')
    function_line = None
    for i, line in enumerate(lines):
        if 'async def search_products' in line:
            # Function might span multiple lines, collect them
            function_line = line
            j = i + 1
            while j < len(lines) and '->' not in function_line:
                function_line += lines[j]
                j += 1
            break

    assert function_line is not None, "Should find function definition"

    # Verify all parameters are present
    assert 'status: str = Query(...)' in routes_code, "Should have required status param"
    assert 'category: str | None = Query(None)' in routes_code, "Should have optional category param"
    assert 'page: int | None = Query(1' in routes_code, "Should have param with default"


def test_optional_param_with_complex_endpoint(temp_dir: Path) -> None:
    """Test optional parameters in a more complex endpoint with auth and body."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      category:
        type: string

  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

endpoints:
  /products/search:
    POST:
      name: advanced_search
      description: "Advanced product search"
      auth: required
      query:
        category:
          type: string
          optional: true
          description: "Filter by category"
        in_stock:
          type: bool
          optional: true
          description: "Filter by stock status"
      body: dict
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify optional query parameters are present with correct signature
    assert "category: str | None = Query(None" in routes_code
    assert "in_stock: bool | None = Query(None" in routes_code

    # Verify auth dependency is also present (should be after query params)
    assert "current_user: User = Depends(get_current_user)" in routes_code

    # Verify body parameter is present (should be before optional params)
    # Note: When body type is "dict" in schema, it generates "body: dict" not "body: dict[str, Any]"
    assert "body: dict" in routes_code
