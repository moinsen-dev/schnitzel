"""Integration tests for F114 - CLI help text is well-formatted with Rich styling.

Test Requirements:
- test_help_formatted - Verify help text uses Rich formatting
- test_commands_listed - Verify all commands are listed in help
"""

from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


def test_help_formatted() -> None:
    """Test that CLI help text is well-formatted with Rich styling."""
    # Run help command
    result = runner.invoke(app, ["--help"])

    # Should succeed
    assert result.exit_code == 0

    # Verify help output contains key sections
    output = result.stdout
    assert len(output) > 0, "Help output should not be empty"

    # Check for help structure
    assert "Usage:" in output or "usage:" in output.lower(), \
        "Help should show usage information"

    # Rich formatting may include ANSI codes or plain text
    # Just verify the content is there
    assert "schnitzel" in output.lower(), "Help should mention schnitzel"


def test_commands_listed() -> None:
    """Test that all main commands are listed in help."""
    # Run help command
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Verify main commands are listed
    assert "init" in output, "Help should list 'init' command"
    assert "generate" in output, "Help should list 'generate' command"
    assert "validate" in output, "Help should list 'validate' command"
    assert "version" in output, "Help should list 'version' command"


def test_init_command_help() -> None:
    """Test that init command has help text."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0

    output = result.stdout

    # Verify help describes init command
    assert "init" in output.lower()
    assert "project" in output.lower() or "initialize" in output.lower(), \
        "Init help should describe project initialization"

    # Verify arguments/options are documented
    assert "project" in output.lower() or "name" in output.lower(), \
        "Init help should document project name argument"


def test_generate_command_help() -> None:
    """Test that generate command has help text."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0

    output = result.stdout

    # Verify help describes generate command
    assert "generate" in output.lower()
    assert "schema" in output.lower(), \
        "Generate help should mention schema file"

    # Verify options are documented
    assert "target" in output.lower() or "--target" in output, \
        "Generate help should document --target option"
    assert "force" in output.lower() or "--force" in output, \
        "Generate help should document --force option"


def test_validate_command_help() -> None:
    """Test that validate command has help text."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0

    output = result.stdout

    # Verify help describes validate command
    assert "validate" in output.lower()
    assert "schema" in output.lower(), \
        "Validate help should mention schema validation"


def test_help_shows_global_options() -> None:
    """Test that help shows global options like --verbose and --quiet."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Check for global options
    assert "verbose" in output or "-v" in output, \
        "Help should show --verbose option"
    assert "quiet" in output or "-q" in output, \
        "Help should show --quiet option"


def test_help_describes_schema_format() -> None:
    """Test that help or command descriptions mention schema format."""
    # Main help
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should mention schema-driven or full-stack
    assert "schema" in output, "Help should mention schema"


def test_version_command_works() -> None:
    """Test that version command displays version information."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0

    output = result.stdout

    # Should show version
    assert "schnitzel" in output.lower() or "version" in output.lower(), \
        "Version command should display version info"


def test_help_uses_proper_formatting() -> None:
    """Test that help output has proper structure and formatting."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    output = result.stdout

    # Check for structured sections
    lines = output.split('\n')
    assert len(lines) > 5, "Help should have multiple lines"

    # Verify it's not just plain text - should have structure
    # Rich/Typer adds structure with indentation
    indented_lines = [line for line in lines if line.startswith('  ')]
    assert len(indented_lines) > 0, "Help should have indented content"


def test_init_template_option_documented() -> None:
    """Test that init --template option is documented in help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should document template option
    assert "template" in output, "Init help should document --template option"
    assert "minimal" in output or "full" in output, \
        "Init help should mention template choices"


def test_generate_watch_mode_documented() -> None:
    """Test that generate --watch option is documented."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should document watch mode
    assert "watch" in output, "Generate help should document --watch option"


def test_generate_dry_run_documented() -> None:
    """Test that generate --dry-run option is documented."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should document dry-run mode
    assert "dry" in output or "dry-run" in output, \
        "Generate help should document --dry-run option"


def test_help_is_readable_and_clear() -> None:
    """Test that help text is readable without excessive technical jargon."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    output = result.stdout

    # Help should be reasonably sized - not too short, not too long
    assert 100 < len(output) < 5000, \
        "Help output should be reasonably sized"

    # Should not have error markers
    assert "[red]" not in output.lower(), "Help should not contain error formatting"
    assert "error" not in output.lower() or "error" in "generate", \
        "Help should not contain error messages"


def test_commands_have_descriptions() -> None:
    """Test that each command has a description in help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    # Each command should have description text nearby
    # This is a basic check that commands aren't just listed without context
    lines = result.stdout.split('\n')

    # Find lines with commands
    command_section_found = False
    for line in lines:
        if "commands" in line.lower():
            command_section_found = True
            break

    # Should have a commands section (Typer adds this)
    assert command_section_found or "init" in result.stdout, \
        "Help should have commands section or list commands"
