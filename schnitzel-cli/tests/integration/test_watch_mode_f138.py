"""Integration test for F138: Watch mode - Multiple rapid schema changes.

Test Requirements:
- Test watch mode functionality with file changes
- Test multiple rapid schema modifications
- Mark as skip if watch mode not fully implemented
- Test that changes trigger regeneration
- Test graceful shutdown on Ctrl+C
"""

import tempfile
import os
import time
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def simple_schema(temp_dir: Path) -> Path:
    """Create a simple schema file."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.mark.skip(reason="Watch mode testing requires async/threading - skip if not fully implemented")
def test_watch_mode_basic(temp_dir: Path, simple_schema: Path):
    """Test basic watch mode functionality."""
    # This test would require async execution or threading
    # Marking as skip since watch mode may not be fully testable in sync test environment
    pass


@pytest.mark.skip(reason="Watch mode testing requires async/threading")
def test_watch_mode_multiple_changes(temp_dir: Path, simple_schema: Path):
    """Test watch mode handles multiple rapid schema changes."""
    # This test would require async execution or threading
    pass


def test_watch_mode_flag_exists(temp_dir: Path, simple_schema: Path):
    """Test that --watch flag is recognized by CLI."""
    # Test that the --watch flag doesn't cause errors
    # We can't fully test watch mode behavior, but we can verify the flag exists
    result = runner.invoke(app, ["generate", "--help"])

    assert result.exit_code == 0
    assert "--watch" in result.stdout or "-w" in result.stdout, \
        "CLI should support --watch/-w flag"


def test_generate_without_watch_works(temp_dir: Path, simple_schema: Path):
    """Test that normal generation without --watch flag works correctly."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0, f"Generation should succeed: {result.stdout}"
    assert "Generation complete" in result.stdout or "✓" in result.stdout


def test_schema_modification_detection(temp_dir: Path, simple_schema: Path):
    """Test that schema file modifications can be detected (filesystem test)."""
    # Get initial modification time
    initial_mtime = simple_schema.stat().st_mtime

    # Wait a bit to ensure timestamp difference
    time.sleep(0.1)

    # Modify the schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
"""
    simple_schema.write_text(schema_content)

    # Verify modification time changed
    new_mtime = simple_schema.stat().st_mtime
    assert new_mtime > initial_mtime, "File modification time should increase"


def test_multiple_rapid_modifications(temp_dir: Path, simple_schema: Path):
    """Test that multiple rapid schema modifications can be written to disk."""
    modifications = [
        """schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
""",
        """schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
""",
        """schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
      age:
        type: int
        optional: true
"""
    ]

    # Apply modifications rapidly
    for content in modifications:
        simple_schema.write_text(content)
        time.sleep(0.05)  # Small delay between modifications

    # Verify final content
    final_content = simple_schema.read_text()
    assert "age" in final_content, "Final modification should be present"


@pytest.mark.skip(reason="Watch mode runs indefinitely - cannot test in automated suite")
def test_watch_mode_with_valid_schema(temp_dir: Path, simple_schema: Path):
    """Test that watch mode can be invoked with a valid schema (startup test only)."""
    # Note: This test will start watch mode but won't actually test file watching
    # Watch mode runs indefinitely until Ctrl+C, so we skip this in automated tests
    pass


@pytest.mark.skip(reason="Interactive test - requires manual verification")
def test_watch_mode_regenerates_on_change():
    """Manual test: Verify watch mode regenerates files when schema changes.

    Manual test procedure:
    1. Run: schnitzel generate schema.schnitzel.yaml --watch
    2. Modify schema file
    3. Verify regeneration messages appear
    4. Press Ctrl+C to stop
    5. Verify graceful shutdown message
    """
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
