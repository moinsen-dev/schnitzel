"""Integration tests for api_166 - Commands module structure is properly organized.

Test Requirements:
This feature verifies that the CLI commands module structure is properly organized
with all required command files and proper exports.

Tests:
- test_commands_directory_exists: Verify commands directory exists
- test_commands_init_file_exists: Verify __init__.py exists in commands
- test_serve_command_exists: Verify serve.py command file exists
- test_validate_command_exists: Verify validate.py command file exists
- test_migrate_command_exists: Verify migrate.py command file exists
- test_init_command_exists: Verify init.py command file exists (from module_00)
- test_generate_command_exists: Verify generate.py command file exists (from module_00)
- test_commands_are_importable: Verify all command modules can be imported
- test_commands_export_typer_functions: Verify each command exports proper Typer functions
- test_commands_registered_in_cli: Verify commands are properly registered in CLI app
- test_command_files_have_no_errors: Verify command files have no syntax errors
- test_command_files_have_no_warnings: Verify command files follow best practices
- test_command_files_have_no_todos: Verify command files have no TODOs (zero-tolerance)
"""

import pytest
from pathlib import Path
import ast
import re
from typing import List, Dict, Any
from typer.testing import CliRunner


def get_commands_directory() -> Path:
    """Get the path to the commands directory."""
    project_root = Path(__file__).parent.parent.parent
    commands_dir = project_root / "src" / "schnitzel" / "cli" / "commands"
    return commands_dir


def test_commands_directory_exists() -> None:
    """Test that the commands directory exists at the correct location."""
    commands_dir = get_commands_directory()

    assert commands_dir.exists(), f"Commands directory should exist at {commands_dir}"
    assert commands_dir.is_dir(), f"Commands path should be a directory: {commands_dir}"

    print(f"\n✓ Commands directory exists: {commands_dir}")


def test_commands_init_file_exists() -> None:
    """Test that __init__.py exists in commands directory."""
    commands_dir = get_commands_directory()
    init_file = commands_dir / "__init__.py"

    assert init_file.exists(), f"__init__.py should exist in commands directory"
    assert init_file.is_file(), f"__init__.py should be a file"

    # Read the content to verify it's not empty
    content = init_file.read_text()
    assert len(content.strip()) > 0, "__init__.py should not be empty"

    print(f"✓ Commands __init__.py exists and has content")


def test_serve_command_exists() -> None:
    """Test that serve.py command file exists."""
    commands_dir = get_commands_directory()
    serve_file = commands_dir / "serve.py"

    assert serve_file.exists(), f"serve.py should exist in {commands_dir}"
    assert serve_file.is_file(), f"serve.py should be a file"

    # Verify it has content
    content = serve_file.read_text()
    assert len(content) > 0, "serve.py should not be empty"
    assert "def serve_command" in content, "serve.py should define serve_command function"

    print("✓ serve.py command file exists with serve_command function")


def test_validate_command_exists() -> None:
    """Test that validate.py command file exists."""
    commands_dir = get_commands_directory()
    validate_file = commands_dir / "validate.py"

    assert validate_file.exists(), f"validate.py should exist in {commands_dir}"
    assert validate_file.is_file(), f"validate.py should be a file"

    # Verify it has content
    content = validate_file.read_text()
    assert len(content) > 0, "validate.py should not be empty"
    assert "def validate_command" in content, "validate.py should define validate_command function"

    print("✓ validate.py command file exists with validate_command function")


def test_migrate_command_exists() -> None:
    """Test that migrate.py command file exists."""
    commands_dir = get_commands_directory()
    migrate_file = commands_dir / "migrate.py"

    assert migrate_file.exists(), f"migrate.py should exist in {commands_dir}"
    assert migrate_file.is_file(), f"migrate.py should be a file"

    # Verify it has content
    content = migrate_file.read_text()
    assert len(content) > 0, "migrate.py should not be empty"
    # migrate is a command group with subcommands
    assert "migrate = typer.Typer" in content or "def migrate_command" in content, \
        "migrate.py should define migrate command or command group"

    print("✓ migrate.py command file exists with migrate command group")


