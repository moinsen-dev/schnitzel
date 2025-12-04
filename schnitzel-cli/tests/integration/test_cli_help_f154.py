"""Integration tests for F154 - CLI help text organization and clarity.

Test Requirements:
- test_help_shows_commands - Help shows all available commands
- test_help_shows_descriptions - Help includes command descriptions
- test_help_shows_options - Help shows options for each command
- test_command_help_detailed - Individual commands have detailed help
- test_help_is_organized - Help is well-organized and easy to read
"""

from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


def test_help_shows_commands() -> None:
    """Test that --help shows all available commands."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Check for main commands
    assert "init" in output, "Should show init command"
    assert "generate" in output, "Should show generate command"
    assert "validate" in output, "Should show validate command"
    assert "version" in output, "Should show version command"


def test_help_shows_descriptions() -> None:
    """Test that help includes descriptions for commands."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout

    # Help should not be just a list - should have context
    assert len(output) > 100, "Help should have substantial content"

    # Should mention key concepts
    assert "schema" in output.lower(), "Should mention schema"


def test_help_shows_options() -> None:
    """Test that help shows global options."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should show global options
    assert "verbose" in output or "-v" in output, "Should show --verbose option"
    assert "quiet" in output or "-q" in output, "Should show --quiet option"
    assert "help" in output, "Should show --help option"


def test_command_help_detailed() -> None:
    """Test that individual commands have detailed help."""
    # Test init command help
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    init_output = result.stdout.lower()

    assert "init" in init_output
    assert "project" in init_output or "name" in init_output, \
        "Init help should mention project name"

    # Test generate command help
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    gen_output = result.stdout.lower()

    assert "generate" in gen_output
    assert "schema" in gen_output, "Generate help should mention schema"
    assert "target" in gen_output or "--target" in gen_output, \
        "Generate help should mention --target option"

    # Test validate command help
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    val_output = result.stdout.lower()

    assert "validate" in val_output
    assert "schema" in val_output, "Validate help should mention schema"


def test_help_is_organized() -> None:
    """Test that help is well-organized with clear sections."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout

    # Should have usage section
    assert "usage:" in output.lower() or "Usage:" in output, \
        "Help should have usage section"

    # Should have multiple lines (well-formatted)
    lines = output.split('\n')
    assert len(lines) > 5, "Help should have multiple lines"

    # Should have indented content (indicates structure)
    indented_lines = [line for line in lines if line.startswith('  ')]
    assert len(indented_lines) > 0, "Help should have indented content"


def test_init_help_shows_template_option() -> None:
    """Test that init help shows template option."""
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should mention template option
    assert "template" in output, "Init help should mention --template option"


def test_generate_help_shows_key_options() -> None:
    """Test that generate help shows key options."""
    result = runner.invoke(app, ["generate", "--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should show important options
    assert "force" in output or "--force" in output, \
        "Generate help should show --force option"
    assert "watch" in output or "--watch" in output, \
        "Generate help should show --watch option"
    assert "dry" in output or "dry-run" in output or "--dry-run" in output, \
        "Generate help should show --dry-run option"


def test_help_examples_or_usage() -> None:
    """Test that help provides usage information."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should show how to use the CLI
    assert "schnitzel" in output, "Should mention schnitzel command"


def test_help_no_errors() -> None:
    """Test that help doesn't contain error messages."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should not have error indicators in help
    # (Note: "error" might appear in command descriptions, so check context)
    assert "[red]" not in output, "Help should not have red error formatting"


def test_version_in_help() -> None:
    """Test that version command is documented in help."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should mention version command
    assert "version" in output, "Help should mention version command"


def test_validate_help_clear() -> None:
    """Test that validate command help is clear."""
    result = runner.invoke(app, ["validate", "--help"])

    assert result.exit_code == 0
    output = result.stdout.lower()

    # Should be clear about what validate does
    assert "schema" in output, "Validate help should mention schema"
    assert "validate" in output, "Should mention validation"


def test_help_appropriate_length() -> None:
    """Test that help text is not too short or too long."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = result.stdout

    # Should be informative but not overwhelming
    assert 50 < len(output) < 5000, \
        "Help should be appropriate length (not empty, not too verbose)"


def test_command_help_consistent_format() -> None:
    """Test that all command help follows consistent format."""
    commands = ["init", "generate", "validate"]

    for cmd in commands:
        result = runner.invoke(app, [cmd, "--help"])
        assert result.exit_code == 0, f"{cmd} --help should succeed"

        output = result.stdout
        assert len(output) > 20, f"{cmd} help should have content"
        assert cmd in output.lower(), f"{cmd} help should mention the command"
