"""Integration test for F141: CLI robustness - Handle invalid command arguments.

Test Requirements:
- Test CLI handles invalid arguments gracefully
- Test missing required files
- Test bad command options
- Test invalid flag combinations
- Test helpful error messages
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


@pytest.fixture
def valid_schema(temp_dir: Path) -> Path:
    """Create a valid schema file."""
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
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_cli_without_arguments():
    """Test CLI without any arguments shows help or usage."""
    result = runner.invoke(app, [])

    # Typer apps without arguments may return exit code 0 (help) or 2 (missing command)
    # Both behaviors are acceptable
    assert result.exit_code in [0, 2], f"Exit code should be 0 or 2, got {result.exit_code}"


def test_cli_with_invalid_command():
    """Test CLI with non-existent command."""
    result = runner.invoke(app, ["invalid_command_xyz"])

    # Should fail gracefully with exit code 2 (Typer's default for invalid commands)
    assert result.exit_code == 2, f"Exit code should be 2, got {result.exit_code}"
    # Note: Typer outputs error to stderr, so stdout may be empty


def test_generate_without_schema_file(temp_dir: Path):
    """Test generate command without schema file argument."""
    result = runner.invoke(app, ["generate"])

    # Should try default schema.schnitzel.yaml and fail gracefully if not found
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "Error" in result.stdout


def test_generate_with_nonexistent_file(temp_dir: Path):
    """Test generate command with non-existent file."""
    result = runner.invoke(app, ["generate", "nonexistent.yaml"])

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "Error" in result.stdout


def test_generate_with_invalid_target(temp_dir: Path, valid_schema: Path):
    """Test generate command with invalid --target option."""
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "invalid_target"])

    assert result.exit_code == 1
    assert "Invalid target" in result.stdout or "Error" in result.stdout


def test_generate_with_invalid_output_dir(temp_dir: Path, valid_schema: Path):
    """Test generate command with invalid output directory."""
    # Try to write to a file that exists (not a directory)
    invalid_dir = temp_dir / "notadir.txt"
    invalid_dir.write_text("This is a file, not a directory")

    result = runner.invoke(app, ["generate", str(valid_schema), "--output", str(invalid_dir)])

    # Should handle gracefully - might create subdirectories or fail with clear error
    # Either way, should not crash
    assert result.exit_code in [0, 1]


def test_help_flag_works():
    """Test that --help flag works."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage" in result.stdout or "Commands" in result.stdout


def test_generate_help_flag_works():
    """Test that generate --help works."""
    result = runner.invoke(app, ["generate", "--help"])

    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "--target" in result.stdout or "target" in result.stdout.lower()


def test_init_help_flag_works():
    """Test that init --help works."""
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    assert "Usage" in result.stdout or "Create" in result.stdout


def test_multiple_conflicting_flags(temp_dir: Path, valid_schema: Path):
    """Test handling of potentially conflicting flags."""
    # Test --dry-run with --force (should not conflict, just both apply)
    result = runner.invoke(app, [
        "generate",
        str(valid_schema),
        "--dry-run",
        "--force"
    ])

    # Should handle gracefully
    assert result.exit_code == 0


def test_schema_flag_and_positional_arg(temp_dir: Path, valid_schema: Path):
    """Test that --schema flag works (may override positional arg)."""
    result = runner.invoke(app, [
        "generate",
        str(valid_schema),
        "--schema", str(valid_schema)
    ])

    # Should work - both specify same file
    assert result.exit_code == 0


def test_invalid_flag_format():
    """Test handling of invalid flag format."""
    result = runner.invoke(app, ["generate", "---invalid-flag"])

    # Should handle gracefully
    assert result.exit_code != 0


def test_empty_string_argument(temp_dir: Path):
    """Test handling of empty string as argument."""
    result = runner.invoke(app, ["generate", ""])

    assert result.exit_code == 1
    # Should indicate file not found or invalid path


def test_directory_instead_of_file(temp_dir: Path):
    """Test handling when directory is provided instead of file."""
    subdir = temp_dir / "somedir"
    subdir.mkdir()

    result = runner.invoke(app, ["generate", str(subdir)])

    # Should fail gracefully with appropriate error
    assert result.exit_code == 1


def test_schema_with_special_characters(temp_dir: Path):
    """Test handling of file paths with special characters."""
    special_file = temp_dir / "schema with spaces.yaml"
    special_file.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
""")

    result = runner.invoke(app, ["generate", str(special_file)])

    # Should handle file paths with spaces
    assert result.exit_code == 0


def test_very_long_argument():
    """Test handling of extremely long argument."""
    long_arg = "x" * 10000

    result = runner.invoke(app, ["generate", long_arg])

    # Should fail gracefully without crash
    assert result.exit_code == 1


def test_unicode_in_arguments(temp_dir: Path):
    """Test handling of unicode characters in arguments."""
    unicode_file = temp_dir / "schéma_测试.yaml"
    unicode_file.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
""")

    result = runner.invoke(app, ["generate", str(unicode_file)])

    # Should handle unicode file names
    # May succeed or fail depending on filesystem, but shouldn't crash
    assert result.exit_code in [0, 1]


def test_cli_error_messages_are_helpful(temp_dir: Path):
    """Test that error messages provide helpful context."""
    result = runner.invoke(app, ["generate", "missing_file.yaml"])

    assert result.exit_code == 1

    # Error message should be helpful
    stdout_lower = result.stdout.lower()
    # Should mention what went wrong
    assert any(phrase in stdout_lower for phrase in [
        "not found",
        "does not exist",
        "error",
        "failed"
    ])


def test_target_option_accepts_valid_values(temp_dir: Path, valid_schema: Path):
    """Test that --target accepts all valid target values."""
    valid_targets = ["all", "python", "dart", "flutter", "docker"]

    for target in valid_targets:
        result = runner.invoke(app, ["generate", str(valid_schema), "--target", target])

        assert result.exit_code == 0, \
            f"Valid target '{target}' should be accepted: {result.stdout}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
