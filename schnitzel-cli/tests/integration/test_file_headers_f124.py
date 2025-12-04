"""Integration tests for F124 - Generated files have consistent header comments.

Test Requirements:
- test_python_file_has_header - Verify Python files have header
- test_dart_file_has_header - Verify Dart files have header
- test_docker_file_has_header - Verify docker-compose has header
- test_header_includes_timestamp - Verify headers include generation timestamp
- test_header_includes_source - Verify headers mention source schema file
- test_header_format_consistent - Verify headers follow same format across files
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest
from datetime import datetime

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


def test_python_file_has_header(temp_dir: Path) -> None:
    """Test that generated Python files have header comments."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()
    lines = content.split("\n")

    # First lines should be comments
    assert lines[0].startswith("#"), "First line should be a comment"

    # Should mention generation
    header = "\n".join(lines[:10])
    assert "Generated" in header or "generated" in header.lower(), \
        "Header should mention it's generated"

    # Should warn about not editing
    assert "DO NOT EDIT" in header or "auto-generated" in header.lower(), \
        "Header should warn about manual editing"


def test_dart_file_has_header(temp_dir: Path) -> None:
    """Test that generated Dart files have header comments."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()
    lines = content.split("\n")

    # First lines should be comments
    assert lines[0].startswith("//"), "First line should be a comment"

    # Should mention generation
    header = "\n".join(lines[:10])
    assert "Generated" in header or "generated" in header.lower(), \
        "Header should mention it's generated"


def test_docker_file_has_header(temp_dir: Path) -> None:
    """Test that docker-compose.yaml has header comments."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    lines = content.split("\n")

    # First lines should be comments
    assert lines[0].startswith("#"), "First line should be a comment"

    # Should mention generation
    header = "\n".join(lines[:10])
    assert "Generated" in header or "generated" in header.lower(), \
        "Header should mention it's generated"


def test_header_includes_timestamp(temp_dir: Path) -> None:
    """Test that headers include generation timestamp."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Check Python file
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_content = python_file.read_text()
    python_header = "\n".join(python_content.split("\n")[:10])

    # Should have timestamp info
    assert "Generated at" in python_header or "timestamp" in python_header.lower() or \
           "date" in python_header.lower(), \
        "Header should include timestamp information"


def test_header_includes_source(temp_dir: Path) -> None:
    """Test that headers mention source schema file."""
    # Create schema with specific name
    schema_content = """schnitzel: "1.0"

models:
  Customer:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "my_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Check Python file
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_content = python_file.read_text()
    python_header = "\n".join(python_content.split("\n")[:10])

    # Should mention source file
    assert "Source" in python_header or "source" in python_header.lower() or \
           "schema" in python_header.lower() or "my_schema" in python_content, \
        "Header should reference source schema file"


def test_header_format_consistent(temp_dir: Path) -> None:
    """Test that headers follow same format across different files."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command for all targets
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Read all generated files
    python_file = temp_dir / "backend" / "app" / "models.py"
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_file = temp_dir / "docker-compose.yaml"

    python_lines = python_file.read_text().split("\n")
    dart_lines = dart_file.read_text().split("\n")
    docker_lines = docker_file.read_text().split("\n")

    # All should have "Generated by Schnitzel" or similar
    python_header = "\n".join(python_lines[:10])
    dart_header = "\n".join(dart_lines[:10])
    docker_header = "\n".join(docker_lines[:10])

    # All should mention Schnitzel
    assert "Schnitzel" in python_header, "Python header should mention Schnitzel"
    assert "Schnitzel" in dart_header, "Dart header should mention Schnitzel"
    assert "Schnitzel" in docker_header, "Docker header should mention Schnitzel"

    # All should warn about editing
    assert "DO NOT EDIT" in python_header or "auto-generated" in python_header, \
        "Python header should warn about editing"
    assert "DO NOT EDIT" in dart_header or "auto-generated" in dart_header, \
        "Dart header should warn about editing"
    assert "DO NOT EDIT" in docker_header or "auto-generated" in docker_header, \
        "Docker header should warn about editing"


def test_header_separated_from_code(temp_dir: Path) -> None:
    """Test that header is visually separated from code."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Event:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()
    lines = content.split("\n")

    # Find where header ends (first non-comment, non-empty line)
    header_end = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#"):
            header_end = i
            break

    # Should have blank line before code starts (or double newline)
    assert header_end > 0, "Should have header before code"
    # The line before code should be empty or the header should end with blank
    if header_end > 1:
        assert lines[header_end - 1].strip() == "", \
            "Should have blank line separating header from code"


def test_header_concise(temp_dir: Path) -> None:
    """Test that headers are concise (not overly verbose)."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Check Python file
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_lines = python_file.read_text().split("\n")

    # Count comment lines at start
    header_line_count = 0
    for line in python_lines:
        if line.strip().startswith("#"):
            header_line_count += 1
        elif line.strip():
            break

    # Header should be concise (typically 3-7 lines)
    assert header_line_count <= 10, \
        f"Header should be concise, found {header_line_count} comment lines"
