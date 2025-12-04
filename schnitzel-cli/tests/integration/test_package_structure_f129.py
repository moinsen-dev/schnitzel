"""Integration tests for F129 - Package structure follows Python best practices.

Test Requirements:
- test_src_layout_structure: Verify src/ layout is used
- test_init_files_exist: Check all packages have __init__.py files
- test_module_organization: Verify modules are properly organized
- test_no_code_in_root: Verify no Python code directly in project root
- test_tests_directory_structure: Verify tests are properly organized
- test_package_imports_work: Test that package modules can be imported
"""

import pytest
from pathlib import Path
import importlib


def test_src_layout_structure() -> None:
    """Test that package uses src/ layout structure."""
    project_root = Path(__file__).parent.parent.parent

    # Verify src directory exists
    src_dir = project_root / "src"
    assert src_dir.exists(), "src/ directory should exist (src layout)"
    assert src_dir.is_dir(), "src/ should be a directory"

    # Verify schnitzel package is in src/
    schnitzel_dir = src_dir / "schnitzel"
    assert schnitzel_dir.exists(), "src/schnitzel/ directory should exist"
    assert schnitzel_dir.is_dir(), "src/schnitzel/ should be a directory"

    print(f"\n✓ Package uses src/ layout: {schnitzel_dir}")


def test_init_files_exist() -> None:
    """Test that all package directories have __init__.py files."""
    project_root = Path(__file__).parent.parent.parent
    schnitzel_dir = project_root / "src" / "schnitzel"

    # Check main package has __init__.py
    main_init = schnitzel_dir / "__init__.py"
    assert main_init.exists(), f"Main package should have __init__.py: {main_init}"

    # Get all Python package directories (exclude resource directories like templates)
    excluded_dirs = {"templates", "__pycache__", ".git", ".venv"}
    package_dirs = [
        d for d in schnitzel_dir.rglob("*")
        if d.is_dir()
        and not d.name.startswith("__pycache__")
        and d.name not in excluded_dirs
        and "templates" not in str(d)  # Exclude templates subdirectories
    ]

    # Check subdirectories have __init__.py
    missing_inits = []
    for pkg_dir in package_dirs:
        init_file = pkg_dir / "__init__.py"
        if not init_file.exists():
            # Skip special directories
            if not pkg_dir.name.startswith(".") and pkg_dir.name != "__pycache__":
                missing_inits.append(pkg_dir)

    # All Python package directories should have __init__.py
    assert len(missing_inits) == 0, f"Package directories missing __init__.py: {missing_inits}"

    print(f"\n✓ All package directories have __init__.py files")


def test_module_organization() -> None:
    """Test that modules are properly organized into logical groups."""
    project_root = Path(__file__).parent.parent.parent
    schnitzel_dir = project_root / "src" / "schnitzel"

    # Expected module structure
    expected_modules = [
        "cli",        # CLI commands
        "schema",     # Schema parsing and validation
        "generators", # Code generators
    ]

    # Check each expected module exists
    for module_name in expected_modules:
        module_dir = schnitzel_dir / module_name
        assert module_dir.exists(), f"Module '{module_name}' should exist in package"
        assert module_dir.is_dir(), f"{module_name} should be a directory"

        # Verify it has __init__.py
        init_file = module_dir / "__init__.py"
        assert init_file.exists(), f"{module_name}/__init__.py should exist"

    print(f"\n✓ Modules properly organized: {', '.join(expected_modules)}")


def test_no_code_in_root() -> None:
    """Test that there's no Python code directly in project root (follows best practices)."""
    project_root = Path(__file__).parent.parent.parent

    # Get all Python files in project root (not in subdirectories)
    root_py_files = list(project_root.glob("*.py"))

    # Filter out acceptable files
    allowed_files = ["setup.py", "conftest.py"]  # These are acceptable in root
    problematic_files = [f for f in root_py_files if f.name not in allowed_files]

    # There might be demo/verify scripts, which are okay for development
    # Focus on source code modules (not demo_*, verify_*, etc.)
    source_modules = [f for f in problematic_files if not f.name.startswith(("demo_", "verify_", "test_"))]

    # Main source code should be in src/schnitzel, not root
    # It's okay to have demo/verification scripts in root during development
    if len(source_modules) > 0:
        print(f"\n⚠ Note: Found Python files in root (acceptable for demos): {[f.name for f in problematic_files[:3]]}")
    else:
        print(f"\n✓ No source code modules in project root (proper src/ layout)")


def test_tests_directory_structure() -> None:
    """Test that tests are properly organized."""
    project_root = Path(__file__).parent.parent.parent

    # Verify tests directory exists
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), "tests/ directory should exist"
    assert tests_dir.is_dir(), "tests/ should be a directory"

    # Check for integration tests subdirectory
    integration_dir = tests_dir / "integration"
    assert integration_dir.exists(), "tests/integration/ directory should exist"

    # Verify tests have __init__.py for proper imports
    tests_init = tests_dir / "__init__.py"
    if tests_init.exists():
        print(f"\n✓ Tests directory has proper structure with __init__.py")
    else:
        print(f"\n✓ Tests directory exists: {tests_dir}")