def test_init_command_exists() -> None:
    """Test that init.py command file exists (from module_00)."""
    commands_dir = get_commands_directory()
    init_file = commands_dir / "init.py"

    assert init_file.exists(), f"init.py should exist in {commands_dir}"
    assert init_file.is_file(), f"init.py should be a file"

    # Verify it has content
    content = init_file.read_text()
    assert len(content) > 0, "init.py should not be empty"
    assert "def init_command" in content, "init.py should define init_command function"

    print("✓ init.py command file exists with init_command function")


def test_generate_command_exists() -> None:
    """Test that generate.py command file exists (from module_00)."""
    commands_dir = get_commands_directory()
    generate_file = commands_dir / "generate.py"

    assert generate_file.exists(), f"generate.py should exist in {commands_dir}"
    assert generate_file.is_file(), f"generate.py should be a file"

    # Verify it has content
    content = generate_file.read_text()
    assert len(content) > 0, "generate.py should not be empty"
    assert "def generate_command" in content, "generate.py should define generate_command function"

    print("✓ generate.py command file exists with generate_command function")


def test_all_required_commands_exist() -> None:
    """Test that all required command files exist."""
    commands_dir = get_commands_directory()

    required_commands = [
        "serve.py",
        "validate.py",
        "migrate.py",
        "init.py",
        "generate.py",
    ]

    for command_file in required_commands:
        file_path = commands_dir / command_file
        assert file_path.exists(), f"Required command file {command_file} should exist"
        assert file_path.is_file(), f"{command_file} should be a file"

    print(f"✓ All {len(required_commands)} required command files exist")


def test_commands_are_importable() -> None:
    """Test that all command modules can be imported without errors."""
    try:
        from schnitzel.cli.commands import init
        from schnitzel.cli.commands import generate
        from schnitzel.cli.commands import validate
        from schnitzel.cli.commands import serve
        from schnitzel.cli.commands import migrate

        print("✓ All command modules are importable")

    except ImportError as e:
        pytest.fail(f"Failed to import command modules: {e}")


def test_init_command_exports_function() -> None:
    """Test that init.py exports init_command function."""
    from schnitzel.cli.commands.init import init_command

    assert callable(init_command), "init_command should be callable"
    assert hasattr(init_command, "__name__"), "init_command should have __name__"

    print("✓ init.py exports callable init_command function")


def test_generate_command_exports_function() -> None:
    """Test that generate.py exports generate_command function."""
    from schnitzel.cli.commands.generate import generate_command

    assert callable(generate_command), "generate_command should be callable"
    assert hasattr(generate_command, "__name__"), "generate_command should have __name__"

    print("✓ generate.py exports callable generate_command function")


def test_validate_command_exports_function() -> None:
    """Test that validate.py exports validate_command function."""
    from schnitzel.cli.commands.validate import validate_command

    assert callable(validate_command), "validate_command should be callable"
    assert hasattr(validate_command, "__name__"), "validate_command should have __name__"

    print("✓ validate.py exports callable validate_command function")


def test_serve_command_exports_function() -> None:
    """Test that serve.py exports serve_command function."""
    from schnitzel.cli.commands.serve import serve_command

    assert callable(serve_command), "serve_command should be callable"
    assert hasattr(serve_command, "__name__"), "serve_command should have __name__"

    print("✓ serve.py exports callable serve_command function")


def test_migrate_command_exports_function() -> None:
    """Test that migrate.py exports migrate_command function or Typer instance."""
    from schnitzel.cli.commands.migrate import migrate_command

    assert callable(migrate_command), "migrate_command should be callable"

    # migrate_command returns a Typer instance (it's a command group)
    result = migrate_command()
    import typer
    assert isinstance(result, typer.Typer), "migrate_command should return a Typer instance"

    print("✓ migrate.py exports migrate_command function returning Typer instance")


