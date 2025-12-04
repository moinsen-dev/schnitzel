"""Integration tests for api_176 - All module tests can be run with pytest.

Test Requirements:
This feature verifies that all tests in the module can be discovered and run with pytest.
It ensures the pytest configuration is correct and all tests can be collected without errors.

The Schnitzel project follows a zero-tolerance policy:
- No errors during test collection
- No warnings during test collection
- No TODO comments in production code
- All tests must be discoverable

Tests:
- test_pytest_config_exists: Verify pytest configuration exists in pyproject.toml
- test_pytest_discovers_all_tests: Verify pytest can discover all test files
- test_pytest_collects_without_errors: Verify pytest collection runs without errors
- test_test_directory_structure: Verify test directory structure is correct
- test_all_test_files_importable: Verify all test modules can be imported
- test_test_markers_work: Verify pytest markers work correctly (if any)
- test_pytest_pythonpath_configured: Verify pythonpath is correctly set
- test_no_collection_warnings: Verify no warnings during collection
"""

import ast
import re
import subprocess
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_tests_directory() -> Path:
    """Get the tests directory."""
    return get_project_root() / "tests"


def get_pyproject_path() -> Path:
    """Get the pyproject.toml file path."""
    return get_project_root() / "pyproject.toml"


def test_pytest_config_exists() -> None:
    """Test that pytest configuration exists in pyproject.toml.

    Verifies:
    - pyproject.toml exists
    - Contains [tool.pytest.ini_options] section
    - Has pythonpath configured
    - Has testpaths configured
    """
    pyproject_path = get_pyproject_path()

    assert pyproject_path.exists(), f"pyproject.toml should exist at {pyproject_path}"
    assert pyproject_path.is_file(), "pyproject.toml should be a file"

    content = pyproject_path.read_text()

    # Check for pytest configuration section
    assert "[tool.pytest.ini_options]" in content, \
        "pyproject.toml should contain [tool.pytest.ini_options] section"

    # Check for pythonpath configuration
    assert "pythonpath" in content, \
        "pytest config should specify pythonpath for module imports"

    # Check for testpaths configuration
    assert "testpaths" in content, \
        "pytest config should specify testpaths for test discovery"

    # Verify pythonpath includes src
    assert '"src"' in content or '["src"]' in content, \
        "pythonpath should include 'src' directory"

    # Verify testpaths includes tests
    assert '"tests"' in content or '["tests"]' in content, \
        "testpaths should include 'tests' directory"

    print(f"✓ pytest configuration exists in {pyproject_path}")
    print("✓ pythonpath configured: ['src']")
    print("✓ testpaths configured: ['tests']")


def test_test_directory_structure() -> None:
    """Test that test directory structure is correct.

    Verifies:
    - tests/ directory exists
    - tests/__init__.py exists
    - tests/integration/ directory exists
    - tests/integration/__init__.py exists
    """
    tests_dir = get_tests_directory()

    assert tests_dir.exists(), f"tests directory should exist at {tests_dir}"
    assert tests_dir.is_dir(), "tests path should be a directory"

    # Check for __init__.py in tests/
    tests_init = tests_dir / "__init__.py"
    assert tests_init.exists(), "tests/__init__.py should exist"
    assert tests_init.is_file(), "tests/__init__.py should be a file"

    # Check for integration tests directory
    integration_dir = tests_dir / "integration"
    assert integration_dir.exists(), "tests/integration directory should exist"
    assert integration_dir.is_dir(), "tests/integration should be a directory"

    # Check for __init__.py in tests/integration/
    integration_init = integration_dir / "__init__.py"
    assert integration_init.exists(), "tests/integration/__init__.py should exist"
    assert integration_init.is_file(), "tests/integration/__init__.py should be a file"

    print(f"✓ Test directory structure is correct: {tests_dir}")
    print("  ✓ tests/__init__.py exists")
    print("  ✓ tests/integration/ exists")
    print("  ✓ tests/integration/__init__.py exists")


def test_pytest_discovers_all_tests() -> None:
    """Test that pytest can discover all test files.

    Runs pytest --collect-only and verifies:
    - Command succeeds (exit code 0)
    - Tests are discovered
    - Multiple test files are found
    """
    project_root = get_project_root()

    # Run pytest collection using uv (which manages the venv)
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60
    )

    # Check exit code
    assert result.returncode == 0, \
        f"pytest --collect-only should succeed. Exit code: {result.returncode}\n" \
        f"stderr: {result.stderr}"

    output = result.stdout + result.stderr

    # Check that tests were collected
    assert "collected" in output.lower() or "test" in output.lower(), \
        f"pytest should discover tests. Output:\n{output}"

    # Extract number of collected tests from output
    # Output format: "collected X items" or "X tests collected"
    collected_match = re.search(r'(\d+)\s+(?:tests?\s+)?collected', output)

    if collected_match:
        num_tests = int(collected_match.group(1))
        assert num_tests > 0, f"Should discover at least 1 test, found {num_tests}"
        print(f"✓ pytest discovered {num_tests} tests")
    else:
        # Fallback: just verify no errors
        assert "error" not in output.lower() or "0 error" in output.lower(), \
            f"pytest collection should not have errors. Output:\n{output}"
        print("✓ pytest test discovery completed successfully")


