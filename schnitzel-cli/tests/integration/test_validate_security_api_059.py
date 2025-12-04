"""Integration tests for API_059 - Validate command checks security requirements.

Test Requirements:
1. Implement security validation checks:
   - Password fields should not be exposed in API responses
   - Sensitive fields (email, phone) should have appropriate auth requirements
   - Delete endpoints should require authentication
   - Admin-only endpoints should have role restrictions
2. Add --security flag to validate command
3. Create integration test that:
   - Tests security violations are detected
   - Tests proper security configurations pass
   - Tests --security flag works

This test validates that the `schnitzel validate --security` command:
- Detects password fields that may be exposed in API responses
- Detects DELETE endpoints without authentication
- Detects endpoints with role restrictions but no authentication
- Detects endpoints returning sensitive data without authentication
- Detects mutation endpoints (POST/PUT/PATCH/DELETE) without authentication
- Provides clear, actionable error messages with recommendations
"""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_security_flag_exists(temp_dir: Path) -> None:
    """Test that the --security flag is registered and accessible."""
    # Create a minimal valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate command with --security flag
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Command should succeed (schema has no security issues)
    assert result.exit_code == 0, f"Security validation failed: {result.stdout}"


def test_security_detects_password_fields(temp_dir: Path) -> None:
    """Test that security validation detects password fields."""
    # Create a schema with a password field
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      password:
        type: string
"""
    schema_file = temp_dir / "password_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail due to password field
    assert result.exit_code == 1
    # Should mention password security issue
    assert "password" in result.stdout.lower()
    assert "security" in result.stdout.lower()


def test_security_detects_password_hash_fields(temp_dir: Path) -> None:
    """Test that security validation detects password_hash and similar fields."""
    # Create a schema with password_hash field
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      password_hash:
        type: string
"""
    schema_file = temp_dir / "hash_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail due to password_hash field
    assert result.exit_code == 1
    # Should mention password security issue
    assert "password" in result.stdout.lower()
    assert "security" in result.stdout.lower()


def test_security_detects_delete_without_auth(temp_dir: Path) -> None:
    """Test that security validation detects DELETE endpoints without authentication."""
    # Create a schema with DELETE endpoint without auth
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
  /posts/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: deletePost
      description: "Delete a post"
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "delete_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail due to DELETE without auth
    assert result.exit_code == 1
    # Should mention DELETE and authentication
    assert "delete" in result.stdout.lower()
    assert "auth" in result.stdout.lower()


def test_security_detects_roles_without_auth(temp_dir: Path) -> None:
    """Test that security validation detects endpoints with roles but no authentication."""
    # Create a schema with role restriction but no auth
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email

endpoints:
  /admin/users:
    GET:
      name: listUsers
      description: "List all users (admin only)"
      roles:
        - admin
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "roles_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail due to roles without auth
    assert result.exit_code == 1
    # Should mention role restrictions and authentication
    assert "role" in result.stdout.lower() or "admin" in result.stdout.lower()
    assert "auth" in result.stdout.lower()


def test_security_warns_mutation_without_auth(temp_dir: Path) -> None:
    """Test that security validation warns about POST/PUT/PATCH endpoints without auth."""
    # Create a schema with POST endpoint without auth
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
  /posts:
    POST:
      name: createPost
      description: "Create a new post"
      body: Post
      response:
        201:
          type: Post
"""
    schema_file = temp_dir / "mutation_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should succeed with warnings
    assert result.exit_code == 0
    # Should mention POST and authentication warning
    assert "post" in result.stdout.lower()
    assert "warning" in result.stdout.lower() or "security" in result.stdout.lower()


def test_security_warns_sensitive_data_without_auth(temp_dir: Path) -> None:
    """Test that security validation warns about endpoints returning sensitive data without auth."""
    # Create a schema with endpoint returning email without auth
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      phone:
        type: string
        format: phone

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: getUser
      description: "Get user by ID"
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "sensitive_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should succeed with warnings
    assert result.exit_code == 0
    # Should mention sensitive data warning
    assert "sensitive" in result.stdout.lower() or "email" in result.stdout.lower() or "phone" in result.stdout.lower()


def test_security_passes_with_proper_auth(temp_dir: Path) -> None:
    """Test that security validation passes with proper authentication."""
    # Create a schema with proper auth on all endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      name:
        type: string

endpoints:
  /users:
    GET:
      name: listUsers
      description: "List all users"
      auth: required
      response:
        200:
          type: User

    POST:
      name: createUser
      description: "Create a new user"
      auth: required
      body: User
      response:
        201:
          type: User

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: getUser
      description: "Get user by ID"
      auth: required
      response:
        200:
          type: User

    DELETE:
      name: deleteUser
      description: "Delete a user"
      auth: required
      response:
        204:
          type: null
"""
    schema_file = temp_dir / "secure_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should succeed
    assert result.exit_code == 0
    # Should show security passed
    assert "no security issues" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_security_passes_admin_endpoint_with_auth(temp_dir: Path) -> None:
    """Test that security validation passes for admin endpoints with proper auth."""
    # Create a schema with admin endpoint with auth
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email

