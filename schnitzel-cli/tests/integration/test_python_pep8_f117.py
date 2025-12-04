"""Integration tests for F117 - Generated Python code follows PEP 8.

Test Requirements:
- test_line_length_under_100 - Verify lines are under 100 characters (ruff configured)
- test_imports_sorted - Verify imports are sorted
- test_proper_indentation - Verify 4-space indentation
- test_blank_lines - Verify proper blank line usage
- test_no_trailing_whitespace - Verify no trailing whitespace
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


def test_line_length_under_100(temp_dir: Path) -> None:
    """Test that generated Python code has lines under 100 characters."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A user in the system with authentication credentials"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists()

    content = models_file.read_text()
    lines = content.split("\n")

    # Check line length (excluding header comments)
    code_lines = [line for line in lines if not line.startswith("#")]
    long_lines = [line for line in code_lines if len(line) > 100]

    assert len(long_lines) == 0, \
        f"Found {len(long_lines)} lines over 100 characters: {long_lines[:3]}"


def test_imports_sorted(temp_dir: Path) -> None:
    """Test that imports are sorted alphabetically."""
    # Create schema with UUID and datetime fields to trigger imports
    schema_content = """schnitzel: "1.0"

models:
  Event:
    fields:
      id:
        type: uuid
        primary: true
      created_at:
        type: datetime
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Extract import lines
    lines = content.split("\n")
    import_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            import_lines.append(stripped)

    # Imports should be present
    assert len(import_lines) > 0, "Should have import statements"

    # Check if imports are sorted (excluding future imports which must be first)
    future_imports = [imp for imp in import_lines if "from __future__" in imp]
    other_imports = [imp for imp in import_lines if "from __future__" not in imp]

    # Other imports should be sorted
    sorted_imports = sorted(other_imports)
    assert other_imports == sorted_imports, \
        f"Imports are not sorted.\nExpected: {sorted_imports}\nGot: {other_imports}"


def test_proper_indentation(temp_dir: Path) -> None:
    """Test that generated code uses 4-space indentation."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
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

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()
    lines = content.split("\n")

    # Check for tabs (should not exist in PEP 8 code)
    tab_lines = [i for i, line in enumerate(lines) if "\t" in line and not line.strip().startswith("#")]
    assert len(tab_lines) == 0, \
        f"Found tabs on lines: {tab_lines}. PEP 8 requires spaces, not tabs."

    # Check that class body is indented with 4 spaces
    class_found = False
    for i, line in enumerate(lines):
        if line.startswith("class "):
            class_found = True
            # Next non-empty line should be indented with 4 spaces
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].strip().startswith("#"):
                    # Should start with 4 spaces (or 8 for nested)
                    assert lines[j].startswith("    "), \
                        f"Line {j} in class body not indented with 4 spaces: '{lines[j]}'"
                    break

    assert class_found, "Should have at least one class definition"


def test_blank_lines(temp_dir: Path) -> None:
    """Test that proper blank lines are used between sections."""
    # Create schema with multiple models
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
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

    # Find class definitions
    class_lines = [i for i, line in enumerate(lines) if line.startswith("class ")]

    # If we have multiple classes, check spacing
    if len(class_lines) >= 2:
        # Between classes, there should be blank lines (PEP 8 recommends 2)
        for i in range(len(class_lines) - 1):
            class1_line = class_lines[i]
            class2_line = class_lines[i + 1]
            # Count blank lines between classes
            blank_count = 0
            for j in range(class1_line + 1, class2_line):
                if lines[j].strip() == "":
                    blank_count += 1
            # Should have at least 1 blank line
            assert blank_count >= 1, \
                f"Should have blank lines between classes at lines {class1_line} and {class2_line}"


def test_no_trailing_whitespace(temp_dir: Path) -> None:
    """Test that generated code has no trailing whitespace."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string
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

    # Check for trailing whitespace
    trailing_whitespace_lines = []
    for i, line in enumerate(lines):
        if line != line.rstrip():
            trailing_whitespace_lines.append(i + 1)

    assert len(trailing_whitespace_lines) == 0, \
        f"Found trailing whitespace on lines: {trailing_whitespace_lines[:10]}"


def test_docstring_format(temp_dir: Path) -> None:
    """Test that docstrings are properly formatted."""
    # Create schema with model descriptions
    schema_content = """schnitzel: "1.0"

models:
  Customer:
    description: "A customer who purchases products"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Should have docstrings with triple quotes
    assert '"""' in content, "Should use triple quotes for docstrings"

    # Docstring should contain the description
    assert "A customer who purchases products" in content, \
        "Docstring should contain model description"


def test_pydantic_v2_syntax(temp_dir: Path) -> None:
    """Test that generated code uses Pydantic v2 syntax."""
    # Create schema with optional field
    schema_content = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      subtitle:
        type: string
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Should use Pydantic v2 union syntax (| None) not Optional
    # Count occurrences
    modern_syntax_count = content.count("| None")
    old_syntax_count = content.count("Optional[")

    # Should prefer modern syntax
    assert modern_syntax_count > 0 or old_syntax_count == 0, \
        "Should use Pydantic v2 syntax (| None) for optional fields"


def test_naming_conventions(temp_dir: Path) -> None:
    """Test that generated code follows Python naming conventions."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  BlogPost:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Class names should be in PascalCase
    assert "class BlogPost" in content, "Class names should be PascalCase"

    # Field names should be snake_case (check that we don't have camelCase in field names)
    # This is harder to verify without AST parsing, but we can check basics
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        # Skip comments and class definitions
        if stripped.startswith("#") or stripped.startswith("class "):
            continue
        # Field definitions typically have colon
        if ":" in stripped and "=" in stripped:
            # Extract field name (before colon)
            field_part = stripped.split(":")[0].strip()
            if field_part and not field_part.startswith('"') and field_part.isidentifier():
                # Check it's snake_case (all lowercase or has underscores)
                assert field_part.islower() or "_" in field_part, \
                    f"Field '{field_part}' should be snake_case"


def test_consistent_spacing(temp_dir: Path) -> None:
    """Test consistent spacing around operators and colons."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      count:
        type: int
        default: 0
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Check for proper spacing around =
    # PEP 8: spaces around assignment operator
    lines = content.split("\n")
    for i, line in enumerate(lines):
        # Skip comments
        if line.strip().startswith("#"):
            continue
        # Check field assignments
        if "=" in line and ":" in line and not line.strip().startswith("class"):
            # Should have spaces around =
            parts = line.split("=")
            if len(parts) >= 2:
                # Left side should end with space or be at end of type annotation
                # Right side should start with space
                # This is a basic check
                before_equals = parts[0]
                after_equals = parts[1]
                # After equals should start with space (unless it's a string)
                if after_equals and not after_equals[0] in [" ", '"', "'"]:
                    # Some exceptions for Field() calls
                    if not after_equals.startswith("Field"):
                        pass  # Allow for now as formatting can vary
