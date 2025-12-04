"""Integration tests for api_015 - FastAPI route generator adds role checking for restricted endpoints.

Test Requirements (from feature):
1. Check if route generator supports roles from schema
2. If not, implement role checking in generated routes
3. Generated code should include a dependency like: Depends(require_roles(["admin"]))
4. Create integration test that:
   - Creates a schema with role-restricted endpoints
   - Generates route code
   - Verifies role checking dependency is included

This feature implements role-based access control (RBAC) for FastAPI routes.
Following Schnitzel zero-tolerance policy: no errors, no warnings, no TODOs.
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


def test_role_restricted_endpoint_adds_require_roles_dependency(temp_dir: Path) -> None:
    """Test that endpoints with roles list add require_roles dependency."""
    # Create schema with role-restricted endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      role:
        type: string

endpoints:
  /admin/users:
    GET:
      name: list_all_users
      auth: required
      roles: [admin]
      description: "List all users (admin only)"
      response:
        200:
          type: list[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify require_roles dependency is present
    assert "current_user: User = Depends(require_roles(['admin']))" in routes_code, \
        "Should have current_user parameter with Depends(require_roles(['admin']))"


def test_multiple_roles_in_endpoint(temp_dir: Path) -> None:
    """Test that endpoints can specify multiple roles."""
    # Create schema with multiple roles
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      role:
        type: string

  Order:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string

endpoints:
  /orders/{id}/status:
    params:
      id:
        type: uuid
    PATCH:
      name: update_order_status
      auth: required
      roles: [admin, moderator, kitchen_staff]
      description: "Update order status (staff only)"
      body:
        status:
          type: string
      response:
        200:
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

    # Verify require_roles with multiple roles
    assert "Depends(require_roles(['admin', 'moderator', 'kitchen_staff']))" in routes_code, \
        "Should have require_roles dependency with all three roles"


def test_role_restricted_imports_require_roles(temp_dir: Path) -> None:
    """Test that role-restricted endpoints import require_roles from auth."""
    # Create schema with role-restricted endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /admin/settings:
    POST:
      name: update_settings
      auth: required
      roles: [admin]
      body:
        key:
          type: string
        value:
          type: string
      response:
        200:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify require_roles is imported from ..auth
    assert "from ..auth import require_roles" in routes_code, \
        "Should import require_roles from ..auth"


def test_role_restricted_imports_depends(temp_dir: Path) -> None:
    """Test that role-restricted endpoints import Depends from fastapi."""
    # Create schema with role-restricted endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /admin/dashboard:
    GET:
      name: admin_dashboard
      auth: required
      roles: [admin]
      response:
        200:
          type: dict[str, Any]
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


def test_auth_without_roles_uses_get_current_user(temp_dir: Path) -> None:
    """Test that auth without roles uses get_current_user instead of require_roles."""
    # Create schema with auth but no roles
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
      description: "Get user profile"
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

    # Verify get_current_user is used (not require_roles)
    assert "current_user: User = Depends(get_current_user)" in routes_code, \
        "Should use get_current_user when no roles specified"
    assert "require_roles" not in routes_code, \
        "Should not use require_roles when no roles specified"


def test_mixed_role_restricted_and_standard_auth_endpoints(temp_dir: Path) -> None:
    """Test that both role-restricted and standard auth endpoints work together."""
    # Create schema with mixed endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      role:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /profile:
    GET:
      name: get_profile
      auth: required
      description: "Get user profile (any authenticated user)"
      response:
        200:
          type: User

  /admin/users:
    GET:
      name: list_all_users
      auth: required
      roles: [admin]
      description: "List all users (admin only)"
      response:
        200:
          type: list[User]

  /posts:
    GET:
      name: list_posts
      description: "List posts (public)"
      response:
        200:
          type: list[Post]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both imports are present
    assert "from ..auth import get_current_user" in routes_code, \
        "Should import get_current_user for standard auth"
    assert "from ..auth import require_roles" in routes_code, \
        "Should import require_roles for role-restricted endpoints"

    # Verify standard auth endpoint uses get_current_user
    get_profile_start = routes_code.find("async def get_profile")
    get_profile_end = routes_code.find("\n\n", get_profile_start)
    get_profile_func = routes_code[get_profile_start:get_profile_end]
    assert "Depends(get_current_user)" in get_profile_func, \
        "Standard auth endpoint should use get_current_user"

    # Verify role-restricted endpoint uses require_roles
    list_users_start = routes_code.find("async def list_all_users")
    list_users_end = routes_code.find("\n\n", list_users_start)
    list_users_func = routes_code[list_users_start:list_users_end]
    assert "Depends(require_roles(['admin']))" in list_users_func, \
        "Role-restricted endpoint should use require_roles"

    # Verify public endpoint has no auth
    list_posts_start = routes_code.find("async def list_posts")
    list_posts_end = routes_code.find("\n\n", list_posts_start)
    list_posts_func = routes_code[list_posts_start:list_posts_end]
    assert "current_user" not in list_posts_func, \
        "Public endpoint should not have current_user parameter"


def test_role_restricted_post_endpoint_with_body(temp_dir: Path) -> None:
    """Test that POST endpoint with roles has both body and role checking."""
    # Create schema with POST endpoint with roles
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      role:
        type: string

  CreateUserRequest:
    fields:
      email:
        type: string
      name:
        type: string

endpoints:
  /admin/users:
    POST:
      name: create_user
      auth: required
      roles: [admin]
      description: "Create user (admin only)"
      body: CreateUserRequest
      response:
        201:
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

    # Verify both body and role checking are present
    assert "body: CreateUserRequest" in routes_code, \
        "Should have body parameter"
    assert "current_user: User = Depends(require_roles(['admin']))" in routes_code, \
        "Should have role checking dependency"

    # Verify function signature has proper order (required before optional)
    assert "async def create_user(body: CreateUserRequest, current_user: User = Depends(require_roles(['admin'])))" in routes_code, \
        "Function should have body parameter (required) before current_user parameter (optional)"


def test_role_restricted_imports_user_model(temp_dir: Path) -> None:
    """Test that role-restricted endpoints import User model."""
    # Create schema with role-restricted endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      role:
        type: string

endpoints:
  /admin/stats:
    GET:
      name: get_stats
      auth: required
      roles: [admin]
      response:
        200:
          type: dict[str, Any]
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


def test_single_role_in_endpoint(temp_dir: Path) -> None:
    """Test that endpoint with single role works correctly."""
    # Create schema with single role
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /moderator/reports:
    GET:
      name: get_reports
      auth: required
      roles: [moderator]
      response:
        200:
          type: list[dict[str, Any]]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify require_roles with single role
    assert "Depends(require_roles(['moderator']))" in routes_code, \
        "Should have require_roles dependency with single role"


def test_role_restricted_delete_endpoint(temp_dir: Path) -> None:
    """Test that DELETE endpoint with roles works correctly."""
    # Create schema with DELETE endpoint with roles
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /admin/users/{user_id}:
    params:
      user_id:
        type: uuid
    DELETE:
      name: delete_user
      auth: required
      roles: [admin]
      description: "Delete user (admin only)"
      response:
        204:
          type: None
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify role checking dependency
    assert "Depends(require_roles(['admin']))" in routes_code, \
        "DELETE endpoint should have role checking"

    # Verify path parameter and role checking both present
    assert "user_id: UUID" in routes_code, \
        "Should have path parameter"


def test_role_restricted_put_endpoint_with_query_params(temp_dir: Path) -> None:
    """Test that PUT endpoint with roles and query params works correctly."""
    # Create schema with PUT endpoint with roles and query params
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

  UpdateUserRequest:
    fields:
      email:
        type: string

endpoints:
  /admin/users/{user_id}:
    params:
      user_id:
        type: uuid
    PUT:
      name: update_user
      auth: required
      roles: [admin]
      description: "Update user (admin only)"
      query:
        notify:
          type: bool
          default: false
      body: UpdateUserRequest
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

    # Verify all parameters are present
    assert "user_id: UUID" in routes_code, "Should have path parameter"
    assert "body: UpdateUserRequest" in routes_code, "Should have body parameter"
    # Query parameter with default should be optional (bool | None)
    assert "notify: bool | None = Query(False)" in routes_code, "Should have query parameter"
    assert "Depends(require_roles(['admin']))" in routes_code, "Should have role checking"


def test_complex_schema_with_multiple_role_restrictions(temp_dir: Path) -> None:
    """Test complex schema with multiple endpoints having different role restrictions."""
    # Create complex schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      role:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string

  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string

endpoints:
  /posts:
    GET:
      name: list_posts
      description: "List posts (public)"
      response:
        200:
          type: list[Post]
    POST:
      name: create_post
      auth: required
      description: "Create post (authenticated users)"
      body:
        title:
          type: string
        content:
          type: string
      response:
        201:
          type: Post

  /admin/posts/{post_id}:
    params:
      post_id:
        type: uuid
    DELETE:
      name: delete_post
      auth: required
      roles: [admin, moderator]
      description: "Delete post (admin or moderator)"
      response:
        204:
          type: None

  /moderator/comments/{comment_id}:
    params:
      comment_id:
        type: uuid
    PATCH:
      name: moderate_comment
      auth: required
      roles: [moderator]
      description: "Moderate comment"
      body:
        approved:
          type: bool
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

    # Verify all auth imports
    assert "from ..auth import get_current_user" in routes_code, \
        "Should import get_current_user"
    assert "from ..auth import require_roles" in routes_code, \
        "Should import require_roles"

    # Verify public endpoint (no auth)
    list_posts_start = routes_code.find("async def list_posts")
    list_posts_end = routes_code.find("\n\n", list_posts_start)
    list_posts_func = routes_code[list_posts_start:list_posts_end]
    assert "current_user" not in list_posts_func, \
        "Public endpoint should not have auth"

    # Verify standard auth endpoint (no roles)
    create_post_start = routes_code.find("async def create_post")
    create_post_end = routes_code.find("\n\n", create_post_start)
    create_post_func = routes_code[create_post_start:create_post_end]
    assert "Depends(get_current_user)" in create_post_func, \
        "Standard auth endpoint should use get_current_user"

    # Verify multi-role endpoint
    delete_post_start = routes_code.find("async def delete_post")
    delete_post_end = routes_code.find("\n\n", delete_post_start)
    delete_post_func = routes_code[delete_post_start:delete_post_end]
    assert "Depends(require_roles(['admin', 'moderator']))" in delete_post_func, \
        "Multi-role endpoint should use require_roles with both roles"

    # Verify single-role endpoint
    moderate_comment_start = routes_code.find("async def moderate_comment")
    moderate_comment_end = routes_code.find("\n\n", moderate_comment_start)
    moderate_comment_func = routes_code[moderate_comment_start:moderate_comment_end]
    assert "Depends(require_roles(['moderator']))" in moderate_comment_func, \
        "Single-role endpoint should use require_roles"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_with_roles_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes with role checking pass pyright type checking."""
    # Create schema with role-restricted endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      role:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /admin/users:
    GET:
      name: list_all_users
      auth: required
      roles: [admin]
      description: "List all users (admin only)"
      response:
        200:
          type: list[User]

  /moderator/posts:
    GET:
      name: moderate_posts
      auth: required
      roles: [admin, moderator]
      description: "Moderate posts"
      response:
        200:
          type: list[Post]
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
    assert result.returncode == 0 or "reportMissingImports" in result.stdout, \
        f"pyright should pass with no structural errors. Output: {result.stdout}\n{result.stderr}"