endpoints:
  /admin/users:
    GET:
      name: listUsers
      description: "List all users (admin only)"
      auth: required
      roles:
        - admin
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "admin_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should succeed
    assert result.exit_code == 0


def test_security_provides_helpful_error_messages(temp_dir: Path) -> None:
    """Test that security error messages are helpful and actionable."""
    # Create a schema with multiple security issues
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      password:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: deleteUser
      description: "Delete a user"
      response:
        204:
          type: null
"""
    schema_file = temp_dir / "issues_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail
    assert result.exit_code == 1

    # Error messages should be helpful:
    # - Mention the specific issue
    # - Provide recommendations
    output = result.stdout.lower()
    assert "security" in output
    assert "password" in output or "delete" in output
    assert "recommendation" in output or "auth: required" in output


def test_security_without_flag_does_not_check(temp_dir: Path) -> None:
    """Test that security validation is not performed without --security flag."""
    # Create a schema with security issues
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      password:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: deleteUser
      response:
        204:
          type: null
"""
    schema_file = temp_dir / "insecure_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate WITHOUT --security flag
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should succeed (security not checked)
    assert result.exit_code == 0
    # Should show tip about --security flag
    assert "security" in result.stdout.lower()


def test_security_with_quiet_mode(temp_dir: Path) -> None:
    """Test that security validation works in quiet mode."""
    # Create a schema with security issue
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      password:
        type: string
"""
    schema_file = temp_dir / "quiet_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security and --quiet
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file), "--security"])

    # Should fail
    assert result.exit_code == 1
    # Output should be minimal
    assert "SECURITY_FAILED" in result.stdout or "violations" in result.stdout.lower()


def test_security_multiple_violations(temp_dir: Path) -> None:
    """Test that security validation detects multiple violations."""
    # Create a schema with multiple security issues
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      password:
        type: string
      password_hash:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: deleteUser
      response:
        204:
          type: null

  /admin/users:
    POST:
      name: createAdminUser
      roles:
        - admin
      body: User
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "multiple_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail
    assert result.exit_code == 1
    # Should mention multiple violations
    output = result.stdout.lower()
    assert "violation" in output
    # Should detect password fields
    assert "password" in output
    # Should detect DELETE without auth
    assert "delete" in output or "auth" in output


def test_security_edge_case_password_variants(temp_dir: Path) -> None:
    """Test that security validation detects various password field name patterns."""
    # Test different password field naming patterns
    password_variants = [
        "password",
        "passwd",
        "pwd",
        "password_hash",
        "hashed_password",
        "password_digest",
    ]

    for variant in password_variants:
        # Create a schema with this password variant
        schema_content = f"""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      {variant}:
        type: string
"""
        schema_file = temp_dir / f"{variant}_schema.yaml"
        schema_file.write_text(schema_content)

        # Run validate with --security
        result = runner.invoke(app, ["validate", str(schema_file), "--security"])

        # Should detect the password field
        assert result.exit_code == 1, f"Failed to detect password variant: {variant}"
        assert "password" in result.stdout.lower() or variant in result.stdout.lower()


def test_security_optional_auth_is_insecure(temp_dir: Path) -> None:
    """Test that optional auth on DELETE endpoints is flagged as insecure."""
    # Create a schema with optional auth on DELETE
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
  /posts/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: deletePost
      auth: optional
      response:
        204:
          type: null
"""
    schema_file = temp_dir / "optional_auth_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail (optional auth is not sufficient for DELETE)
    assert result.exit_code == 1
    assert "delete" in result.stdout.lower()
    assert "auth" in result.stdout.lower()


def test_security_paginated_response_sensitive_data(temp_dir: Path) -> None:
    """Test that security validation detects sensitive data in paginated responses."""
    # Create a schema with paginated response containing sensitive data
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      api_key:
        type: string

endpoints:
  /users:
    GET:
      name: listUsers
      description: "List all users"
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "paginated_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should warn about sensitive data
    assert result.exit_code == 0  # Warning, not error
    output = result.stdout.lower()
    assert "warning" in output or "sensitive" in output


def test_security_no_endpoints_passes(temp_dir: Path) -> None:
    """Test that security validation passes for schemas without endpoints."""
    # Create a schema with only models
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
      password_hash:
        type: string
"""
    schema_file = temp_dir / "no_endpoints_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --security
    result = runner.invoke(app, ["validate", str(schema_file), "--security"])

    # Should fail due to password field (even without endpoints)
    assert result.exit_code == 1
    assert "password" in result.stdout.lower()


def test_security_combined_with_strict_mode(temp_dir: Path) -> None:
    """Test that --security works together with --strict mode."""
    # Create a schema with naming warnings and security issues
    schema_content = """schnitzel: "1.0"

models:
  user_model:
    fields:
      id:
        type: uuid
        primary: true
      password:
        type: string
"""
    schema_file = temp_dir / "combined_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with both --strict and --security
    result = runner.invoke(app, ["validate", str(schema_file), "--strict", "--security"])

    # Should fail due to naming convention (--strict catches this first)
    assert result.exit_code == 1
    # Should mention naming convention issues
    assert "naming" in result.stdout.lower() or "pascalcase" in result.stdout.lower()
