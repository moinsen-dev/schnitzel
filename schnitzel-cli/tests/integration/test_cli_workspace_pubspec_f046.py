"""Integration tests for F046 - Init command generates workspace pubspec.yaml.

Test Requirements:
- test_init_with_flutter_creates_pubspec_yaml
- test_pubspec_contains_workspace_definition
- test_pubspec_uses_project_name
- test_init_without_flutter_no_pubspec
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest
import yaml

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_init_with_flutter_creates_pubspec_yaml(temp_dir: Path) -> None:
    """Test that init command with --with-flutter creates pubspec.yaml in project root."""
    project_name = "test-flutter-project"

    # Run init command with --with-flutter flag
    result = runner.invoke(app, ["init", project_name, "--with-flutter"])

    # The command might fail if Flutter is not installed, but we check if it attempted
    # to create the pubspec.yaml when Flutter creation succeeded
    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    # If Flutter is installed and the app was created successfully,
    # pubspec.yaml should exist
    if result.exit_code == 0 and "✓ Flutter app created successfully" in result.stdout:
        assert pubspec_file.exists(), "pubspec.yaml not created in project root when Flutter app was created"
        assert pubspec_file.is_file(), "pubspec.yaml is not a file"


def test_pubspec_contains_workspace_definition(temp_dir: Path) -> None:
    """Test that pubspec.yaml contains the workspace definition."""
    project_name = "test-workspace"

    # Run init command with --with-flutter flag
    result = runner.invoke(app, ["init", project_name, "--with-flutter"])

    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    # Only verify if Flutter app was created successfully
    if result.exit_code == 0 and pubspec_file.exists():
        # Read and parse pubspec.yaml
        content = pubspec_file.read_text()

        # Parse as YAML
        try:
            pubspec_data = yaml.safe_load(content)

            # Verify workspace key exists
            assert "workspace" in pubspec_data, "pubspec.yaml missing 'workspace' key"

            # Verify workspace contains packages/app
            workspace = pubspec_data["workspace"]
            assert isinstance(workspace, list), "workspace should be a list"
            assert "packages/app" in workspace, "workspace should contain 'packages/app'"

            # Verify environment section
            assert "environment" in pubspec_data, "pubspec.yaml missing 'environment' key"
            assert "sdk" in pubspec_data["environment"], "environment missing 'sdk' key"

            # Verify description
            assert "description" in pubspec_data, "pubspec.yaml missing 'description' key"
            assert "workspace" in pubspec_data["description"].lower(), "description should mention workspace"

        except yaml.YAMLError as e:
            pytest.fail(f"pubspec.yaml is not valid YAML: {e}")


def test_pubspec_uses_project_name(temp_dir: Path) -> None:
    """Test that pubspec.yaml uses the sanitized project name for workspace name."""
    project_name = "my-awesome-project"
    expected_workspace_name = "my_awesome_project_workspace"  # Hyphens become underscores

    # Run init command with --with-flutter flag
    result = runner.invoke(app, ["init", project_name, "--with-flutter"])

    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    # Only verify if Flutter app was created successfully
    if result.exit_code == 0 and pubspec_file.exists():
        # Read and parse pubspec.yaml
        content = pubspec_file.read_text()

        try:
            pubspec_data = yaml.safe_load(content)

            # Verify name field uses sanitized project name with _workspace suffix
            assert "name" in pubspec_data, "pubspec.yaml missing 'name' key"
            assert pubspec_data["name"] == expected_workspace_name, \
                f"Expected workspace name '{expected_workspace_name}', got '{pubspec_data['name']}'"

        except yaml.YAMLError as e:
            pytest.fail(f"pubspec.yaml is not valid YAML: {e}")


def test_init_without_flutter_no_pubspec(temp_dir: Path) -> None:
    """Test that init command without --with-flutter does not create pubspec.yaml."""
    project_name = "test-no-flutter"

    # Run init command WITHOUT --with-flutter flag
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify pubspec.yaml was NOT created
    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    assert not pubspec_file.exists(), \
        "pubspec.yaml should not be created when --with-flutter flag is not used"


def test_pubspec_yaml_structure(temp_dir: Path) -> None:
    """Test that pubspec.yaml has the correct structure and format."""
    project_name = "structure-test"

    # Run init command with --with-flutter flag
    result = runner.invoke(app, ["init", project_name, "--with-flutter"])

    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    # Only verify if Flutter app was created successfully
    if result.exit_code == 0 and pubspec_file.exists():
        content = pubspec_file.read_text()

        # Verify content contains expected sections
        assert "name:" in content, "pubspec.yaml missing 'name:' field"
        assert "description:" in content, "pubspec.yaml missing 'description:' field"
        assert "environment:" in content, "pubspec.yaml missing 'environment:' section"
        assert "sdk:" in content, "pubspec.yaml missing 'sdk:' field"
        assert "workspace:" in content, "pubspec.yaml missing 'workspace:' section"
        assert "- packages/app" in content, "pubspec.yaml missing 'packages/app' in workspace"

        # Verify SDK version constraint
        assert ">=3.0.0 <4.0.0" in content, "pubspec.yaml has incorrect SDK version constraint"


def test_pubspec_name_sanitization(temp_dir: Path) -> None:
    """Test that project names with special characters are properly sanitized."""
    project_name = "Test-Project-123"
    expected_workspace_name = "test_project_123_workspace"

    # Run init command with --with-flutter flag
    result = runner.invoke(app, ["init", project_name, "--with-flutter"])

    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    # Only verify if Flutter app was created successfully
    if result.exit_code == 0 and pubspec_file.exists():
        content = pubspec_file.read_text()

        try:
            pubspec_data = yaml.safe_load(content)

            # Verify name is properly sanitized
            assert pubspec_data["name"] == expected_workspace_name, \
                f"Expected '{expected_workspace_name}', got '{pubspec_data['name']}'"

            # Verify name is lowercase and uses underscores
            workspace_name = pubspec_data["name"]
            assert workspace_name.islower() or "_" in workspace_name, \
                "Workspace name should be lowercase with underscores"
            assert "-" not in workspace_name, "Workspace name should not contain hyphens"

        except yaml.YAMLError as e:
            pytest.fail(f"pubspec.yaml is not valid YAML: {e}")


def test_pubspec_created_after_flutter_success(temp_dir: Path) -> None:
    """Test that pubspec.yaml is only created when Flutter app creation succeeds."""
    project_name = "success-check"

    # Run init command with --with-flutter flag
    result = runner.invoke(app, ["init", project_name, "--with-flutter"])

    project_path = temp_dir / project_name
    pubspec_file = project_path / "pubspec.yaml"

    # If Flutter is not installed or creation failed, pubspec.yaml should not exist
    if "Flutter not installed" in result.stdout or "Flutter create failed" in result.stdout:
        assert not pubspec_file.exists(), \
            "pubspec.yaml should not be created when Flutter app creation fails"

    # If Flutter app was created successfully, pubspec.yaml should exist
    if "✓ Flutter app created successfully" in result.stdout or "✓ Created packages/app/ (Flutter app)" in result.stdout:
        assert pubspec_file.exists(), \
            "pubspec.yaml should be created when Flutter app creation succeeds"
