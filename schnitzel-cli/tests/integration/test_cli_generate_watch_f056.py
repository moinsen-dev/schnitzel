"""Integration tests for F056 - Generate command with --watch mode.

Test Requirements:
- test_generate_watch_option_exists - verify --watch and -w flags work
- test_generate_watch_shows_watching_message - shows "Watching for changes..."
- test_generate_watch_accepts_schema_path - monitors specified schema file
- test_generate_watch_generates_initially - generates on first run before watching

Note: These tests verify that watch mode is correctly configured and shows expected
output messages. Full end-to-end watch functionality (actual file watching) would
require more complex integration tests with file modification.
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest
import subprocess
import time
import signal

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


def test_generate_watch_option_exists(temp_dir: Path) -> None:
    """Test that generate command accepts --watch and -w flags."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Test that --help shows the watch option
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "--watch" in result.stdout or "-w" in result.stdout, \
        f"Expected --watch option in help: {result.stdout}"


def test_generate_watch_shows_watching_message(temp_dir: Path) -> None:
    """Test that generate command shows 'Watching for changes...' message in watch mode."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "A product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "watch_schema.yaml"
    schema_file.write_text(schema_content)

    # Use subprocess to start watch mode and kill it after a short time
    proc = subprocess.Popen(
        ["uv", "run", "schnitzel", "generate", str(schema_file), "--watch"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli"
    )

    # Give it time to start and show initial messages
    time.sleep(1)

    # Terminate the process
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    output = stdout + stderr

    # Check for expected messages
    assert "Watch mode enabled" in output or "Watching" in output, \
        f"Expected watch mode message in output: {output}"


def test_generate_watch_accepts_schema_path(temp_dir: Path) -> None:
    """Test that generate command monitors the specified schema file in watch mode."""
    # Create a custom schema file
    schema_content = """schnitzel: "1.0"

models:
  Order:
    description: "An order model"
    fields:
      id:
        type: uuid
        primary: true
      total:
        type: float
"""
    custom_schema = temp_dir / "custom_watch_schema.yaml"
    custom_schema.write_text(schema_content)

    # Use subprocess to verify schema path is shown
    proc = subprocess.Popen(
        ["uv", "run", "schnitzel", "generate", str(custom_schema), "--watch"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli"
    )

    time.sleep(1)
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    output = stdout + stderr

    # Verify that the custom schema path is mentioned
    # The output might wrap the path across lines, so check for both the filename and wrapped version
    output_no_newlines = output.replace("\n", "")
    assert "custom_watch_schema.yaml" in output or "custom_watch_schema" in output_no_newlines, \
        f"Expected custom schema path in output: {output}"


def test_generate_watch_generates_initially(temp_dir: Path) -> None:
    """Test that generate command generates code on first run before entering watch mode."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model for initial generation"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
      name:
        type: string
"""
    schema_file = temp_dir / "initial_gen_schema.yaml"
    schema_file.write_text(schema_content)

    # Use subprocess
    proc = subprocess.Popen(
        ["uv", "run", "schnitzel", "generate", str(schema_file), "--watch", "--target", "python"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli"
    )

    time.sleep(1)
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    output = stdout + stderr

    # Verify initial generation happened
    assert "Schema parsed successfully" in output or "Parsing schema" in output, \
        f"Expected schema parsing message in output: {output}"
    assert "Generating" in output or "Generated" in output, \
        f"Expected generation message in output: {output}"


def test_generate_watch_without_watch_flag_runs_once(temp_dir: Path) -> None:
    """Test that generate command without --watch flag runs only once and exits."""
    # Create a valid schema file
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
    schema_file = temp_dir / "no_watch_schema.yaml"
    schema_file.write_text(schema_content)

    # Run without watch mode
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Should complete successfully without watching
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Generation complete" in result.stdout
    assert "Watching" not in result.stdout, "Should not enter watch mode"
    assert "Watch mode" not in result.stdout, "Should not enter watch mode"


def test_generate_watch_shows_timestamp(temp_dir: Path) -> None:
    """Test that watch mode shows timestamp for regeneration events."""
    # Create a valid schema file
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
"""
    schema_file = temp_dir / "timestamp_schema.yaml"
    schema_file.write_text(schema_content)

    # Use subprocess
    proc = subprocess.Popen(
        ["uv", "run", "schnitzel", "generate", str(schema_file), "--watch"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli"
    )

    time.sleep(1)
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    output = stdout + stderr

    # Verify timestamp format appears (HH:MM:SS)
    import re
    timestamp_pattern = r'\[\d{2}:\d{2}:\d{2}\]'
    assert re.search(timestamp_pattern, output), \
        f"Expected timestamp pattern in output: {output}"


def test_generate_watch_combines_with_target_option(temp_dir: Path) -> None:
    """Test that watch mode works correctly with --target option."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "Product model"
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
"""
    schema_file = temp_dir / "target_watch_schema.yaml"
    schema_file.write_text(schema_content)

    # Use subprocess
    proc = subprocess.Popen(
        ["uv", "run", "schnitzel", "generate", str(schema_file), "--watch", "--target", "python"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli"
    )

    time.sleep(1)
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    output = stdout + stderr

    # Verify both watch mode and target are honored
    assert "Watch mode" in output or "Watching" in output, \
        f"Expected watch mode in output: {output}"
    assert "Python" in output or "python" in output, \
        f"Expected python target in output: {output}"
