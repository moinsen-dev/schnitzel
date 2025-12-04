"""Integration tests for F111 - Init command creates README.md with getting started instructions.

Test Requirements:
- test_readme_created - Verify README.md is created
- test_readme_has_instructions - Verify README has getting started content
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

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


def test_readme_created(temp_dir: Path) -> None:
    """Test that init command creates README.md in project root."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify README.md was created
    readme_path = temp_dir / project_name / "README.md"
    assert readme_path.exists(), f"README.md not created at {readme_path}"
    assert readme_path.is_file(), "README.md is not a file"

    # Verify README.md is not empty
    readme_content = readme_path.read_text()
    assert len(readme_content) > 0, "README.md is empty"


def test_readme_has_instructions(temp_dir: Path) -> None:
    """Test that README.md contains getting started instructions."""
    project_name = "my-awesome-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read README content
    readme_path = temp_dir / project_name / "README.md"
    readme_content = readme_path.read_text()

    # Verify project name in title
    assert f"# {project_name}" in readme_content, "README missing project name in title"

    # Verify getting started section
    assert "Getting Started" in readme_content or "getting started" in readme_content.lower(), \
        "README missing getting started section"

    # Verify prerequisites section
    assert "Prerequisites" in readme_content or "prerequisites" in readme_content.lower(), \
        "README missing prerequisites section"

    # Verify key prerequisites are mentioned
    assert "Flutter" in readme_content or "flutter" in readme_content.lower(), \
        "README should mention Flutter"
    assert "Python" in readme_content or "python" in readme_content.lower(), \
        "README should mention Python"
    assert "Docker" in readme_content or "docker" in readme_content.lower(), \
        "README should mention Docker"

    # Verify quick start/setup instructions
    assert "schnitzel generate" in readme_content.lower(), \
        "README missing 'schnitzel generate' instruction"

    # Verify schema file is mentioned
    assert "schema.schnitzel.yaml" in readme_content, \
        "README should reference schema.schnitzel.yaml"


def test_readme_has_project_structure(temp_dir: Path) -> None:
    """Test that README.md contains project structure information."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Read README content
    readme_path = temp_dir / project_name / "README.md"
    readme_content = readme_path.read_text()

    # Verify project structure section exists
    assert "Project Structure" in readme_content or "project structure" in readme_content.lower(), \
        "README missing project structure section"

    # Verify key directories are mentioned
    assert "backend" in readme_content.lower(), "README should mention backend directory"
    assert "packages" in readme_content.lower() or "app" in readme_content.lower(), \
        "README should mention packages/app directory"


def test_readme_has_next_steps(temp_dir: Path) -> None:
    """Test that README.md contains next steps guidance."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Read README content
    readme_path = temp_dir / project_name / "README.md"
    readme_content = readme_path.read_text()

    # Verify next steps section
    assert "Next Steps" in readme_content or "next steps" in readme_content.lower(), \
        "README missing next steps section"


def test_readme_creation_shown_in_output(temp_dir: Path) -> None:
    """Test that init command output indicates README.md creation."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify README creation is mentioned in output
    output_lower = result.stdout.lower()
    assert "readme" in output_lower or "README.md" in result.stdout, \
        "Output should mention README.md creation"


def test_readme_with_different_project_names(temp_dir: Path) -> None:
    """Test that README.md adapts to different project names."""
    project_names = ["simple", "my-complex-project", "test_app_123"]

    for project_name in project_names:
        # Run init command
        result = runner.invoke(app, ["init", project_name])
        assert result.exit_code == 0, f"Command failed for {project_name}"

        # Read README content
        readme_path = temp_dir / project_name / "README.md"
        readme_content = readme_path.read_text()

        # Verify project name appears in README
        assert project_name in readme_content, \
            f"README should contain project name '{project_name}'"


def test_readme_with_template_option(temp_dir: Path) -> None:
    """Test that README.md is created regardless of template choice."""
    project_name = "full-template-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    # Verify README.md exists
    readme_path = temp_dir / project_name / "README.md"
    assert readme_path.exists(), "README.md not created with full template"
    assert readme_path.is_file()

    # Verify content
    readme_content = readme_path.read_text()
    assert len(readme_content) > 100, "README.md should have substantial content"
    assert project_name in readme_content


def test_readme_force_overwrite(temp_dir: Path) -> None:
    """Test that README.md is recreated when using --force flag."""
    project_name = "test-project"

    # Create project first time
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify initial README
    readme_path = temp_dir / project_name / "README.md"
    assert readme_path.exists()

    # Recreate project with --force
    result = runner.invoke(app, ["init", project_name, "--force"])
    assert result.exit_code == 0

    # Verify README still exists
    assert readme_path.exists(), "README.md should be recreated with --force"
    readme_content = readme_path.read_text()
    assert len(readme_content) > 0, "README.md should have content after force recreation"
