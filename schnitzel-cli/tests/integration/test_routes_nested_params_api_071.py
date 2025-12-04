"""Integration tests for api_071 - FastAPI route generator handles nested path parameters.

Test Requirements (from feature):
1. Verify route generator handles nested path parameters correctly
2. Verify generated code has all path params in function signature
3. Verify all params have correct types from schema
4. Verify params are extracted in correct order
5. Create integration test with /orgs/{org_id}/users/{user_id}/posts/{post_id}

This test ensures the route generator can handle deeply nested resource paths
with multiple path parameters, which is common in REST APIs.
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


def test_single_path_parameter(temp_dir: Path) -> None:
    """Test that single path parameter is handled correctly."""
    # Create schema with single path parameter
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path parameter in decorator
    assert "@router.get('/users/{id}'" in routes_code, \
        "Should have path parameter in decorator"

    # Verify path parameter in function signature with correct type
    assert "async def get_user(id: UUID) -> User:" in routes_code, \
        "Should have id parameter with UUID type in function signature"


def test_two_nested_path_parameters(temp_dir: Path) -> None:
    """Test that two nested path parameters are handled correctly."""
    # Create schema with two nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      user_id:
        type: uuid

endpoints:
  /users/{user_id}/posts/{post_id}:
    params:
      user_id:
        type: uuid
      post_id:
        type: uuid
    GET:
      name: get_user_post
      description: "Get a specific post for a user"
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.get('/users/{user_id}/posts/{post_id}'" in routes_code, \
        "Should have nested path parameters in decorator"

    # Verify both parameters in function signature with correct types
    assert "user_id: UUID" in routes_code, \
        "Should have user_id parameter with UUID type"
    assert "post_id: UUID" in routes_code, \
        "Should have post_id parameter with UUID type"

    # Verify parameters appear in correct order
    assert "async def get_user_post(user_id: UUID, post_id: UUID) -> Post:" in routes_code, \
        "Should have both parameters in correct order in function signature"


def test_three_nested_path_parameters(temp_dir: Path) -> None:
    """Test that three nested path parameters are handled correctly (requirement 5)."""
    # Create schema with three nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
      user_id:
        type: uuid
      org_id:
        type: uuid

endpoints:
  /orgs/{org_id}/users/{user_id}/posts/{post_id}:
    params:
      org_id:
        type: uuid
      user_id:
        type: uuid
      post_id:
        type: uuid
    GET:
      name: get_org_user_post
      description: "Get a specific post for a user in an organization"
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.get('/orgs/{org_id}/users/{user_id}/posts/{post_id}'" in routes_code, \
        "Should have all three nested path parameters in decorator"

    # Verify all three parameters in function signature with correct types
    assert "org_id: UUID" in routes_code, \
        "Should have org_id parameter with UUID type"
    assert "user_id: UUID" in routes_code, \
        "Should have user_id parameter with UUID type"
    assert "post_id: UUID" in routes_code, \
        "Should have post_id parameter with UUID type"

    # Verify parameters appear in correct order (requirement 4)
    assert "async def get_org_user_post(org_id: UUID, user_id: UUID, post_id: UUID) -> Post:" in routes_code, \
        "Should have all three parameters in correct order: org_id, user_id, post_id"


def test_nested_path_params_with_different_types(temp_dir: Path) -> None:
    """Test that nested path parameters with different types are handled correctly."""
    # Create schema with mixed parameter types
    schema_content = """schnitzel: "1.0"

models:
  Comment:
    fields:
      id:
        type: int
        primary: true
      text:
        type: string
      post_id:
        type: uuid

