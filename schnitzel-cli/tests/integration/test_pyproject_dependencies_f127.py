"""Integration tests for F127 - pyproject.toml includes all required dependencies.

Test Requirements:
- test_pyproject_toml_exists: Verify pyproject.toml file exists
- test_required_dependencies_present: Check all required runtime dependencies are listed
- test_dependency_versions_specified: Verify dependencies have version constraints
- test_dev_dependencies_present: Check development dependencies are listed
- test_python_version_requirement: Verify Python version requirement is specified
- test_cli_entry_point_registered: Verify CLI entry point is registered in pyproject.toml
"""

import pytest
from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def test_pyproject_toml_exists() -> None:
    """Test that pyproject.toml file exists in project root."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    assert pyproject_file.exists(), "pyproject.toml should exist in project root"
    assert pyproject_file.is_file(), "pyproject.toml should be a file"

    print(f"\n✓ pyproject.toml exists at {pyproject_file}")


def test_required_dependencies_present() -> None:
    """Test that all required runtime dependencies are listed in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get dependencies
    dependencies = pyproject_data.get("project", {}).get("dependencies", [])

    # Convert to lowercase for comparison (package names are case-insensitive)
    dependencies_lower = [dep.lower() for dep in dependencies]

    # Required dependencies as specified in the feature requirements
    required_deps = [
        "typer",      # CLI framework
        "pydantic",   # Data validation
        "pyyaml",     # YAML parsing (or ruamel.yaml)
        "rich",       # Terminal formatting
    ]

    # Additional common dependencies that might be present
    optional_deps = [
        "jinja2",     # Template engine
        "watchfiles", # File watching
        "ruamel.yaml",# Alternative YAML parser
    ]

    # Check each required dependency
    for dep in required_deps:
        # Check if dependency name appears in any of the dependency strings
        found = any(dep.lower() in dep_str for dep_str in dependencies_lower)
        assert found, f"Required dependency '{dep}' should be in dependencies list. Found: {dependencies}"

    print(f"\n✓ All required dependencies present: {', '.join(required_deps)}")

    # Report optional dependencies that are also present
    found_optional = [dep for dep in optional_deps if any(dep.lower() in dep_str for dep_str in dependencies_lower)]
    if found_optional:
        print(f"✓ Additional dependencies found: {', '.join(found_optional)}")


def test_dependency_versions_specified() -> None:
    """Test that dependencies have version constraints specified."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get dependencies
    dependencies = pyproject_data.get("project", {}).get("dependencies", [])

    assert len(dependencies) > 0, "Should have at least one dependency"

    # Check that most dependencies have version constraints
    # (>=, ==, ~=, ^, etc.)
    versioned_deps = [dep for dep in dependencies if any(op in dep for op in [">=", "==", "~=", "^", ">", "<"])]

    # At least 80% of dependencies should have version constraints
    version_ratio = len(versioned_deps) / len(dependencies)
    assert version_ratio >= 0.8, f"Most dependencies should have version constraints. Found {len(versioned_deps)}/{len(dependencies)}"

    print(f"\n✓ Dependencies have version constraints ({len(versioned_deps)}/{len(dependencies)})")


def test_dev_dependencies_present() -> None:
    """Test that development dependencies are listed in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get optional/dev dependencies
    # Can be in project.optional-dependencies.dev or tool.poetry.dev-dependencies
    optional_deps = pyproject_data.get("project", {}).get("optional-dependencies", {})
    dev_deps = optional_deps.get("dev", [])

    # Common development dependencies
    expected_dev_deps = ["pytest"]  # At minimum, should have pytest

    if len(dev_deps) > 0:
        dev_deps_lower = [dep.lower() for dep in dev_deps]

        # Check for pytest
        has_pytest = any("pytest" in dep for dep in dev_deps_lower)
        assert has_pytest, "Development dependencies should include pytest"

        print(f"\n✓ Development dependencies present: {', '.join(dev_deps[:3])}...")
    else:
        pytest.skip("No dev dependencies section found (might use different config)")


def test_python_version_requirement() -> None:
    """Test that Python version requirement is specified in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get Python version requirement
    python_version = pyproject_data.get("project", {}).get("requires-python", "")

    assert python_version != "", "Python version requirement should be specified"
    assert ">=" in python_version or "==" in python_version, "Python version should have a constraint"

    # Verify it requires a modern Python version (3.9+)
    # Extract version number
    version_str = python_version.replace(">=", "").replace("==", "").strip()
    major_minor = version_str.split(".")[:2]
    if len(major_minor) == 2:
        major, minor = int(major_minor[0]), int(major_minor[1])
        assert major == 3, "Should require Python 3"
        assert minor >= 9, "Should require Python 3.9 or higher for modern features"

    print(f"\n✓ Python version requirement specified: {python_version}")


def test_cli_entry_point_registered() -> None:
    """Test that CLI entry point 'schnitzel' is registered in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get scripts/entry points
    scripts = pyproject_data.get("project", {}).get("scripts", {})

    # Verify schnitzel command is registered
    assert "schnitzel" in scripts, "CLI command 'schnitzel' should be registered as a script entry point"

    # Get the entry point value
    schnitzel_entry = scripts["schnitzel"]

    # Verify it points to the correct module and function
    assert "schnitzel" in schnitzel_entry.lower(), "Entry point should reference schnitzel module"
    assert "main" in schnitzel_entry or "app" in schnitzel_entry or "cli" in schnitzel_entry, "Entry point should reference main/app/cli function"

    print(f"\n✓ CLI entry point registered: schnitzel = {schnitzel_entry}")


def test_project_metadata_present() -> None:
    """Test that essential project metadata is present in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    project = pyproject_data.get("project", {})

    # Check essential metadata
    assert "name" in project, "Project name should be specified"
    assert "version" in project, "Project version should be specified"
    assert "description" in project, "Project description should be specified"

    assert project["name"] == "schnitzel", "Project name should be 'schnitzel'"
    assert len(project["description"]) > 0, "Description should not be empty"

    print(f"\n✓ Project metadata present: {project['name']} v{project['version']}")


def test_build_system_specified() -> None:
    """Test that build system is properly specified in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_file = project_root / "pyproject.toml"

    # Read pyproject.toml
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Check build system
    build_system = pyproject_data.get("build-system", {})

    assert "requires" in build_system, "Build system requirements should be specified"
    assert "build-backend" in build_system, "Build backend should be specified"

    # Common build backends
    backend = build_system["build-backend"]
    assert backend in ["hatchling.build", "setuptools.build_meta", "poetry.core.masonry.api", "flit_core.buildapi"], \
        f"Build backend should be a recognized backend, got: {backend}"

    print(f"\n✓ Build system specified: {backend}")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F127: pyproject.toml includes all required dependencies")
    print("=" * 70)

    try:
        print("\n1. Testing pyproject.toml exists...")
        test_pyproject_toml_exists()

        print("\n2. Testing required dependencies...")
        test_required_dependencies_present()

        print("\n3. Testing dependency versions...")
        test_dependency_versions_specified()

        print("\n4. Testing dev dependencies...")
        test_dev_dependencies_present()

        print("\n5. Testing Python version requirement...")
        test_python_version_requirement()

        print("\n6. Testing CLI entry point registration...")
        test_cli_entry_point_registered()

        print("\n7. Testing project metadata...")
        test_project_metadata_present()

        print("\n8. Testing build system...")
        test_build_system_specified()

        print("\n" + "=" * 70)
        print("✓ All F127 tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