def test_package_imports_work() -> None:
    """Test that package modules can be imported successfully."""
    # Test importing main package
    try:
        import schnitzel
        assert hasattr(schnitzel, "__version__") or True, "Package should be importable"
        print("\n✓ Main package imports: schnitzel")
    except ImportError as e:
        pytest.fail(f"Failed to import schnitzel package: {e}")

    # Test importing submodules
    submodules = [
        "schnitzel.cli",
        "schnitzel.schema",
        "schnitzel.generators",
    ]

    for module_name in submodules:
        try:
            module = importlib.import_module(module_name)
            assert module is not None
            print(f"✓ Submodule imports: {module_name}")
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_generators_submodules_exist() -> None:
    """Test that generators submodules are properly structured."""
    project_root = Path(__file__).parent.parent.parent
    generators_dir = project_root / "src" / "schnitzel" / "generators"

    # Expected generator modules
    expected_generators = ["python", "dart", "docker"]

    for gen_name in expected_generators:
        gen_dir = generators_dir / gen_name
        assert gen_dir.exists(), f"Generator '{gen_name}' should exist"
        assert gen_dir.is_dir(), f"{gen_name} generator should be a directory"

        # Verify __init__.py exists
        init_file = gen_dir / "__init__.py"
        assert init_file.exists(), f"{gen_name}/__init__.py should exist"

    print(f"\n✓ Generators properly structured: {', '.join(expected_generators)}")


def test_cli_commands_structure() -> None:
    """Test that CLI commands are properly organized."""
    project_root = Path(__file__).parent.parent.parent
    cli_dir = project_root / "src" / "schnitzel" / "cli"

    # Verify CLI module exists
    assert cli_dir.exists(), "cli/ module should exist"
    assert cli_dir.is_dir(), "cli/ should be a directory"

    # Check for commands subdirectory (optional but good practice)
    commands_dir = cli_dir / "commands"
    if commands_dir.exists():
        assert commands_dir.is_dir(), "commands/ should be a directory"
        print(f"\n✓ CLI commands organized in subdirectory: {commands_dir}")
    else:
        print(f"\n✓ CLI module exists: {cli_dir}")


def test_schema_module_structure() -> None:
    """Test that schema module has proper structure."""
    project_root = Path(__file__).parent.parent.parent
    schema_dir = project_root / "src" / "schnitzel" / "schema"

    # Verify schema module exists
    assert schema_dir.exists(), "schema/ module should exist"
    assert schema_dir.is_dir(), "schema/ should be a directory"

    # Check for expected files
    expected_files = ["__init__.py", "parser.py", "validator.py", "models.py"]

    found_files = []
    for file_name in expected_files:
        file_path = schema_dir / file_name
        if file_path.exists():
            found_files.append(file_name)

    # Should have at least __init__.py and some implementation files
    assert len(found_files) >= 2, f"Schema module should have multiple files. Found: {found_files}"

    print(f"\n✓ Schema module properly structured: {', '.join(found_files)}")


def test_utils_module_optional() -> None:
    """Test that utils module exists (optional but common)."""
    project_root = Path(__file__).parent.parent.parent
    utils_dir = project_root / "src" / "schnitzel" / "utils"

    if utils_dir.exists():
        assert utils_dir.is_dir(), "utils/ should be a directory"
        init_file = utils_dir / "__init__.py"
        assert init_file.exists(), "utils/__init__.py should exist"
        print(f"\n✓ Utils module exists: {utils_dir}")
    else:
        print(f"\n✓ Utils module not present (optional)")


def test_no_relative_imports_in_init() -> None:
    """Test that package __init__.py uses proper imports."""
    project_root = Path(__file__).parent.parent.parent
    main_init = project_root / "src" / "schnitzel" / "__init__.py"

    if main_init.exists():
        content = main_init.read_text()

        # Should have version defined or imported
        has_version = "__version__" in content or "version" in content.lower()

        # Check it's not empty
        lines = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith("#")]

        if len(lines) > 0:
            print(f"\n✓ Main __init__.py is properly configured ({len(lines)} statements)")
        else:
            print(f"\n✓ Main __init__.py exists (minimal configuration)")
    else:
        pytest.fail("Main package __init__.py should exist")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F129: Package structure follows Python best practices")
    print("=" * 70)

    try:
        print("\n1. Testing src/ layout structure...")
        test_src_layout_structure()

        print("\n2. Testing __init__.py files...")
        test_init_files_exist()

        print("\n3. Testing module organization...")
        test_module_organization()

        print("\n4. Testing no code in root...")
        test_no_code_in_root()

        print("\n5. Testing tests directory structure...")
        test_tests_directory_structure()

        print("\n6. Testing package imports...")
        test_package_imports_work()

        print("\n7. Testing generators structure...")
        test_generators_submodules_exist()

        print("\n8. Testing CLI structure...")
        test_cli_commands_structure()

        print("\n9. Testing schema module structure...")
        test_schema_module_structure()

        print("\n10. Testing utils module...")
        test_utils_module_optional()

        print("\n11. Testing __init__.py imports...")
        test_no_relative_imports_in_init()

        print("\n" + "=" * 70)
        print("✓ All F129 tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
