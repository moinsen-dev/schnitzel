"""Integration tests for F049 - Init command displays progress with Rich.

Test Requirements:
- test_init_shows_creating_message
- test_init_shows_success_indicators
- test_init_shows_next_steps
- test_init_output_includes_project_name
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


def test_init_shows_creating_message(temp_dir: Path) -> None:
    """Test that init command shows 'Creating project: {name}' message."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify output includes creating message
    assert "Creating project:" in result.stdout, "Missing 'Creating project:' message"
    assert project_name in result.stdout, f"Project name '{project_name}' not in output"


def test_init_shows_success_indicators(temp_dir: Path) -> None:
    """Test that init command shows ✓ success indicators for each step."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Verify success indicators (✓) are shown
    assert "✓" in output, "Missing success indicators (✓)"

    # Verify specific success messages for key components
    # At minimum, should show success for schema and docker-compose
    assert "schema.schnitzel.yaml" in output, "Missing schema.schnitzel.yaml in output"
    assert "docker-compose.yaml" in output, "Missing docker-compose.yaml in output"
    assert "packages/app" in output, "Missing packages/app in output"
    assert "backend/app" in output, "Missing backend/app in output"


def test_init_shows_next_steps(temp_dir: Path) -> None:
    """Test that init command shows next steps with clear guidance."""
    project_name = "my-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Verify next steps section exists
    assert "Next steps:" in output, "Missing 'Next steps:' section"

    # Verify specific next steps are mentioned
    assert f"cd {project_name}" in output, f"Missing 'cd {project_name}' instruction"
    assert "schema.schnitzel.yaml" in output, "Missing schema editing instruction"
    assert "schnitzel generate" in output, "Missing 'schnitzel generate' instruction"


def test_init_output_includes_project_name(temp_dir: Path) -> None:
    """Test that init command output includes the project name in multiple places."""
    project_name = "my-custom-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Project name should appear at the start (creating message)
    assert "Creating project:" in output and project_name in output, \
        "Project name missing from creating message"

    # Project name should appear in next steps
    assert f"cd {project_name}" in output, "Project name missing from next steps"


def test_init_shows_final_success_message(temp_dir: Path) -> None:
    """Test that init command shows final success message."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout.lower()

    # Verify final success message with ✓
    assert "project created successfully" in output or "✓" in output, \
        "Missing final success message"


def test_init_progress_shows_all_created_files(temp_dir: Path) -> None:
    """Test that progress indicators show all created files and directories."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Should show creation of:
    # - schema.schnitzel.yaml
    # - packages/app/
    # - backend/app/
    # - docker-compose.yaml

    # Check for key file mentions with success indicators
    lines_with_checkmark = [line for line in output.split('\n') if '✓' in line]

    # Should have at least 4 success indicators (schema, packages, backend, docker-compose)
    assert len(lines_with_checkmark) >= 4, \
        f"Expected at least 4 success indicators, found {len(lines_with_checkmark)}"

    # Verify key components are mentioned in success lines
    success_text = ' '.join(lines_with_checkmark).lower()
    assert "schema" in success_text, "schema.schnitzel.yaml not in success messages"
    assert "packages" in success_text or "app" in success_text, \
        "packages/app not in success messages"
    assert "backend" in success_text or "app" in success_text, \
        "backend/app not in success messages"
    assert "docker-compose" in success_text, "docker-compose.yaml not in success messages"


def test_init_with_template_shows_progress(temp_dir: Path) -> None:
    """Test that init command with --template flag shows proper progress."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Verify creating message
    assert "Creating project:" in output, "Missing creating message"
    assert project_name in output, "Project name not in output"

    # Verify success indicators
    assert "✓" in output, "Missing success indicators"

    # Verify final success
    assert "Project created successfully" in output or "created successfully" in output, \
        "Missing final success message"


def test_init_output_format_matches_expected(temp_dir: Path) -> None:
    """Test that init output format matches the expected structure from spec."""
    project_name = "my-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Expected format:
    # Creating project: {name}
    #   ✓ Created schema.schnitzel.yaml
    #   ✓ Created packages/app/
    #   ✓ Created backend/app/
    #   ✓ Created docker-compose.yaml
    # ✓ Project created successfully!
    # Next steps:
    #   1. cd {project}
    #   2. Edit schema.schnitzel.yaml
    #   3. Run: schnitzel generate

    # Check header
    assert "Creating project:" in output, "Missing header"

    # Check individual steps with checkmarks (should be indented)
    lines = output.split('\n')
    checkmark_lines = [line for line in lines if '✓' in line]
    assert len(checkmark_lines) >= 4, "Should have at least 4 success indicators"

    # Check final success
    success_lines = [line for line in lines if 'Project created successfully' in line]
    assert len(success_lines) > 0, "Missing final success message"

    # Check next steps section
    assert "Next steps:" in output, "Missing Next steps section"
    assert "1." in output or "cd" in output, "Missing step numbering"
    assert "2." in output or "Edit" in output, "Missing edit instruction"
    assert "3." in output or "schnitzel generate" in output, "Missing generate instruction"
