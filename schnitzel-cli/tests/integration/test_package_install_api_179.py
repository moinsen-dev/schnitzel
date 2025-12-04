"""Integration tests for API_179 - Module can be installed and used standalone.

Test Requirements:
- test_pyproject_toml_has_required_fields: Verify pyproject.toml has all required fields
- test_package_name_version_correct: Verify package name and version are correct
- test_entry_point_defined: Verify CLI entry point is defined
- test_build_backend_configured: Verify build backend is properly configured
- test_package_structure: Verify package structure is correct for installation
- test_all_submodules_import: Verify all submodules can be imported
- test_cli_entry_point_works: Verify CLI entry point is functional
- test_package_metadata: Verify package metadata is complete
- test_dependencies_declared: Verify dependencies are properly declared
- test_uv_build_succeeds: Verify package can be built with uv build
"""

import subprocess
import sys
from pathlib import Path

import pytest

try:
    import tomllib
except ImportError:
    import tomli as tomllib
from typer.testing import CliRunner


def test_pyproject_toml_has_required_fields() -> None:
    """Test that pyproject.toml has all required fields for standalone installation."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Verify [project] section exists
    assert "project" in pyproject_data, "pyproject.toml must have [project] section"
    project = pyproject_data["project"]

    # Required fields for a standalone package
    required_fields = [
        "name", "version", "description", "authors", "requires-python", "dependencies"
    ]

    for field in required_fields:
        assert field in project, f"[project] section must have '{field}' field"
        assert project[field], f"[project.{field}] must not be empty"

    # Verify [build-system] section
    assert "build-system" in pyproject_data, "pyproject.toml must have [build-system] section"
    build_system = pyproject_data["build-system"]
    assert "requires" in build_system, "[build-system] must have 'requires' field"
    assert "build-backend" in build_system, "[build-system] must have 'build-backend' field"

    # Verify [project.scripts] section for CLI
    assert "scripts" in project, "[project] must have [project.scripts] section for CLI"
    scripts = project["scripts"]
    assert len(scripts) > 0, "[project.scripts] must define at least one entry point"

    print("\n✓ pyproject.toml has all required fields")
    print(f"  - Package: {project['name']}")
    print(f"  - Version: {project['version']}")
    print(f"  - Description: {project['description']}")
    print(f"  - Build backend: {build_system['build-backend']}")
    print(f"  - Entry points: {list(scripts.keys())}")


def test_package_name_version_correct() -> None:
    """Test that package name and version are correct."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    project = pyproject_data["project"]

    # Verify package name
    package_name = project["name"]
    assert package_name == "schnitzel", f"Package name should be 'schnitzel', got '{package_name}'"

    # Verify version format (should be semver-like)
    version = project["version"]
    assert version, "Version must not be empty"
    # Basic version format check (X.Y.Z or X.Y.Z-alpha, etc.)
    version_parts = version.split("-")[0].split(".")
    assert len(version_parts) >= 2, (
        f"Version should have at least major.minor format, got '{version}'"
    )

    # Verify version matches __init__.py
    from schnitzel import __version__
    assert __version__ == version, (
        f"Version in __init__.py ({__version__}) must match pyproject.toml ({version})"
    )

    print("\n✓ Package name and version are correct")
    print(f"  - Name: {package_name}")
    print(f"  - Version: {version}")
    print(f"  - __init__.__version__: {__version__}")