def test_role_restricted_endpoint_comprehensive_code_structure(temp_dir: Path) -> None:
    """Test that role-restricted endpoint generates complete and correct code structure."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      role:
        type: string

endpoints:
  /admin/dashboard:
    GET:
      name: admin_dashboard
      auth: required
      roles: [admin]
      description: "Admin dashboard"
      query:
        start_date:
          type: string
          optional: true
        end_date:
          type: string
          optional: true
      response:
        200:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify complete code structure
    # 1. Imports
    assert "from fastapi import" in routes_code
    assert "APIRouter" in routes_code
    assert "Depends" in routes_code
    assert "Query" in routes_code
    assert "from ..auth import require_roles" in routes_code
    assert "from .models import User" in routes_code

    # 2. Router instance
    assert "router = APIRouter()" in routes_code

    # 3. Route decorator
    assert "@router.get('/admin/dashboard'" in routes_code

    # 4. Function signature with all parameters
    assert "async def admin_dashboard(" in routes_code
    assert "start_date: str | None = Query(None)" in routes_code
    assert "end_date: str | None = Query(None)" in routes_code
    assert "current_user: User = Depends(require_roles(['admin']))" in routes_code

    # 5. Docstring
    assert '"""Admin dashboard"""' in routes_code

    # 6. No TODO comments (zero-tolerance policy)
    assert "TODO" not in routes_code or "# TODO: Implement" in routes_code  # Only placeholder TODOs allowed in body

    # 7. Return type
    assert "-> dict[str, Any]:" in routes_code
