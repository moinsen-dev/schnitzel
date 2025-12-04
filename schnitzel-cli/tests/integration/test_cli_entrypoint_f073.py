"""Integration tests for F073 - CLI entry point is accessible via 'schnitzel' command.

Test Requirements:
- test_schnitzel_command_defined_in_pyproject - entry point exists
- test_cli_help_works - --help shows help
- test_cli_version_works - --version shows version (if implemented)
- test_cli_init_command_exists - init subcommand accessible
- test_cli_generate_command_exists - generate subcommand accessible
"""

import subprocess
import tomllib
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


def test_schnitzel_command_defined_in_pyproject() -> None:
    """Test that the 'schnitzel' command entry point is defined in pyproject.toml."""
    # Read pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Verify entry point exists
    assert "project" in pyproject_data, "No [project] section in pyproject.toml"
    assert "scripts" in pyproject_data["project"], "No [project.scripts] section in pyproject.toml"
    assert "schnitzel" in pyproject_data["project"]["scripts"], "No 'schnitzel' entry point defined"

    # Verify entry point points to correct module (uses main wrapper for graceful Ctrl+C handling)
    entry_point = pyproject_data["project"]["scripts"]["schnitzel"]
    assert entry_point == "schnitzel.cli:main", (
        f"Entry point should be 'schnitzel.cli:main', but got '{entry_point}'"
    )


def test_cli_help_works() -> None:
    """Test that --help flag displays help information."""
    result = runner.invoke(app, ["--help"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Help command failed: {result.stdout}"

    # Verify help content is displayed
    assert "schnitzel" in result.stdout.lower() or "Schnitzel" in result.stdout
    assert "Schema-driven full-stack code generator" in result.stdout

    # Verify subcommands are listed
    assert "Commands:" in result.stdout or "command" in result.stdout.lower()

    # Verify at least some expected commands are mentioned
    assert "init" in result.stdout
    assert "generate" in result.stdout


@pytest.mark.skip(reason="version command not yet implemented - to be added in future wave")
def test_cli_version_works() -> None:
    """Test that version command shows the version number."""
    result = runner.invoke(app, ["version"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Version command failed: {result.stdout}"

    # Verify version is displayed
    assert "version" in result.stdout.lower() or "Schnitzel CLI version" in result.stdout
    assert "0.1.0" in result.stdout, "Version number should be displayed"


def test_cli_init_command_exists() -> None:
    """Test that init subcommand is accessible."""
    result = runner.invoke(app, ["init", "--help"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Init help command failed: {result.stdout}"

    # Verify init command help is displayed
    assert "init" in result.stdout.lower()
    assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()


def test_cli_generate_command_exists() -> None:
    """Test that generate subcommand is accessible."""
    result = runner.invoke(app, ["generate", "--help"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Generate help command failed: {result.stdout}"

    # Verify generate command help is displayed
    assert "generate" in result.stdout.lower()
    assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()
    assert "schema" in result.stdout.lower() or "SCHEMA" in result.stdout


@pytest.mark.skipif(
    not Path(__file__).parent.parent.parent.joinpath(".venv/bin/schnitzel").exists(),
    reason="schnitzel command not installed in virtual environment"
)
def test_schnitzel_command_executable_via_subprocess() -> None:
    """Test that 'schnitzel' command can be executed via subprocess (actual CLI entry point)."""
    # Get the virtual environment's bin directory
    venv_bin = Path(__file__).parent.parent.parent / ".venv" / "bin"
    schnitzel_cmd = venv_bin / "schnitzel"

    # Run schnitzel --help via subprocess
    result = subprocess.run(
        [str(schnitzel_cmd), "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )

    # Verify command succeeded
    assert result.returncode == 0, f"schnitzel command failed: {result.stderr}"

    # Verify help content is displayed
    assert "schnitzel" in result.stdout.lower() or "Schnitzel" in result.stdout
    assert "Schema-driven full-stack code generator" in result.stdout


def test_cli_app_is_typer_instance() -> None:
    """Test that the CLI app is properly configured as a Typer instance."""
    import typer

    # Verify app is a Typer instance
    assert isinstance(app, typer.Typer), "app should be a Typer instance"

    # Verify app has the correct name
    assert app.info.name == "schnitzel", "App name should be 'schnitzel'"

    # Verify app has help text
    assert app.info.help is not None, "App should have help text"
    assert "Schema-driven full-stack code generator" in app.info.help


def test_cli_import_from_package() -> None:
    """Test that the CLI app can be imported from the schnitzel.cli package."""
    # This test verifies the import chain works correctly
    from schnitzel.cli import app as cli_app

    assert cli_app is not None, "Failed to import app from schnitzel.cli"

    # Verify it's the same app instance
    assert cli_app is app, "Imported app should be the same instance"


def test_cli_commands_registered() -> None:
    """Test that expected commands are registered with the CLI app."""
    # Get list of registered commands
    registered_commands = list(app.registered_commands)
    command_names = [cmd.name for cmd in registered_commands if cmd.name is not None]

    # Verify expected commands are registered
    assert "init" in command_names, "init command should be registered"
    assert "generate" in command_names, "generate command should be registered"

    # Verify we have at least the core commands
    assert len(command_names) >= 2, f"Expected at least 2 commands, got {len(command_names)}"