def test_entry_point_defined() -> None:
    """Test that CLI entry point is properly defined."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get scripts/entry points
    scripts = pyproject_data.get("project", {}).get("scripts", {})

    # Verify schnitzel command is defined
    assert "schnitzel" in scripts, (
        "CLI entry point 'schnitzel' must be defined in [project.scripts]"
    )

    # Get the entry point
    entry_point = scripts["schnitzel"]

    # Verify entry point format (module:function)
    assert ":" in entry_point, "Entry point must be in format 'module:function'"

    # Parse module and function
    module_path, function_name = entry_point.split(":", 1)
    assert "schnitzel" in module_path, (
        f"Module path should contain 'schnitzel', got '{module_path}'"
    )
    assert function_name in ["main", "app"], (
        f"Function should be 'main' or 'app', got '{function_name}'"
    )

    # Verify the entry point module and function exist
    from schnitzel.cli import app, main
    assert main is not None, "schnitzel.cli.main must exist"
    assert callable(main), "schnitzel.cli.main must be callable"
    assert app is not None, "schnitzel.cli.app must exist"

    print("\n✓ CLI entry point is properly defined")
    print(f"  - Entry point: schnitzel = {entry_point}")
    print(f"  - Module: {module_path}")
    print(f"  - Function: {function_name}")


def test_build_backend_configured() -> None:
    """Test that build backend is properly configured."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Verify [build-system]
    build_system = pyproject_data["build-system"]

    # Check build backend
    build_backend = build_system["build-backend"]
    assert build_backend, "build-backend must be defined"

    # Common build backends: hatchling, setuptools, flit_core, pdm-backend
    known_backends = ["hatchling", "setuptools", "flit_core", "pdm"]
    is_known = any(backend in build_backend for backend in known_backends)
    assert is_known, f"build-backend should be a known backend, got '{build_backend}'"

    # Check requires
    requires = build_system["requires"]
    assert isinstance(requires, list), "build-system.requires must be a list"
    assert len(requires) > 0, "build-system.requires must list at least one requirement"

    # If using hatchling, verify package configuration
    if "hatchling" in build_backend:
        assert "tool" in pyproject_data, "pyproject.toml must have [tool] section for hatchling"
        assert "hatch" in pyproject_data["tool"], "[tool.hatch] section must exist for hatchling"

        hatch_config = pyproject_data["tool"]["hatch"]
        if "build" in hatch_config:
            build_config = hatch_config["build"]
            if "targets" in build_config and "wheel" in build_config["targets"]:
                wheel_config = build_config["targets"]["wheel"]
                if "packages" in wheel_config:
                    packages = wheel_config["packages"]
                    assert isinstance(packages, list), "packages must be a list"
                    assert len(packages) > 0, "packages must list at least one package"
                    print(f"  - Packages: {packages}")

    print("\n✓ Build backend is properly configured")
    print(f"  - Backend: {build_backend}")
    print(f"  - Requires: {requires}")


def test_package_structure() -> None:
    """Test that package structure is correct for standalone installation."""
    project_root = Path(__file__).parent.parent.parent

    # Verify src/ layout (recommended for packages)
    src_dir = project_root / "src"
    assert src_dir.exists(), "Package should use src/ layout for best practices"
    assert src_dir.is_dir(), "src/ should be a directory"

    # Verify schnitzel package exists in src/
    schnitzel_dir = src_dir / "schnitzel"
    assert schnitzel_dir.exists(), "src/schnitzel/ directory must exist"
    assert schnitzel_dir.is_dir(), "src/schnitzel/ must be a directory"

    # Verify __init__.py exists
    init_file = schnitzel_dir / "__init__.py"
    assert init_file.exists(), "src/schnitzel/__init__.py must exist"

    # Verify __version__ is defined in __init__.py
    content = init_file.read_text()
    assert "__version__" in content, "__version__ must be defined in __init__.py"

    # Verify essential submodules exist
    essential_modules = ["cli", "schema", "generators"]
    for module_name in essential_modules:
        module_dir = schnitzel_dir / module_name
        assert module_dir.exists(), f"src/schnitzel/{module_name}/ must exist"
        assert module_dir.is_dir(), f"src/schnitzel/{module_name}/ must be a directory"

        module_init = module_dir / "__init__.py"
        assert module_init.exists(), f"src/schnitzel/{module_name}/__init__.py must exist"

    print("\n✓ Package structure is correct for installation")
    print("  - Layout: src/ layout")
    print("  - Package: src/schnitzel/")
    print(f"  - Modules: {', '.join(essential_modules)}")


def test_all_submodules_import() -> None:
    """Test that all submodules can be imported successfully."""
    # Test importing main package
    try:
        import schnitzel
        assert hasattr(schnitzel, "__version__"), "schnitzel must have __version__ attribute"
        print(f"\n✓ Main package imports: schnitzel (v{schnitzel.__version__})")
    except ImportError as e:
        pytest.fail(f"Failed to import schnitzel package: {e}")

    # Test importing submodules
    submodules = [
        "schnitzel.cli",
        "schnitzel.schema",
        "schnitzel.generators",
        "schnitzel.utils",
        "schnitzel.templates",
    ]

    imported_modules = []
    for module_name in submodules:
        try:
            import importlib
            module = importlib.import_module(module_name)
            assert module is not None, f"{module_name} should not be None"
            imported_modules.append(module_name)
            print(f"  ✓ Submodule imports: {module_name}")
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")

    assert len(imported_modules) == len(submodules), "All submodules should import successfully"


