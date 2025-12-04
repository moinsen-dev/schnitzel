"""Integration tests for F093 - CLI has --quiet flag for minimal output.

Test Requirements:
- test_quiet_flag_accepted - --quiet flag is recognized
- test_quiet_shows_less_output - quiet mode shows minimal output
- test_quiet_short_flag - -q should work as short form
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
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_quiet_flag_accepted(temp_dir: Path) -> None:
    """Test that --quiet flag is recognized and accepted by the CLI."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate command with --quiet flag
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file)])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed with --quiet: {result.stdout}"

    # Verify output exists but is minimal
    assert len(result.stdout) > 0, "Should have some output even in quiet mode"


def test_quiet_shows_less_output(temp_dir: Path) -> None:
    """Test that quiet mode shows significantly less output than normal mode."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
  Post:
    description: "A blog post"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate command without quiet mode
    result_normal = runner.invoke(app, ["validate", str(schema_file)])
    assert result_normal.exit_code == 0, f"Normal command failed: {result_normal.stdout}"

    # Run validate command with quiet mode
    result_quiet = runner.invoke(app, ["--quiet", "validate", str(schema_file)])
    assert result_quiet.exit_code == 0, f"Quiet command failed: {result_quiet.stdout}"

    # Verify quiet mode has less output
    normal_lines = len(result_normal.stdout.strip().split('\n'))
    quiet_lines = len(result_quiet.stdout.strip().split('\n'))

    assert quiet_lines < normal_lines, (
        f"Quiet mode should have fewer lines than normal mode. "
        f"Normal: {normal_lines}, Quiet: {quiet_lines}"
    )

    # Verify quiet mode has minimal output (just "OK" or similar)
    assert quiet_lines <= 3, f"Quiet mode should have very few lines, got {quiet_lines}"

    # Normal mode should contain verbose information
    assert "Models defined" in result_normal.stdout or "User" in result_normal.stdout, (
        "Normal mode should show model details"
    )

    # Quiet mode should not contain verbose information
    assert "Models defined" not in result_quiet.stdout, (
        "Quiet mode should not show verbose model details"
    )


def test_quiet_short_flag(temp_dir: Path) -> None:
    """Test that -q works as short form of --quiet."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "A product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate command with -q flag
    result_short = runner.invoke(app, ["-q", "validate", str(schema_file)])

    # Run validate command with --quiet flag
    result_long = runner.invoke(app, ["--quiet", "validate", str(schema_file)])

    # Both should succeed
    assert result_short.exit_code == 0, f"Command failed with -q: {result_short.stdout}"
    assert result_long.exit_code == 0, f"Command failed with --quiet: {result_long.stdout}"

    # Both should produce similar minimal output
    assert len(result_short.stdout.strip()) < 100, "Short flag should produce minimal output"
    assert len(result_long.stdout.strip()) < 100, "Long flag should produce minimal output"

    # Output should be similar between short and long forms
    short_lines = len(result_short.stdout.strip().split('\n'))
    long_lines = len(result_long.stdout.strip().split('\n'))
    assert short_lines == long_lines, (
        f"-q and --quiet should produce same amount of output. "
        f"-q: {short_lines} lines, --quiet: {long_lines} lines"
    )


def test_quiet_with_generate_command(temp_dir: Path) -> None:
    """Test that --quiet flag works with generate command."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with --quiet flag and --dry-run (to avoid actually creating files)
    result = runner.invoke(app, ["--quiet", "generate", str(schema_file), "--dry-run"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Generate command failed with --quiet: {result.stdout}"

    # Verify output is minimal
    output_lines = len(result.stdout.strip().split('\n'))
    assert output_lines <= 3, (
        f"Quiet mode should have minimal output, got {output_lines} lines"
    )

    # Should not contain verbose progress information
    assert "Parsing schema" not in result.stdout, "Should not show parsing progress"
    assert "Validating schema" not in result.stdout, "Should not show validation progress"
    assert "Models validated" not in result.stdout, "Should not show model details"


def test_quiet_with_init_command(temp_dir: Path) -> None:
    """Test that --quiet flag works with init command."""
    project_name = "test_project_quiet"

    # Run init command with --quiet flag
    result = runner.invoke(app, ["--quiet", "init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Init command failed with --quiet: {result.stdout}"

    # Verify project was created
    project_path = temp_dir / project_name
    assert project_path.exists(), "Project directory should be created"
    assert (project_path / "schema.schnitzel.yaml").exists(), "Schema file should be created"

    # Verify output is minimal
    output_lines = len(result.stdout.strip().split('\n'))
    assert output_lines <= 3, (
        f"Quiet mode should have minimal output, got {output_lines} lines"
    )

    # Should not contain verbose creation information
    assert "Creating project" not in result.stdout, "Should not show verbose creation info"
    assert "Next steps" not in result.stdout, "Should not show next steps in quiet mode"


def test_quiet_flag_with_errors(temp_dir: Path) -> None:
    """Test that errors are still shown even in quiet mode."""
    # Create an invalid schema file with unsupported field type
    invalid_schema = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid field type"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type_xyz
"""
    schema_file = temp_dir / "invalid_schema.yaml"
    schema_file.write_text(invalid_schema)

    # Run generate command with --quiet flag (generate validates the schema)
    result = runner.invoke(app, ["--quiet", "generate", str(schema_file)])

    # Verify command failed
    assert result.exit_code == 1, f"Command should fail with invalid schema. Output: {result.stdout}"

    # Verify error message is still shown (errors should always be displayed)
    assert "Schema validation failed" in result.stdout or "error" in result.stdout.lower() or "Unsupported field type" in result.stdout, (
        f"Error messages should be shown even in quiet mode. Output: {result.stdout}"
    )


def test_quiet_flag_position_before_command(temp_dir: Path) -> None:
    """Test that --quiet flag works when placed before the command."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Test with --quiet before command
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file)])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify minimal output
    assert len(result.stdout.strip().split('\n')) <= 3, "Should have minimal output"
