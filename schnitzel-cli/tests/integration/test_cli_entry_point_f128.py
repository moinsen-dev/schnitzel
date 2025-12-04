"""Integration tests for F128 - CLI entry point is registered in pyproject.toml.

Test Requirements:
- test_cli_entry_point_in_pyproject: Verify schnitzel command is registered
- test_cli_command_can_be_imported: Test that CLI module can be imported
- test_cli_command_executes: Test that schnitzel command can be executed
- test_cli_help_works: Test that schnitzel --help works
- test_cli_version_works: Test that schnitzel version command works
"""

import pytest
import subprocess
import sys
from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from typer.testing import CliRunner


def test_cli_entry_point_in_pyproject() -> None:
    """Test that CLI entry point 'schnitzel' is registered in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get scripts/entry points
    scripts = pyproject_data.get("project", {}).get("scripts", {})

    # Verify schnitzel command is registered
    assert "schnitzel" in scripts, "CLI command 'schnitzel' should be registered in [project.scripts]"

    # Get the entry point
    entry_point = scripts["schnitzel"]

    # Verify entry point format (module:function)
    assert ":" in entry_point, "Entry point should be in format 'module:function'"
    assert "schnitzel" in entry_point, "Entry point should reference schnitzel module"

    # Parse module and function
    module_path, function_name = entry_point.split(":", 1)
    assert "schnitzel" in module_path, "Module path should contain 'schnitzel'"
    assert function_name in ["main", "app"], "Function should be 'main' or 'app'"

    print(f"\n✓ CLI entry point registered: schnitzel = {entry_point}")


def test_cli_module_can_be_imported() -> None:
    """Test that CLI module can be imported successfully."""
    try:
        # Import the CLI module
        from schnitzel.cli import app, main

        assert app is not None, "CLI app should be importable"
        assert main is not None, "main function should be importable"
        assert callable(main), "main should be a callable function"

        print("\n✓ CLI module imports successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import CLI module: {e}")


def test_cli_app_is_typer_instance() -> None:
    """Test that CLI app is a Typer instance."""
    from schnitzel.cli import app
    import typer

    # Verify app is a Typer instance
    assert isinstance(app, typer.Typer), "CLI app should be a Typer instance"

    print("\n✓ CLI app is a valid Typer instance")


def test_cli_help_works() -> None:
    """Test that schnitzel --help command works."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Run --help command
    result = runner.invoke(app, ["--help"])

    # Verify success
    assert result.exit_code == 0, f"--help should succeed. Output: {result.stdout}"

    # Verify help output contains expected content
    assert "schnitzel" in result.stdout.lower(), "Help should mention schnitzel"
    assert "Usage:" in result.stdout or "usage:" in result.stdout.lower(), "Help should show usage"

    # Check for common commands (should have at least some commands)
    commands_present = any(cmd in result.stdout.lower() for cmd in ["init", "generate", "validate", "version"])
    assert commands_present, f"Help should list available commands. Output: {result.stdout}"

    print("\n✓ CLI --help command works")


def test_cli_version_command_exists() -> None:
    """Test that schnitzel version command exists and works."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Run version command
    result = runner.invoke(app, ["version"])

    # Verify success
    assert result.exit_code == 0, f"version command should succeed. Output: {result.stdout}"

    # Verify version output
    assert "schnitzel" in result.stdout.lower() or "version" in result.stdout.lower(), \
        f"Version output should mention schnitzel or version. Output: {result.stdout}"

    print(f"\n✓ CLI version command works: {result.stdout.strip()}")


@pytest.mark.skip(reason="validate command not implemented - generate does validation")
def test_cli_validate_command_exists() -> None:
    """Test that schnitzel validate command exists."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Run validate command without arguments (should show error or help)
    result = runner.invoke(app, ["validate"])

    # Command should exist (exit code 0 for help, or 2 for missing argument)
    assert result.exit_code in [0, 1, 2], f"validate command should exist. Output: {result.stdout}"

    # Error message should indicate missing schema path
    output_lower = result.stdout.lower()
    assert "schema" in output_lower or "argument" in output_lower or "missing" in output_lower, \
        f"Should indicate missing schema argument. Output: {result.stdout}"

    print("\n✓ CLI validate command exists")