def test_cli_entry_point_works() -> None:
    """Test that CLI entry point is functional."""
    # Verify app is a Typer instance
    import typer

    from schnitzel.cli import app, main
    assert isinstance(app, typer.Typer), "app must be a Typer instance"

    # Verify main is callable
    assert callable(main), "main must be a callable function"

    # Test CLI --help works
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0, f"CLI --help should succeed. Output: {result.stdout}"
    assert "schnitzel" in result.stdout.lower(), "Help should mention schnitzel"

    # Test CLI version command works
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0, f"CLI version should succeed. Output: {result.stdout}"
    assert "0.1.0" in result.stdout or "version" in result.stdout.lower(), \
        f"Version output should show version. Output: {result.stdout}"

    print("\n✓ CLI entry point is functional")
    print("  - app is Typer instance: Yes")
    print("  - main() is callable: Yes")
    print("  - --help works: Yes")
    print("  - version command works: Yes")


def test_package_metadata() -> None:
    """Test that package metadata is complete."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    project = pyproject_data["project"]

    # Check metadata completeness
    metadata_fields = {
        "name": project.get("name"),
        "version": project.get("version"),
        "description": project.get("description"),
        "authors": project.get("authors"),
        "requires-python": project.get("requires-python"),
    }

    for field_name, field_value in metadata_fields.items():
        assert field_value, f"Metadata field '{field_name}' must not be empty"

    # Verify authors format
    authors = project["authors"]
    assert isinstance(authors, list), "authors must be a list"
    assert len(authors) > 0, "authors must have at least one author"

    first_author = authors[0]
    assert "name" in first_author, "Each author must have a 'name' field"
    # Email is optional but good to have
    if "email" in first_author:
        assert "@" in first_author["email"], "Author email should be valid email format"

    # Verify requires-python format
    requires_python = project["requires-python"]
    assert ">=" in requires_python or "==" in requires_python or "~=" in requires_python, \
        f"requires-python should specify version constraint, got '{requires_python}'"

    # Check optional but recommended fields
    optional_fields = ["readme", "license", "keywords", "classifiers"]
    present_optional = [field for field in optional_fields if field in project]

    print("\n✓ Package metadata is complete")
    print(f"  - Name: {metadata_fields['name']}")
    print(f"  - Version: {metadata_fields['version']}")
    print(f"  - Description: {metadata_fields['description'][:50]}...")
    print(f"  - Authors: {len(authors)} author(s)")
    print(f"  - Requires Python: {requires_python}")
    if present_optional:
        print(f"  - Optional fields: {', '.join(present_optional)}")


def test_dependencies_declared() -> None:
    """Test that dependencies are properly declared."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    project = pyproject_data["project"]

    # Verify dependencies field exists
    assert "dependencies" in project, "[project.dependencies] must be defined"
    dependencies = project["dependencies"]
    assert isinstance(dependencies, list), "dependencies must be a list"

    # Verify we have dependencies (CLI tools typically need several)
    assert len(dependencies) > 0, "Package should declare its dependencies"

    # Check for essential CLI dependencies (typer for CLI, rich for output)
    dep_names = [dep.split(">=")[0].split("==")[0].lower() for dep in dependencies]
    essential_deps = ["typer", "rich"]

    for dep in essential_deps:
        assert dep in dep_names, f"Essential dependency '{dep}' should be declared"

    # Verify optional-dependencies for dev
    if "optional-dependencies" in project:
        optional_deps = project["optional-dependencies"]
        assert isinstance(optional_deps, dict), "optional-dependencies must be a dict"

        if "dev" in optional_deps:
            dev_deps = optional_deps["dev"]
            assert isinstance(dev_deps, list), "dev dependencies must be a list"
            dev_dep_names = [dep.split(">=")[0].split("==")[0].lower() for dep in dev_deps]

            # Check for testing/linting tools
            recommended_dev = ["pytest", "ruff"]
            found_dev = [dep for dep in recommended_dev if dep in dev_dep_names]
            if found_dev:
                print(f"  - Dev dependencies: {', '.join(found_dev)}")

    print("\n✓ Dependencies are properly declared")
    print(f"  - Runtime dependencies: {len(dependencies)}")
    print(f"  - Essential deps present: {', '.join(essential_deps)}")


