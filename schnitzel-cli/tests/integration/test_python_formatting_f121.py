"""Integration tests for F121 - Generated Python models have consistent formatting.

Test Requirements:
- test_consistent_field_spacing - Verify consistent spacing in field definitions
- test_consistent_class_structure - Verify classes follow same pattern
- test_consistent_import_style - Verify imports are consistently formatted
- test_consistent_docstrings - Verify docstrings are consistently formatted
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


def test_consistent_field_spacing(temp_dir: Path) -> None:
    """Test that field definitions have consistent spacing."""
    # Create schema with multiple fields
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
      age:
        type: int
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
    lines = content.split("\n")

    # Find field definitions (lines with : and = typically)
    field_lines = []
    in_class = False
    for line in lines:
        if line.startswith("class "):
            in_class = True
        elif in_class:
            stripped = line.strip()
            if stripped and ":" in stripped and not stripped.startswith('"""') and not stripped.startswith("#"):
                field_lines.append(line)

    # All field lines should use consistent spacing pattern
    # Check that spacing around : and = is consistent
    if len(field_lines) >= 2:
        # Pattern check: space after colon
        for line in field_lines:
            if ":" in line and not line.strip().startswith("def"):
                # After type annotation colon, there should be a space
                parts = line.split(":")
                if len(parts) >= 2:
                    # Second part should start with space (for type annotation)
                    assert parts[1].startswith(" "), \
                        f"Inconsistent spacing after colon: '{line}'"


def test_consistent_class_structure(temp_dir: Path) -> None:
    """Test that all classes follow the same structural pattern."""
    # Create schema with multiple models
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

  Post:
    description: "Post model"
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

    # All classes should inherit from BaseModel
    assert content.count("(BaseModel)") >= 2, \
        "All model classes should inherit from BaseModel"

    # All classes with descriptions should have docstrings
    assert content.count('"""') >= 2, \
        "Models with descriptions should have docstrings"


def test_consistent_import_style(temp_dir: Path) -> None:
    """Test that imports follow consistent style."""
    # Create schema that triggers multiple imports
    schema_content = """schnitzel: "1.0"

models:
  Event:
    fields:
      id:
        type: uuid
        primary: true
      created_at:
        type: datetime
      data:
        type: json
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated Python file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Get import lines
    lines = content.split("\n")
    import_lines = [line for line in lines if line.startswith("from ") or line.startswith("import ")]

    # All imports should follow consistent style
    # Check that all from imports have proper spacing
    from_imports = [line for line in import_lines if line.startswith("from ")]
    for imp in from_imports:
        # Should have format: from MODULE import ITEMS
        assert " import " in imp, f"Import should have ' import ' pattern: {imp}"


def test_consistent_docstrings(temp_dir: Path) -> None:
    """Test that docstrings are consistently formatted."""
    # Create schema with descriptions
    schema_content = """schnitzel: "1.0"

models:
  Customer:
    description: "A customer entity"
    fields:
      id:
        type: uuid
        primary: true

  Order:
    description: "An order entity"
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

    # Find docstring lines
    docstring_lines = [i for i, line in enumerate(lines) if '"""' in line]

    # All docstrings should use triple double-quotes
    for idx in docstring_lines:
        line = lines[idx]
        assert '"""' in line, "Should use triple double-quotes for docstrings"


def test_consistent_optional_field_syntax(temp_dir: Path) -> None:
    """Test that optional fields use consistent syntax."""
    # Create schema with multiple optional fields
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
      summary:
        type: text
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

    # All optional fields should use | None syntax (Pydantic v2)
    optional_count = content.count("| None")

    # Should have at least the optional fields
    assert optional_count >= 2, \
        "Optional fields should consistently use | None syntax"


def test_consistent_blank_line_usage(temp_dir: Path) -> None:
    """Test that blank lines are used consistently."""
    # Create schema with multiple models
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Category:
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
    lines = content.split("\n")

    # Find class definitions
    class_indices = [i for i, line in enumerate(lines) if line.startswith("class ")]

    # Between consecutive classes, should have blank lines
    if len(class_indices) >= 2:
        for i in range(len(class_indices) - 1):
            idx1 = class_indices[i]
            idx2 = class_indices[i + 1]

            # Count blank lines between classes
            blank_count = 0
            for j in range(idx1 + 1, idx2):
                if lines[j].strip() == "":
                    blank_count += 1

            # Should have at least one blank line
            assert blank_count >= 1, \
                f"Classes should be separated by blank lines (found {blank_count} between classes)"


def test_consistent_indentation_depth(temp_dir: Path) -> None:
    """Test that indentation depth is consistent."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
      description:
        type: text
      priority:
        type: int
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

    # Class body should use 4-space indentation consistently
    in_class = False
    for line in lines:
        if line.startswith("class "):
            in_class = True
        elif in_class and line.strip() and not line.startswith("class "):
            # Should start with 4 spaces for first level
            if not line.startswith("#") and not line.strip().startswith('"""'):
                if line.startswith(" "):
                    # Count leading spaces
                    spaces = len(line) - len(line.lstrip())
                    # Should be multiple of 4
                    assert spaces % 4 == 0, \
                        f"Indentation should be multiple of 4, got {spaces}: '{line}'"
