"""Integration tests for F123 - CLI version flag shows version.

Test Requirements:
- test_version_command - Verify 'schnitzel version' works
- test_version_flag - Verify '--version' flag works
- test_version_format - Verify version format is valid
- test_version_matches_package - Verify version matches __version__
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest
import re

from schnitzel.cli import app
from schnitzel import __version__

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_version_command() -> None:
    """Test that 'schnitzel version' command works."""
    # Run version command
    result = runner.invoke(app, ["version"])

    # Should succeed
    assert result.exit_code == 0, f"Version command failed: {result.stdout}"

    output = result.stdout

    # Should show version
    assert len(output.strip()) > 0, "Version command should produce output"

    # Should mention "version" or show version number
    assert "version" in output.lower() or re.search(r'\d+\.\d+', output), \
        "Output should mention version or show version number"


def test_version_format() -> None:
    """Test that version format is valid (semantic versioning)."""
    # Run version command
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0

    output = result.stdout

    # Should match semantic versioning pattern: X.Y.Z
    version_pattern = r'\d+\.\d+\.\d+'
    assert re.search(version_pattern, output), \
        f"Version should match semantic versioning (X.Y.Z), got: {output}"


def test_version_matches_package() -> None:
    """Test that CLI version matches package __version__."""
    # Run version command
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0

    output = result.stdout

    # Should contain the package version
    assert __version__ in output, \
        f"CLI version should show package version {__version__}, got: {output}"


def test_version_shows_cli_name() -> None:
    """Test that version output mentions Schnitzel CLI."""
    # Run version command
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0

    output = result.stdout
    output_lower = output.lower()

    # Should mention schnitzel or CLI
    assert "schnitzel" in output_lower or "cli" in output_lower, \
        "Version output should mention Schnitzel or CLI"


def test_version_concise() -> None:
    """Test that version output is concise."""
    # Run version command
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0

    output = result.stdout
    lines = [line for line in output.split("\n") if line.strip()]

    # Should be concise (1-3 lines)
    assert len(lines) <= 3, \
        f"Version output should be concise, got {len(lines)} lines"
