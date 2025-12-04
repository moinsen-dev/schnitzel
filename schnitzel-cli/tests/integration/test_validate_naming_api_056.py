"""Integration test for API_056: Validate command checks naming conventions.

Test Requirements:
- Test that validate command checks model names (PascalCase)
- Test that validate command checks field names (snake_case)
- Test that validate command checks endpoint paths (kebab-case)
- Test that validate command shows warnings for violations
- Test that --strict flag treats warnings as errors
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_validate_command_exists():
    """Test that validate command is available."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate a Schnitzel schema file" in result.stdout


def test_validate_checks_model_naming_pascalcase(temp_dir: Path):
    """Test that validate checks model names are PascalCase.

    Step 1: Create schema with correct PascalCase model names
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify no warnings about model names
    """
    # Step 1: Create schema with correct model names
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  OrderItem:
    fields:
      id:
        type: uuid
        primary: true
      quantity:
        type: int
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify output indicates success
    assert "✓ Schema is valid!" in result.stdout or "OK" in result.stdout


def test_validate_detects_invalid_model_names(temp_dir: Path):
    """Test that validate detects non-PascalCase model names.

    Step 1: Create schema with invalid model name (snake_case)
    Step 2: Run schnitzel validate
    Step 3: Verify validation fails with error about model naming
    Step 4: Verify error message suggests correct name
    """
    # Step 1: Create schema with invalid model name
    schema_content = """schnitzel: "1.0"

models:
  user_profile:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation fails
    assert result.exit_code == 1, "Validation should fail for invalid model name"

    # Step 4: Verify error message
    assert "user_profile" in result.stdout
    assert "UserProfile" in result.stdout or "PascalCase" in result.stdout


def test_validate_checks_field_naming_snake_case(temp_dir: Path):
    """Test that validate checks field names are snake_case.

    Step 1: Create schema with correct snake_case field names
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify no warnings about field names
    """
    # Step 1: Create schema with correct field names
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      first_name:
        type: string
      last_name:
        type: string
      email_address:
        type: string
      created_at:
        type: datetime
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"


def test_validate_detects_invalid_field_names(temp_dir: Path):
    """Test that validate detects non-snake_case field names.

    Step 1: Create schema with invalid field name (camelCase)
    Step 2: Run schnitzel validate
    Step 3: Verify validation fails with error about field naming
    Step 4: Verify error message suggests correct name
    """
    # Step 1: Create schema with invalid field name
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      firstName:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation fails
    assert result.exit_code == 1, "Validation should fail for invalid field name"

    # Step 4: Verify error message
    assert "firstName" in result.stdout
    assert "first_name" in result.stdout or "snake_case" in result.stdout


def test_validate_checks_endpoint_paths_kebab_case(temp_dir: Path):
    """Test that validate checks endpoint paths are kebab-case.

    Step 1: Create schema with correct kebab-case endpoint paths
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify no warnings about endpoint paths
    """
    # Step 1: Create schema with correct endpoint paths
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    get: {}
  /user-profiles:
    get: {}
  /api/v1/order-items:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes (warnings don't fail by default)
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Check for no warnings
    assert "Warning" not in result.stdout or "0 warnings" in result.stdout


def test_validate_detects_invalid_endpoint_paths(temp_dir: Path):
    """Test that validate detects non-kebab-case endpoint paths.

    Step 1: Create schema with invalid endpoint path (snake_case)
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes but shows warnings
    Step 4: Verify warning message suggests correct path
    """
    # Step 1: Create schema with invalid endpoint path
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /user_profiles:
    get: {}
  /orderItems:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes (warnings don't fail by default)
    assert result.exit_code == 0, "Validation should pass but show warnings"

    # Step 4: Verify warning messages
    assert "Warning" in result.stdout or "warning" in result.stdout
    assert "/user_profiles" in result.stdout or "/orderItems" in result.stdout


def test_validate_shows_warnings_for_violations(temp_dir: Path):
    """Test that validate shows warnings for naming convention violations.

    Step 1: Create schema with endpoint naming violations
    Step 2: Run schnitzel validate
    Step 3: Verify warnings are shown
    Step 4: Verify suggestions are provided
    """
    # Step 1: Create schema with violations
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /user_profiles:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify warnings are shown
    assert "warning" in result.stdout.lower()

    # Step 4: Verify suggestions
    assert "user-profiles" in result.stdout or "kebab-case" in result.stdout


def test_validate_strict_mode_fails_on_warnings(temp_dir: Path):
    """Test that --strict flag treats warnings as errors.

    Step 1: Create schema with endpoint naming violations
    Step 2: Run schnitzel validate --strict
    Step 3: Verify validation fails
    Step 4: Verify exit code is 1
    """
    # Step 1: Create schema with violations
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /user_profiles:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate with --strict
    result = runner.invoke(app, ["validate", str(schema_file), "--strict"])

    # Step 3: Verify validation fails
    assert result.exit_code == 1, "Strict mode should fail on warnings"

    # Step 4: Verify error message
    assert "failed" in result.stdout.lower() or "FAILED" in result.stdout


def test_validate_naming_summary_in_output(temp_dir: Path):
    """Test that validate output includes naming convention summary.

    Step 1: Create valid schema
    Step 2: Run schnitzel validate
    Step 3: Verify output shows naming convention status
    Step 4: Verify summary includes model and field counts
    """
    # Step 1: Create valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Product:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify naming convention status in output
    assert "Naming Convention" in result.stdout or "naming" in result.stdout.lower()

    # Step 4: Verify counts
    assert "2" in result.stdout  # 2 models


def test_validate_multiple_naming_violations(temp_dir: Path):
    """Test that validate detects multiple naming violations.

    Step 1: Create schema with multiple violations
    Step 2: Run schnitzel validate
    Step 3: Verify all violations are reported
    Step 4: Verify warning count is correct
    """
    # Step 1: Create schema with multiple violations
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /user_profiles:
    get: {}
  /orderItems:
    get: {}
  /ProductCategories:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes with warnings
    assert result.exit_code == 0

    # Step 4: Verify multiple warnings
    output_lower = result.stdout.lower()
    assert "warning" in output_lower
    # Should have warnings for /user_profiles, /orderItems, /ProductCategories
    assert "3" in result.stdout or output_lower.count("warning") >= 3


def test_validate_quiet_mode_with_warnings(temp_dir: Path):
    """Test that quiet mode shows warning count.

    Step 1: Create schema with violations
    Step 2: Run schnitzel validate --quiet
    Step 3: Verify output shows warning count
    """
    # Step 1: Create schema with violations
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /user_profiles:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate with --quiet
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file)])

    # Step 3: Verify output shows warning count
    assert result.exit_code == 0
    assert "warning" in result.stdout.lower()


def test_validate_with_params_in_paths(temp_dir: Path):
    """Test that validate correctly handles path parameters.

    Step 1: Create schema with parameterized paths
    Step 2: Run schnitzel validate
    Step 3: Verify paths with parameters are validated correctly
    """
    # Step 1: Create schema with parameterized paths
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    get: {}
  /users/{id}/orders:
    get: {}
  /api/v1/users/{userId}/profiles:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes (these paths are correctly formatted)
    assert result.exit_code == 0
    # Should not have warnings for these paths
    assert "/users/{id}" not in (result.stdout if "Warning" in result.stdout else "")


def test_validate_comprehensive_naming_check(temp_dir: Path):
    """Test comprehensive naming convention validation.

    Step 1: Create schema with mixed valid/invalid names
    Step 2: Run schnitzel validate
    Step 3: Verify correct items pass
    Step 4: Verify incorrect items are flagged
    """
    # Step 1: Create mixed schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      user_name:
        type: string

  invalid_model:
    fields:
      id:
        type: uuid
        primary: true
      InvalidField:
        type: string

endpoints:
  /users:
    get: {}
  /user_profiles:
    get: {}
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3 & 4: Verify mixed results
    # Should fail because of invalid model and field names (errors)
    assert result.exit_code == 1
    assert "invalid_model" in result.stdout
    assert "InvalidField" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