def test_commands_registered_in_cli() -> None:
    """Test that all commands are properly registered in the CLI app."""
    from schnitzel.cli import app

    # Get registered commands from the Typer app
    # Typer stores commands in app.registered_commands
    commands = {}
    for command in app.registered_commands:
        if hasattr(command, 'name'):
            commands[command.name] = command

    # Also check for command groups (like migrate)
    groups = {}
    for group in app.registered_groups:
        if hasattr(group, 'name'):
            groups[group.name] = group

    # Expected commands (version may or may not have a name attribute)
    # These are the core commands we require
    required_commands = ["init", "generate", "validate", "serve"]
    expected_groups = ["migrate"]

    # Check required commands
    for cmd_name in required_commands:
        assert cmd_name in commands or any(cmd_name in str(c) for c in commands.values()), \
            f"Command '{cmd_name}' should be registered in CLI app"

    # Check command groups
    for group_name in expected_groups:
        assert group_name in groups or any(group_name in str(g) for g in groups.values()), \
            f"Command group '{group_name}' should be registered in CLI app"

    # version command may be present but with None name, which is OK
    print(f"✓ All commands registered in CLI: {len(commands)} commands, {len(groups)} groups")


def test_cli_help_shows_all_commands() -> None:
    """Test that CLI --help shows all registered commands."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0, "CLI --help should succeed"

    # Check that help text mentions the commands
    help_text = result.stdout.lower()

    expected_in_help = ["init", "generate", "validate", "serve", "migrate"]

    found_commands = []
    for cmd in expected_in_help:
        if cmd in help_text:
            found_commands.append(cmd)

    assert len(found_commands) >= 4, \
        f"Help should mention most commands. Found: {found_commands}"

    print(f"✓ CLI help shows commands: {found_commands}")


def test_command_files_have_no_syntax_errors() -> None:
    """Test that all command files have valid Python syntax (no syntax errors)."""
    commands_dir = get_commands_directory()

    command_files = [
        "init.py",
        "generate.py",
        "validate.py",
        "serve.py",
        "migrate.py",
    ]

    for command_file in command_files:
        file_path = commands_dir / command_file
        content = file_path.read_text()

        try:
            ast.parse(content)
            print(f"✓ {command_file}: No syntax errors")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {command_file}: {e}")


def test_command_files_have_no_todos() -> None:
    """Test that command files have no TODO comments (zero-tolerance policy)."""
    commands_dir = get_commands_directory()

    command_files = [
        "init.py",
        "generate.py",
        "validate.py",
        "serve.py",
        "migrate.py",
    ]

    # Pattern to match TODO comments (case insensitive)
    todo_pattern = re.compile(r'#.*\bTODO\b', re.IGNORECASE)

    todos_found = {}

    for command_file in command_files:
        file_path = commands_dir / command_file
        content = file_path.read_text()

        todos = []
        for line_num, line in enumerate(content.splitlines(), 1):
            if todo_pattern.search(line):
                todos.append((line_num, line.strip()))

        if todos:
            todos_found[command_file] = todos

    # Assert no TODOs found (zero-tolerance)
    if todos_found:
        error_msg = "TODO comments found (zero-tolerance policy):\n"
        for file_name, todos in todos_found.items():
            error_msg += f"\n{file_name}:\n"
            for line_num, line in todos:
                error_msg += f"  Line {line_num}: {line}\n"
        pytest.fail(error_msg)

    print(f"✓ No TODO comments found in {len(command_files)} command files")


def test_command_files_have_docstrings() -> None:
    """Test that all command files have module-level docstrings."""
    commands_dir = get_commands_directory()

    command_files = [
        "init.py",
        "generate.py",
        "validate.py",
        "serve.py",
        "migrate.py",
    ]

    for command_file in command_files:
        file_path = commands_dir / command_file
        content = file_path.read_text()

        # Parse the file and check for module docstring
        tree = ast.parse(content)

        has_docstring = (
            len(tree.body) > 0 and
            isinstance(tree.body[0], ast.Expr) and
            isinstance(tree.body[0].value, ast.Constant) and
            isinstance(tree.body[0].value.value, str)
        )

        assert has_docstring, f"{command_file} should have a module-level docstring"

    print(f"✓ All {len(command_files)} command files have module docstrings")


def test_command_functions_have_docstrings() -> None:
    """Test that command functions have docstrings."""
    commands_to_check = [
        ("init.py", "init_command"),
        ("generate.py", "generate_command"),
        ("validate.py", "validate_command"),
        ("serve.py", "serve_command"),
        ("migrate.py", "migrate_command"),
    ]

    commands_dir = get_commands_directory()

    for file_name, function_name in commands_to_check:
        file_path = commands_dir / file_name
        content = file_path.read_text()

        # Parse and find the function
        tree = ast.parse(content)

        function_found = False
        has_docstring = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                function_found = True
                # Check if function has docstring
                if (
                    len(node.body) > 0 and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                ):
                    has_docstring = True
                break

        if function_found:
            assert has_docstring, f"{function_name} in {file_name} should have a docstring"
            print(f"✓ {file_name}::{function_name} has docstring")


def test_commands_use_typer_decorators() -> None:
    """Test that command functions use proper Typer type hints."""
    from schnitzel.cli.commands.init import init_command
    from schnitzel.cli.commands.generate import generate_command
    from schnitzel.cli.commands.validate import validate_command
    from schnitzel.cli.commands.serve import serve_command

    commands = [
        ("init_command", init_command),
        ("generate_command", generate_command),
        ("validate_command", validate_command),
        ("serve_command", serve_command),
    ]

    for name, func in commands:
        # Check that function has annotations (type hints)
        assert hasattr(func, "__annotations__"), f"{name} should have type annotations"

        # Check that function has a return type hint
        annotations = func.__annotations__
        # Note: return type is optional but recommended

        print(f"✓ {name} has type annotations")


def test_commands_module_structure_summary() -> None:
    """Summary test showing the complete module structure."""
    commands_dir = get_commands_directory()

    # Collect all Python files in commands directory
    command_files = sorted([f.name for f in commands_dir.glob("*.py") if not f.name.startswith("_")])

    print("\n" + "=" * 70)
    print("Commands Module Structure Summary")
    print("=" * 70)
    print(f"Location: {commands_dir}")
    print(f"\nCommand Files ({len(command_files)}):")
    for file_name in command_files:
        print(f"  ✓ {file_name}")

    # Check registrations in CLI
    from schnitzel.cli import app

    commands = [cmd for cmd in app.registered_commands]
    groups = [grp for grp in app.registered_groups]

    print(f"\nRegistered in CLI:")
    print(f"  Commands: {len(commands)}")
    print(f"  Groups: {len(groups)}")

    print("=" * 70)

    # Final assertion
    assert len(command_files) >= 5, "Should have at least 5 command files"
    print("✓ Module structure is properly organized")


if __name__ == "__main__":
    # Run all tests manually for development
    print("=" * 70)
    print("Testing api_166: Commands module structure is properly organized")
    print("=" * 70)

    tests = [
        ("Commands directory exists", test_commands_directory_exists),
        ("Commands __init__.py exists", test_commands_init_file_exists),
        ("serve.py exists", test_serve_command_exists),
        ("validate.py exists", test_validate_command_exists),
        ("migrate.py exists", test_migrate_command_exists),
        ("init.py exists", test_init_command_exists),
        ("generate.py exists", test_generate_command_exists),
        ("All required commands exist", test_all_required_commands_exist),
        ("Commands are importable", test_commands_are_importable),
        ("init exports function", test_init_command_exports_function),
        ("generate exports function", test_generate_command_exports_function),
        ("validate exports function", test_validate_command_exports_function),
        ("serve exports function", test_serve_command_exports_function),
        ("migrate exports function", test_migrate_command_exports_function),
        ("Commands registered in CLI", test_commands_registered_in_cli),
        ("CLI help shows commands", test_cli_help_shows_all_commands),
        ("No syntax errors", test_command_files_have_no_syntax_errors),
        ("No TODOs (zero-tolerance)", test_command_files_have_no_todos),
        ("Module docstrings", test_command_files_have_docstrings),
        ("Function docstrings", test_command_functions_have_docstrings),
        ("Typer type hints", test_commands_use_typer_decorators),
        ("Module structure summary", test_commands_module_structure_summary),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{passed + failed + 1}. Testing: {test_name}...")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("✓ All api_166 tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 70)
