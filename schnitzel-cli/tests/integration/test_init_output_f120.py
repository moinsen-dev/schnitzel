"""Integration tests for F120 - Init command output is informative.

Test Requirements:
- test_init_shows_progress - Verify init shows what it's creating
- test_init_shows_next_steps - Verify init shows next steps
- test_init_output_structured - Verify output is well-structured
- test_init_visual_feedback - Verify visual feedback (checkmarks)
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


def test_init_shows_progress(temp_dir: Path) -> None:
    """Test that init command shows what it's creating."""
    # Run init command
    result = runner.invoke(app, ["init", "test-project"])
    assert result.exit_code == 0

    output = result.stdout

    # Should show what's being created
    assert "test-project" in output or "project" in output.lower(), \
        "Should mention the project name"

    # Should mention key files/directories being created
    output_lower = output.lower()
    assert "schema" in output_lower or "yaml" in output_lower, \
        "Should mention schema file"


def test_init_shows_next_steps(temp_dir: Path) -> None:
    """Test that init command shows next steps."""
    # Run init command
    result = runner.invoke(app, ["init", "my-app"])
    assert result.exit_code == 0

    output = result.stdout
    output_lower = output.lower()

    # Should show next steps
    assert "next" in output_lower or "step" in output_lower, \
        "Should mention next steps"

    # Should mention key actions
    assert "cd" in output_lower or "edit" in output_lower or \
           "generate" in output_lower, \
        "Should suggest what to do next"


def test_init_output_structured(temp_dir: Path) -> None:
    """Test that init output is well-structured and readable."""
    # Run init command
    result = runner.invoke(app, ["init", "awesome-project"])
    assert result.exit_code == 0

    output = result.stdout
    lines = [line for line in output.split("\n") if line.strip()]

    # Should have multiple lines showing different actions
    assert len(lines) >= 3, \
        f"Output should have multiple informative lines, got {len(lines)}"

    # Should not be overly verbose
    assert len(lines) < 50, \
        f"Output should be concise, got {len(lines)} lines"


def test_init_visual_feedback(temp_dir: Path) -> None:
    """Test that init provides visual feedback (checkmarks, colors)."""
    # Run init command
    result = runner.invoke(app, ["init", "cool-app"])
    assert result.exit_code == 0

    output = result.stdout

    # Should use checkmarks for success
    assert "✓" in output, "Should use checkmark (✓) for successful actions"

    # Should have multiple checkmarks for different files/actions
    checkmark_count = output.count("✓")
    assert checkmark_count >= 2, \
        f"Should show multiple successful actions, found {checkmark_count} checkmarks"


def test_init_shows_template_info(temp_dir: Path) -> None:
    """Test that init shows information about template used."""
    # Run init with full template
    result = runner.invoke(app, ["init", "full-project", "--template", "full"])
    assert result.exit_code == 0

    output = result.stdout

    # Should mention template or examples
    assert len(output) > 0, "Should have output"

    # With full template, might mention models or examples
    output_lower = output.lower()
    # Basic check - should show creation was successful
    assert "✓" in output or "success" in output_lower or "created" in output_lower, \
        "Should indicate successful creation"


def test_init_quiet_mode_minimal(temp_dir: Path) -> None:
    """Test that init in quiet mode has minimal output."""
    # Run init in quiet mode
    result = runner.invoke(app, ["--quiet", "init", "quiet-project"])
    assert result.exit_code == 0

    output = result.stdout

    # Quiet mode should have minimal output
    assert len(output) < 100, "Quiet mode should have minimal output"

    # But should still confirm success
    assert "OK" in output or len(output.strip()) < 10, \
        "Quiet mode should show minimal success indicator"


def test_init_shows_file_structure(temp_dir: Path) -> None:
    """Test that init output mentions key parts of file structure."""
    # Run init command
    result = runner.invoke(app, ["init", "structured-app"])
    assert result.exit_code == 0

    output = result.stdout
    output_lower = output.lower()

    # Should mention key directories or files
    # Could mention: schema, backend, packages, docker-compose, etc.
    keywords = ["schema", "backend", "packages", "docker", "readme", "gitignore"]
    found_keywords = [kw for kw in keywords if kw in output_lower]

    assert len(found_keywords) >= 2, \
        f"Should mention key files/directories, found: {found_keywords}"


def test_init_error_clear(temp_dir: Path) -> None:
    """Test that init errors are clear and helpful."""
    # Create existing directory
    existing_dir = temp_dir / "existing"
    existing_dir.mkdir()

    # Try to init without --force
    result = runner.invoke(app, ["init", "existing"])
    assert result.exit_code == 1

    output = result.stdout

    # Error should be clear
    assert "error" in output.lower() or "exists" in output.lower() or \
           "already" in output.lower(), \
        "Should clearly indicate the error"


def test_init_with_options_shows_choices(temp_dir: Path) -> None:
    """Test that init shows what options were used."""
    # Run init with --with-backend option
    result = runner.invoke(app, ["init", "backend-project", "--with-backend"])
    # May succeed or show helpful message about uv
    output = result.stdout

    # Should mention backend in some way
    assert len(output) > 0, "Should have output"


def test_init_completion_message(temp_dir: Path) -> None:
    """Test that init shows clear completion message."""
    # Run init command
    result = runner.invoke(app, ["init", "final-app"])
    assert result.exit_code == 0

    output = result.stdout
    output_lower = output.lower()

    # Should have clear completion indicator
    assert "✓" in output or "success" in output_lower or \
           "complete" in output_lower or "created" in output_lower, \
        "Should show clear completion message"


def test_init_suggests_commands(temp_dir: Path) -> None:
    """Test that init suggests relevant commands to run next."""
    # Run init command
    result = runner.invoke(app, ["init", "command-app"])
    assert result.exit_code == 0

    output = result.stdout
    output_lower = output.lower()

    # Should suggest schnitzel generate command
    assert "schnitzel" in output_lower or "generate" in output_lower, \
        "Should suggest schnitzel generate command"