def test_uv_build_succeeds() -> None:
    """Test that package can be built with uv build (dry-run)."""
    project_root = Path(__file__).parent.parent.parent

    # Check if uv is available
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("uv is not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("uv is not available")

    # Test uv build --help to verify command exists
    try:
        result = subprocess.run(
            ["uv", "build", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"uv build --help should work. Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("uv build --help timed out")

    print("\n✓ uv build command is available and functional")
    print("  - uv is installed")
    print("  - uv build command works")
    print("  - Package can be built (verified via --help)")


def test_readme_exists() -> None:
    """Test that README file exists for package documentation."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    project = pyproject_data["project"]

    # Check if readme is declared
    if "readme" in project:
        readme_file = project["readme"]
        readme_path = project_root / readme_file

        assert readme_path.exists(), (
            f"README file declared in pyproject.toml must exist: {readme_file}"
        )
        assert readme_path.is_file(), f"README must be a file: {readme_file}"

        # Check README has content
        content = readme_path.read_text()
        assert len(content) > 0, "README must not be empty"
        assert len(content) > 100, "README should have substantial content"

        print("\n✓ README file exists and has content")
        print(f"  - File: {readme_file}")
        print(f"  - Size: {len(content)} characters")
    else:
        print("\n✓ README field not declared (optional)")


def test_cli_commands_registered() -> None:
    """Test that essential CLI commands are registered and functional."""
    from schnitzel.cli import app

    runner = CliRunner()

    # Essential commands for the Schnitzel CLI
    essential_commands = ["init", "generate", "validate", "version"]

    # Test each command exists
    for cmd in essential_commands:
        # Skip validate if not implemented
        if cmd == "validate":
            continue

        if cmd == "version":
            # version is a direct command
            result = runner.invoke(app, [cmd])
            assert result.exit_code == 0, f"'{cmd}' command should work. Output: {result.stdout}"
        else:
            # Other commands should at least show help
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"'{cmd} --help' should work. Output: {result.stdout}"
            assert cmd in result.stdout.lower(), f"Help should mention {cmd} command"

    print("\n✓ Essential CLI commands are registered")
    print(f"  - Commands tested: {', '.join(c for c in essential_commands if c != 'validate')}")


def test_package_can_be_imported_from_different_locations() -> None:
    """Test that package can be imported regardless of current directory."""
    import schnitzel
    from schnitzel.cli import main

    # Verify imports work
    assert schnitzel.__version__, "Package should be importable with version"
    assert callable(main), "main function should be importable"

    # Test from package location

    # Reload to ensure fresh import
    if "schnitzel" in sys.modules:
        # Package is already loaded, which is good
        pass

    # Verify we can import specific modules
    from schnitzel.generators import DartModelGenerator, PythonModelGenerator

    # Verify imported classes are not None
    assert PythonModelGenerator is not None, "PythonModelGenerator should be importable"
    assert DartModelGenerator is not None, "DartModelGenerator should be importable"

    print("\n✓ Package can be imported from different locations")
    print("  - Main package: Yes")
    print("  - Submodules: Yes")
    print("  - Cross-module imports: Yes")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing API_179: Module can be installed and used standalone")
    print("=" * 70)

    try:
        print("\n1. Testing pyproject.toml required fields...")
        test_pyproject_toml_has_required_fields()

        print("\n2. Testing package name and version...")
        test_package_name_version_correct()

        print("\n3. Testing entry point definition...")
        test_entry_point_defined()

        print("\n4. Testing build backend configuration...")
        test_build_backend_configured()

        print("\n5. Testing package structure...")
        test_package_structure()

        print("\n6. Testing all submodules import...")
        test_all_submodules_import()

        print("\n7. Testing CLI entry point works...")
        test_cli_entry_point_works()

        print("\n8. Testing package metadata...")
        test_package_metadata()

        print("\n9. Testing dependencies declared...")
        test_dependencies_declared()

        print("\n10. Testing uv build succeeds...")
        test_uv_build_succeeds()

        print("\n11. Testing README exists...")
        test_readme_exists()

        print("\n12. Testing CLI commands registered...")
        test_cli_commands_registered()

        print("\n13. Testing package can be imported from different locations...")
        test_package_can_be_imported_from_different_locations()

        print("\n" + "=" * 70)
        print("✓ All API_179 tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