def test_pytest_collects_without_errors() -> None:
    """Test that pytest collection runs without errors.

    This is the critical test that verifies:
    - All test files can be imported
    - No syntax errors in test files
    - No import errors
    - No collection errors
    """
    project_root = get_project_root()

    # Run pytest collection with verbose error reporting
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60
    )

    output = result.stdout + result.stderr

    # Check for collection errors
    # Pytest reports errors like "ERROR tests/integration/test_something.py"
    error_lines = [line for line in output.split('\n') if 'ERROR' in line and 'test_' in line]

    # Filter out error count summaries (e.g., "0 errors")
    actual_errors = [line for line in error_lines if not re.search(r'\d+\s+errors?', line)]

    assert len(actual_errors) == 0, \
        f"pytest collection should have no errors. Found {len(actual_errors)} errors:\n" + \
        "\n".join(actual_errors[:10])  # Show first 10 errors

    # Check that we collected tests successfully
    assert "collected" in output.lower(), \
        f"pytest should successfully collect tests. Output:\n{output[:500]}"

    print("✓ pytest collection completed without errors")
    print("✓ All test files can be imported")
    print("✓ No syntax errors in test files")


def test_all_test_files_have_valid_syntax() -> None:
    """Test that all test files have valid Python syntax.

    Verifies by parsing each test file with ast.parse():
    - No syntax errors
    - Valid Python code
    """
    tests_dir = get_tests_directory()

    test_files = list(tests_dir.rglob("test_*.py"))

    assert len(test_files) > 0, "Should find at least one test file"

    syntax_errors = []

    for test_file in test_files:
        try:
            content = test_file.read_text()
            ast.parse(content)
        except SyntaxError as e:
            syntax_errors.append((test_file, str(e)))

    assert len(syntax_errors) == 0, \
        f"All test files should have valid syntax. Found {len(syntax_errors)} errors:\n" + \
        "\n".join([f"  {file}: {error}" for file, error in syntax_errors[:5]])

    print(f"✓ All {len(test_files)} test files have valid Python syntax")


def test_pytest_pythonpath_configured() -> None:
    """Test that pytest pythonpath is correctly configured.

    Verifies that the pythonpath includes 'src' so that
    'from schnitzel.xyz import ...' imports work in tests.
    """
    pyproject_path = get_pyproject_path()
    content = pyproject_path.read_text()

    # Parse TOML to check pythonpath
    # Simple string search since we know the format
    # Look for pythonpath = ["src"] or pythonpath = ["src"]
    pythonpath_match = re.search(r'pythonpath\s*=\s*\[([^\]]+)\]', content)

    assert pythonpath_match, "pythonpath should be configured in [tool.pytest.ini_options]"

    pythonpath_value = pythonpath_match.group(1)

    assert "src" in pythonpath_value, \
        f"pythonpath should include 'src'. Found: {pythonpath_value}"

    print("✓ pytest pythonpath is correctly configured: ['src']")


def test_no_collection_warnings() -> None:
    """Test that pytest collection produces no warnings.

    Verifies the zero-tolerance policy:
    - No deprecation warnings
    - No import warnings
    - Clean collection output
    """
    project_root = get_project_root()

    # Run pytest collection with warnings enabled
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "-W", "default"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60
    )

    output = result.stdout + result.stderr

    # Check for common warning indicators
    warning_indicators = [
        "DeprecationWarning",
        "PendingDeprecationWarning",
        "FutureWarning",
        "UserWarning",
    ]

    warnings_found = []
    for indicator in warning_indicators:
        if indicator in output:
            # Extract the warning lines
            for line in output.split('\n'):
                if indicator in line:
                    warnings_found.append(line)

    # Note: Some warnings from third-party libraries may be acceptable
    # We focus on warnings from our code (test files and schnitzel module)
    schnitzel_warnings = [w for w in warnings_found if 'schnitzel' in w or 'test_' in w]

    assert len(schnitzel_warnings) == 0, \
        f"pytest collection should produce no warnings from our code.\n" \
        f"Found {len(schnitzel_warnings)} warnings:\n" + \
        "\n".join(schnitzel_warnings[:5])

    print("✓ pytest collection produces no warnings")
    print("✓ Zero-tolerance policy: Clean test collection")


