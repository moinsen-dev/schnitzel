"""Integration tests for F091 - CLI shows helpful error when run outside project directory.

Test Requirements:
- test_error_when_no_schema_found - shows error when schema not found
- test_error_message_is_helpful - message suggests solutions
- test_error_includes_suggestion - suggests schnitzel init
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


def test_error_when_no_schema_found(temp_dir: Path) -> None:
    """Test that CLI shows an error when schema file is not found."""
    # Ensure no schema.schnitzel.yaml exists in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists(), "Schema file should not exist for this test"

    # Run generate command without specifying schema path
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when schema file doesn't exist"
    assert "Error: Schema file not found" in result.stdout or "not found" in result.stdout.lower()


def test_error_message_is_helpful(temp_dir: Path) -> None:
    """Test that the error message is helpful and suggests solutions."""
    # Ensure no schema.schnitzel.yaml exists
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when schema file doesn't exist"

    # Check for helpful error message components
    output = result.stdout

    # Should mention the problem clearly
    assert "Error: Schema file not found" in output or "not found" in output.lower()

    # Should suggest that user might be outside a project directory
    assert "outside" in output.lower() or "project directory" in output.lower()

    # Should provide actionable solutions
    assert "To get started" in output or "get started" in output.lower()


def test_error_includes_suggestion(temp_dir: Path) -> None:
    """Test that error message suggests running schnitzel init."""
    # Ensure no schema.schnitzel.yaml exists
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when schema file doesn't exist"

    output = result.stdout

    # Should suggest schnitzel init
    assert "schnitzel init" in output

    # Should suggest specifying a schema file
    assert "schnitzel generate" in output
    assert "path" in output.lower() or "schema" in output.lower()

    # Should explain the default behavior
    assert "default" in output.lower() or "schema.schnitzel.yaml" in output


def test_error_when_explicit_path_not_found(temp_dir: Path) -> None:
    """Test that error is shown when an explicit schema path doesn't exist."""
    # Create a non-existent path
    nonexistent_schema = temp_dir / "nonexistent" / "schema.yaml"
    assert not nonexistent_schema.exists()

    # Run generate command with explicit non-existent path
    result = runner.invoke(app, ["generate", str(nonexistent_schema)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when specified schema doesn't exist"
    assert "Error: Schema file not found" in result.stdout or "not found" in result.stdout.lower()

    # Should still show helpful suggestions
    assert "schnitzel init" in result.stdout


def test_error_message_includes_all_guidance(temp_dir: Path) -> None:
    """Test that error message includes comprehensive guidance for the user."""
    # Ensure no schema.schnitzel.yaml exists
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1

    output = result.stdout

    # Should include all key guidance elements:
    # 1. Error identification
    assert "Error:" in output or "error" in output.lower()

    # 2. Problem explanation
    assert "outside" in output.lower() or "project" in output.lower()

    # 3. Solution 1: Init new project
    assert "init" in output.lower()
    assert "my-project" in output or "project-name" in output.lower()

    # 4. Solution 2: Specify schema file
    assert "generate" in output.lower()
    assert "schema" in output.lower()

    # 5. Explanation of default behavior
    assert "schema.schnitzel.yaml" in output


def test_error_output_is_user_friendly(temp_dir: Path) -> None:
    """Test that error output doesn't contain technical stack traces."""
    # Ensure no schema.schnitzel.yaml exists
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1

    output = result.stdout

    # Should NOT contain stack trace elements
    assert "Traceback" not in output, "Should not show Python traceback"
    assert "File \"" not in output or "line " not in output, "Should not show code references"

    # Should have helpful content (rich formatting tags are stripped in test output)
    assert "Error:" in output or "error" in output.lower()
    assert "schnitzel init" in output


def test_error_with_schema_flag_not_found(temp_dir: Path) -> None:
    """Test error when using --schema flag with non-existent file."""
    nonexistent_schema = temp_dir / "missing.yaml"
    assert not nonexistent_schema.exists()

    # Run generate with --schema flag
    result = runner.invoke(app, ["generate", "--schema", str(nonexistent_schema)])

    # Verify failure
    assert result.exit_code == 1
    assert "Error: Schema file not found" in result.stdout or "not found" in result.stdout.lower()

    # Should still show helpful guidance
    assert "schnitzel init" in result.stdout


def test_error_distinguishes_missing_vs_other_errors(temp_dir: Path) -> None:
    """Test that missing schema error is distinct from other schema errors."""
    # This test verifies that the specific "file not found" error is shown,
    # not a generic schema parsing error

    # Ensure no schema exists
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command
    result = runner.invoke(app, ["generate"])

    # Verify it's specifically a "not found" error, not a parsing error
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()

    # Should NOT show parsing errors or validation errors
    assert "parsing" not in result.stdout.lower()
    assert "validation" not in result.stdout.lower()
    assert "YAML" not in result.stdout or "yaml" not in result.stdout.lower()


def test_error_message_formatting(temp_dir: Path) -> None:
    """Test that error message is properly formatted with good readability."""
    # Ensure no schema exists
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1

    output = result.stdout

    # Should have clear structure (numbered steps, bullets, etc.)
    assert "1." in output or "2." in output, "Should have numbered suggestions"

    # Should have indentation for readability
    assert "  " in output or "\n\n" in output, "Should have spacing for readability"

    # Should have all the helpful content
    assert "Error:" in output or "error" in output.lower()
    assert "schnitzel init" in output
    assert "schnitzel generate" in output