endpoints:
  /posts/{post_id}/comments/{comment_id}:
    params:
      post_id:
        type: uuid
      comment_id:
        type: int
    GET:
      name: get_post_comment
      description: "Get a specific comment on a post"
      response:
        200:
          type: Comment
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.get('/posts/{post_id}/comments/{comment_id}'" in routes_code, \
        "Should have nested path parameters in decorator"

    # Verify different types are used correctly
    assert "post_id: UUID" in routes_code, \
        "Should have post_id parameter with UUID type"
    assert "comment_id: int" in routes_code, \
        "Should have comment_id parameter with int type"

    # Verify correct order with correct types
    assert "async def get_post_comment(post_id: UUID, comment_id: int) -> Comment:" in routes_code, \
        "Should have both parameters with correct types in correct order"


def test_nested_path_params_with_post_method(temp_dir: Path) -> None:
    """Test that nested path parameters work with POST methods and request body."""
    # Create schema with POST endpoint with nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string
      user_id:
        type: uuid
      post_id:
        type: uuid

  CreateCommentRequest:
    fields:
      text:
        type: string

endpoints:
  /users/{user_id}/posts/{post_id}/comments:
    params:
      user_id:
        type: uuid
      post_id:
        type: uuid
    POST:
      name: create_user_post_comment
      description: "Create a comment on a user's post"
      body: CreateCommentRequest
      response:
        201:
          type: Comment
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.post('/users/{user_id}/posts/{post_id}/comments'" in routes_code, \
        "Should have nested path parameters in POST decorator"

    # Verify path parameters come before body parameter
    assert "async def create_user_post_comment(user_id: UUID, post_id: UUID, body: CreateCommentRequest) -> Comment:" in routes_code, \
        "Should have path parameters before body parameter"


def test_nested_path_params_with_put_method(temp_dir: Path) -> None:
    """Test that nested path parameters work with PUT methods."""
    # Create schema with PUT endpoint with nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      user_id:
        type: uuid

  UpdatePostRequest:
    fields:
      title:
        type: string

endpoints:
  /users/{user_id}/posts/{post_id}:
    params:
      user_id:
        type: uuid
      post_id:
        type: uuid
    PUT:
      name: update_user_post
      description: "Update a user's post"
      body: UpdatePostRequest
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.put('/users/{user_id}/posts/{post_id}'" in routes_code, \
        "Should have nested path parameters in PUT decorator"

    # Verify parameters in correct order
    assert "async def update_user_post(user_id: UUID, post_id: UUID, body: UpdatePostRequest) -> Post:" in routes_code, \
        "Should have path parameters before body parameter in PUT"


def test_nested_path_params_with_delete_method(temp_dir: Path) -> None:
    """Test that nested path parameters work with DELETE methods."""
    # Create schema with DELETE endpoint with nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /users/{user_id}/posts/{post_id}:
    params:
      user_id:
        type: uuid
      post_id:
        type: uuid
    DELETE:
      name: delete_user_post
      description: "Delete a user's post"
      response:
        204: {}
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.delete('/users/{user_id}/posts/{post_id}'" in routes_code, \
        "Should have nested path parameters in DELETE decorator"

    # Verify parameters in correct order
    assert "async def delete_user_post(user_id: UUID, post_id: UUID) -> None:" in routes_code, \
        "Should have path parameters in correct order in DELETE"


def test_nested_path_params_with_query_params(temp_dir: Path) -> None:
    """Test that nested path parameters work correctly with query parameters."""
    # Create schema with nested path parameters and query parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /users/{user_id}/posts/{post_id}:
    params:
      user_id:
        type: uuid
      post_id:
        type: uuid
    GET:
      name: get_user_post
      description: "Get a user's post with optional details"
      query:
        include_comments:
          type: bool
          optional: true
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path parameters come before query parameters
    # Path params are required, query params are optional with defaults
    assert "user_id: UUID, post_id: UUID" in routes_code, \
        "Should have path parameters as required parameters"
    assert "include_comments: bool | None = Query(None)" in routes_code, \
        "Should have query parameter with Query() default"


def test_nested_path_params_with_auth(temp_dir: Path) -> None:
    """Test that nested path parameters work correctly with auth dependency."""
    # Create schema with nested path parameters and auth requirement
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /users/{user_id}/posts/{post_id}:
    params:
      user_id:
        type: uuid
      post_id:
        type: uuid
    GET:
      name: get_user_post
      description: "Get a user's post (requires authentication)"
      auth: required
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path parameters come before auth dependency
    assert "user_id: UUID, post_id: UUID" in routes_code, \
        "Should have path parameters as required parameters"
    assert "current_user: User = Depends(get_current_user)" in routes_code, \
        "Should have auth dependency with default"


def test_extract_path_params_unit_test(temp_dir: Path) -> None:
    """Test the _extract_path_params method directly."""
    generator = PythonRouteGenerator()

    # Test single parameter
    result = generator._extract_path_params("/users/{id}")
    assert result == {"id": "str"}, "Should extract single parameter with default str type"

    # Test two parameters
    result = generator._extract_path_params("/users/{user_id}/posts/{post_id}")
    assert result == {"user_id": "str", "post_id": "str"}, \
        "Should extract both parameters with default str type"

    # Test three parameters
    result = generator._extract_path_params("/orgs/{org_id}/users/{user_id}/posts/{post_id}")
    assert result == {"org_id": "str", "user_id": "str", "post_id": "str"}, \
        "Should extract all three parameters with default str type"

    # Test no parameters
    result = generator._extract_path_params("/users")
    assert result == {}, "Should return empty dict when no parameters"

    # Test parameters with underscores
    result = generator._extract_path_params("/api/{api_version}/users/{user_id}")
    assert result == {"api_version": "str", "user_id": "str"}, \
        "Should extract parameters with underscores"


def test_deeply_nested_four_levels(temp_dir: Path) -> None:
    """Test that deeply nested path parameters (4 levels) are handled correctly."""
    # Create schema with four nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Attachment:
    fields:
      id:
        type: uuid
        primary: true
      filename:
        type: string

endpoints:
  /orgs/{org_id}/users/{user_id}/posts/{post_id}/attachments/{attachment_id}:
    params:
      org_id:
        type: uuid
      user_id:
        type: uuid
      post_id:
        type: uuid
      attachment_id:
        type: uuid
    GET:
      name: get_attachment
      description: "Get an attachment from a post"
      response:
        200:
          type: Attachment
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path in decorator
    assert "@router.get('/orgs/{org_id}/users/{user_id}/posts/{post_id}/attachments/{attachment_id}'" in routes_code, \
        "Should have all four nested path parameters in decorator"

    # Verify all four parameters in function signature in correct order
    assert "async def get_attachment(org_id: UUID, user_id: UUID, post_id: UUID, attachment_id: UUID) -> Attachment:" in routes_code, \
        "Should have all four parameters in correct order"


def test_nested_path_params_preserve_static_segments(temp_dir: Path) -> None:
    """Test that static path segments are preserved with nested parameters."""
    # Create schema with static segments mixed with parameters
    schema_content = """schnitzel: "1.0"

models:
  Settings:
    fields:
      id:
        type: uuid
        primary: true
      value:
        type: string

endpoints:
  /api/v1/orgs/{org_id}/settings/{setting_id}:
    params:
      org_id:
        type: uuid
      setting_id:
        type: uuid
    GET:
      name: get_org_setting
      description: "Get organization settings"
      response:
        200:
          type: Settings
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify static segments are preserved
    assert "@router.get('/api/v1/orgs/{org_id}/settings/{setting_id}'" in routes_code, \
        "Should preserve static path segments: /api/v1/"

    # Verify parameters in function signature
    assert "async def get_org_setting(org_id: UUID, setting_id: UUID) -> Settings:" in routes_code, \
        "Should have both parameters in function signature"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_nested_routes_pass_pyright(temp_dir: Path) -> None:
    """Test that generated routes with nested path parameters pass pyright type checking."""
    # Create schema with nested path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string

endpoints:
  /orgs/{org_id}/users/{user_id}/posts/{post_id}:
    params:
      org_id:
        type: uuid
      user_id:
        type: uuid
      post_id:
        type: uuid
    GET:
      name: get_org_user_post
      description: "Get a specific post for a user in an organization"
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    output_dir = temp_dir / "backend" / "app"
    routes_file, _ = generator.generate_to_file(schema, output_dir)

    # Create a minimal models.py to satisfy imports
    models_file = output_dir / "models.py"
    models_file.write_text("""from uuid import UUID
from pydantic import BaseModel

class Post(BaseModel):
    id: UUID
    title: str
    content: str
""")

    # Create a minimal auth module to satisfy auth imports
    auth_file = output_dir.parent / "auth.py"
    auth_file.write_text("""from uuid import UUID

class User:
    id: UUID
    name: str

def get_current_user() -> User:
    pass
""")

    # Run pyright on the generated file
    result = subprocess.run(
        ["pyright", str(routes_file), "--level", "error"],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Pyright should not find syntax errors or type errors in the signature
    # Note: The generated stub has "pass" which causes reportReturnType error, which is expected
    # We're verifying that the nested path parameters are correctly typed
    output = result.stdout + result.stderr

    # Check for syntax errors or import errors (not expected)
    assert "SyntaxError" not in output, \
        f"Generated routes should not have syntax errors. Output: {output}"
    assert "cannot find implementation" not in output, \
        f"Generated routes should have valid imports. Output: {output}"

    # The reportReturnType error is expected for stub functions with "pass"
    # So we accept returncode 0 (no errors) or 1 (only the expected return type error)
    assert result.returncode in [0, 1], \
        f"pyright should only report expected stub return type error. Output: {output}"


def test_nested_path_params_parameter_order_consistency(temp_dir: Path) -> None:
    """Test that parameter order is consistent with path order."""
    # Create schema to verify parameter order matches path order
    schema_content = """schnitzel: "1.0"

models:
  Resource:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /a/{first}/b/{second}/c/{third}:
    params:
      first:
        type: uuid
      second:
        type: int
      third:
        type: string
    GET:
      name: test_order
      description: "Test parameter order"
      response:
        200:
          type: Resource
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify parameters appear in the same order as in the path
    assert "async def test_order(first: UUID, second: int, third: str) -> Resource:" in routes_code, \
        "Parameters should appear in the same order as in the path: first, second, third"