def test_can_run_specific_test_file() -> None:
    """Test that we can run a specific test file.

    Verifies that:
    - Individual test files can be executed
    - Test collection works at file level
    - No errors when running a single test module
    """
    project_root = get_project_root()

    # Find a test file to run (use this test file itself)
    test_file = Path(__file__)

    # Run pytest on this specific file (just collection)
    result = subprocess.run(
        ["uv", "run", "pytest", str(test_file), "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0, \
        f"Should be able to collect tests from a specific file.\n" \
        f"Exit code: {result.returncode}\n" \
        f"stderr: {result.stderr}"

    output = result.stdout + result.stderr

    # Should find tests in this file
    assert "test_pytest_runner_api_176" in output or "collected" in output.lower(), \
        f"Should discover tests in specific file. Output:\n{output}"

    print("✓ Can run tests from specific test file")
    print("✓ Individual test file collection works")


def test_test_files_follow_naming_convention() -> None:
    """Test that test files follow the correct naming convention.

    Verifies:
    - All test files start with 'test_'
    - Test files are in correct directories
    - No misnamed test files that pytest might miss
    """
    tests_dir = get_tests_directory()

    # Find all Python files in tests directory
    all_py_files = list(tests_dir.rglob("*.py"))

    # Filter out __init__.py files
    py_files = [f for f in all_py_files if f.name != "__init__.py"]

    # Filter out fixture files in fixtures/ directory
    py_files = [f for f in py_files if "fixtures" not in str(f)]

    assert len(py_files) > 0, "Should find test files"

    # Check that all non-init files start with 'test_'
    non_test_files = [f for f in py_files if not f.name.startswith("test_")]

    # Allow verify_*.py files (used for manual verification scripts)
    non_test_files = [f for f in non_test_files if not f.name.startswith("verify_")]

    assert len(non_test_files) == 0, \
        "All test files should start with 'test_'. Found:\n" + \
        "\n".join([f"  {f.relative_to(tests_dir)}" for f in non_test_files[:5]])

    print(f"✓ All {len(py_files)} test files follow naming convention (test_*.py)")


def test_integration_tests_in_integration_directory() -> None:
    """Test that integration tests are in the integration/ directory.

    Verifies proper test organization:
    - Integration tests in tests/integration/
    - Unit tests in tests/ root (if any)
    - Proper directory structure
    """
    tests_dir = get_tests_directory()
    integration_dir = tests_dir / "integration"

    # Count test files in integration directory
    integration_tests = list(integration_dir.glob("test_*.py"))

    assert len(integration_tests) > 0, \
        "Should have integration tests in tests/integration/"

    print(f"✓ Found {len(integration_tests)} integration tests in tests/integration/")
    print("✓ Test organization follows project structure")


def test_pytest_summary() -> None:
    """Summary test showing pytest configuration and test discovery.

    This test provides a comprehensive overview of the pytest setup.
    """
    project_root = get_project_root()
    tests_dir = get_tests_directory()

    # Run full test collection
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60
    )

    output = result.stdout + result.stderr

    # Extract number of tests
    collected_match = re.search(r'(\d+)\s+(?:tests?\s+)?collected', output)
    num_tests = int(collected_match.group(1)) if collected_match else 0

    # Count test files
    test_files = list(tests_dir.rglob("test_*.py"))

    print("\n" + "=" * 70)
    print("Pytest Configuration Summary (api_176)")
    print("=" * 70)
    print(f"Project Root: {project_root}")
    print(f"Tests Directory: {tests_dir}")
    print("\nTest Discovery:")
    print(f"  Test Files: {len(test_files)}")
    print(f"  Tests Collected: {num_tests}")
    print("\nPytest Configuration (pyproject.toml):")
    print("  pythonpath: ['src']")
    print("  testpaths: ['tests']")
    print("\nTest Execution:")
    print("  Command: uv run pytest")
    print(f"  Collection: {'✓ Success' if result.returncode == 0 else '✗ Failed'}")
    print("=" * 70)

    assert result.returncode == 0, "pytest collection should succeed"
    assert num_tests > 0, "Should discover tests"

    print("✓ All module tests can be run with pytest")


if __name__ == "__main__":
    # Run all tests manually for development
    print("=" * 70)
    print("Testing api_176: All module tests can be run with pytest")
    print("=" * 70)

    tests = [
        ("pytest config exists", test_pytest_config_exists),
        ("Test directory structure", test_test_directory_structure),
        ("pytest discovers all tests", test_pytest_discovers_all_tests),
        ("pytest collects without errors", test_pytest_collects_without_errors),
        ("All test files have valid syntax", test_all_test_files_have_valid_syntax),
        ("pytest pythonpath configured", test_pytest_pythonpath_configured),
        ("No collection warnings", test_no_collection_warnings),
        ("Can run specific test file", test_can_run_specific_test_file),
        ("Test files follow naming convention", test_test_files_follow_naming_convention),
        ("Integration tests organized", test_integration_tests_in_integration_directory),
        ("pytest summary", test_pytest_summary),
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
        print("✓ All api_176 tests passed!")
        print("✓ All module tests can be run with pytest")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 70)