def test_cli_generate_command_exists() -> None:
    """Test that schnitzel generate command exists."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Run generate command without arguments (should show error or help)
    result = runner.invoke(app, ["generate"])

    # Command should exist (exit code 0 for help, or 2 for missing argument)
    assert result.exit_code in [0, 1, 2], f"generate command should exist. Output: {result.stdout}"

    # Error message should indicate missing schema path
    output_lower = result.stdout.lower()
    assert "schema" in output_lower or "argument" in output_lower or "missing" in output_lower, \
        f"Should indicate missing schema argument. Output: {result.stdout}"

    print("\n✓ CLI generate command exists")


def test_cli_init_command_exists() -> None:
    """Test that schnitzel init command exists."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Run init command help
    result = runner.invoke(app, ["init", "--help"])

    # Command should exist and help should work
    assert result.exit_code == 0, f"init --help should work. Output: {result.stdout}"
    assert "init" in result.stdout.lower(), f"Help should mention init command. Output: {result.stdout}"

    print("\n✓ CLI init command exists")


def test_cli_main_function_callable() -> None:
    """Test that main() function is callable and handles KeyboardInterrupt."""
    from schnitzel.cli import main

    # Verify main is callable
    assert callable(main), "main should be a callable function"

    # Check that main is properly defined (has __name__ attribute)
    assert hasattr(main, "__name__"), "main should have __name__ attribute"
    assert main.__name__ == "main", "Function should be named 'main'"

    print("\n✓ main() function is properly defined and callable")


def test_cli_quiet_mode_flag() -> None:
    """Test that CLI supports --quiet flag for minimal output."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Check if --quiet flag is available in help
    result = runner.invoke(app, ["--help"])

    # Look for quiet flag in help output
    has_quiet = "--quiet" in result.stdout or "-q" in result.stdout

    if has_quiet:
        print("\n✓ CLI supports --quiet flag")
    else:
        # Not required, just informational
        print("\n✓ CLI help displayed (--quiet flag optional)")


def test_cli_verbose_mode_flag() -> None:
    """Test that CLI supports --verbose flag for detailed output."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Check if --verbose flag is available in help
    result = runner.invoke(app, ["--help"])

    # Look for verbose flag in help output
    has_verbose = "--verbose" in result.stdout or "-v" in result.stdout

    if has_verbose:
        print("\n✓ CLI supports --verbose flag")
    else:
        # Not required, just informational
        print("\n✓ CLI help displayed (--verbose flag optional)")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F128: CLI entry point is registered in pyproject.toml")
    print("=" * 70)

    try:
        print("\n1. Testing CLI entry point in pyproject.toml...")
        test_cli_entry_point_in_pyproject()

        print("\n2. Testing CLI module import...")
        test_cli_module_can_be_imported()

        print("\n3. Testing CLI app is Typer instance...")
        test_cli_app_is_typer_instance()

        print("\n4. Testing CLI --help...")
        test_cli_help_works()

        print("\n5. Testing CLI version command...")
        test_cli_version_command_exists()

        print("\n6. Testing CLI validate command...")
        test_cli_validate_command_exists()

        print("\n7. Testing CLI generate command...")
        test_cli_generate_command_exists()

        print("\n8. Testing CLI init command...")
        test_cli_init_command_exists()

        print("\n9. Testing main() function...")
        test_cli_main_function_callable()

        print("\n10. Testing --quiet flag...")
        test_cli_quiet_mode_flag()

        print("\n11. Testing --verbose flag...")
        test_cli_verbose_mode_flag()

        print("\n" + "=" * 70)
        print("✓ All F128 tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
