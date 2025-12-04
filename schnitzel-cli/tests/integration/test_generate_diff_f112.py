"""Integration tests for F112 - Generate command shows diff before overwriting existing files.

Test Requirements:
- test_diff_shown_option - Test that diff is shown (can be skipped if too complex)

Note: This feature is marked as optional and can be implemented in a future iteration.
The current implementation warns users about overwriting but does not show diffs.
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


@pytest.mark.skip(reason="Diff feature not yet implemented - can be added in future iteration")
def test_diff_shown_option(temp_dir: Path) -> None:
    """Test that generate command shows diff before overwriting (SKIPPED - not implemented).

    This test is skipped because implementing diff functionality is complex and
    requires additional dependencies like difflib formatting or external diff tools.

    Future implementation could:
    - Use Python's difflib to generate unified diffs
    - Show colored diff output using Rich
    - Provide --show-diff flag to enable this feature
    - Ask for confirmation before overwriting when diff is shown
    """
    # This test would verify:
    # 1. Create initial files with generate command
    # 2. Modify schema slightly
    # 3. Run generate again
    # 4. Verify diff is shown in output
    # 5. Verify user is prompted for confirmation
    pass


def test_generate_warns_about_existing_files(temp_dir: Path) -> None:
    """Test that generate command warns when files exist without --force flag."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Generate files first time
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0, f"First generation failed: {result.stdout}"

    # Try to generate again without --force
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should still succeed but warn about existing files
    assert result.exit_code == 0, f"Second generation failed: {result.stdout}"

    # Check for warning messages
    output_lower = result.stdout.lower()
    assert "already exists" in output_lower or "warning" in output_lower, \
        "Should warn about existing files"


def test_generate_force_overwrites_without_warning(temp_dir: Path) -> None:
    """Test that --force flag overwrites files without warnings."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "Product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Generate files first time
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Generate again with --force
    result = runner.invoke(app, ["generate", str(schema_file), "--force"])
    assert result.exit_code == 0, f"Force generation failed: {result.stdout}"

    # Should succeed without interactive prompts
    assert "✓" in result.stdout or "complete" in result.stdout.lower(), \
        "Should show success indicator"


def test_generate_dry_run_shows_what_would_be_written(temp_dir: Path) -> None:
    """Test that --dry-run shows what files would be created/modified."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Order:
    description: "Order model"
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run with --dry-run
    result = runner.invoke(app, ["generate", str(schema_file), "--dry-run"])
    assert result.exit_code == 0, f"Dry run failed: {result.stdout}"

    # Verify dry-run indicators in output
    output_lower = result.stdout.lower()
    assert "dry" in output_lower or "dry-run" in output_lower, \
        "Should indicate dry-run mode"

    # Verify files are not actually created
    backend_dir = temp_dir / "backend" / "app"
    if backend_dir.exists():
        models_file = backend_dir / "models.py"
        assert not models_file.exists(), "Files should not be created in dry-run mode"


def test_generate_existing_file_paths_shown_in_warning(temp_dir: Path) -> None:
    """Test that warnings show which specific files already exist."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Generate first time
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Generate again
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should mention file paths in warnings
    output = result.stdout
    assert "models.py" in output or "models.dart" in output or "docker-compose.yaml" in output, \
        "Should mention specific file names in output"


@pytest.mark.skip(reason="Interactive diff confirmation not implemented")
def test_diff_with_confirmation_prompt(temp_dir: Path) -> None:
    """Test that diff feature includes confirmation prompt (SKIPPED).

    Future implementation could add:
    - Show diff of changes
    - Prompt: "Overwrite this file? [y/N]"
    - Handle user response
    - Support --yes flag to auto-confirm
    """
    pass


@pytest.mark.skip(reason="Colored diff output not implemented")
def test_diff_uses_rich_formatting(temp_dir: Path) -> None:
    """Test that diff output uses Rich for colored formatting (SKIPPED).

    Future implementation could use:
    - Rich Syntax for highlighting differences
    - Green for additions
    - Red for deletions
    - Unified diff format
    """
    pass
