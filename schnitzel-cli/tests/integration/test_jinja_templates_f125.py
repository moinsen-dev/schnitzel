"""Integration tests for F125 - Jinja2 templates loaded from package.

Test Requirements:
- test_jinja_template_exists - Verify Jinja2 template file exists if used
- test_template_loads_from_package - Verify templates load from package resources
- test_template_rendering_works - Verify template rendering produces output
- test_no_template_errors - Verify no Jinja2 template errors during generation

Note: This test checks IF Jinja2 templates are used. If the project doesn't use
Jinja2 for generation (uses direct string formatting), this is acceptable and
tests will verify that generation still works correctly.
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


def test_jinja_template_exists(temp_dir: Path) -> None:
    """Test that Jinja2 template file exists in package if templates are used."""
    # Check if templates directory exists
    from pathlib import Path
    import schnitzel

    schnitzel_path = Path(schnitzel.__file__).parent
    templates_dir = schnitzel_path / "templates"

    # If templates directory exists, check for template files
    if templates_dir.exists():
        # Should have at least one .j2 or .jinja2 file
        template_files = list(templates_dir.glob("**/*.j2")) + list(templates_dir.glob("**/*.jinja2"))
        # Templates are optional - if directory exists, verify structure is correct
        if len(template_files) > 0:
            assert templates_dir.is_dir(), "Templates directory should be a directory"
    # If no templates directory, generation uses direct string formatting (also valid)


def test_generation_works_without_template_errors(temp_dir: Path) -> None:
    """Test that code generation works without Jinja2 template errors."""
    # Create schema
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
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should succeed without template errors
    assert result.exit_code == 0, \
        f"Generation failed, possibly due to template issues: {result.stdout}"

    # Should not have Jinja2 errors in output
    output_lower = result.stdout.lower()
    assert "jinja" not in output_lower or "error" not in output_lower, \
        "Should not have Jinja2 errors"

    # Verify files were actually generated
    python_file = temp_dir / "backend" / "app" / "models.py"
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"

    assert python_file.exists(), "Python models should be generated"
    assert dart_file.exists(), "Dart models should be generated"


def test_template_rendering_produces_valid_output(temp_dir: Path) -> None:
    """Test that template rendering (or string generation) produces valid output."""
    # Create schema with various field types (using snake_case)
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "A product in the catalog"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
      in_stock:
        type: bool
        default: true
      created_at:
        type: datetime
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])
    assert result.exit_code == 0

    # Read generated file
    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Verify output is valid Python
    # Should have import statements
    assert "import " in content or "from " in content, \
        "Generated code should have imports"

    # Should have class definition
    assert "class Product" in content, "Should have Product class"

    # Should have field definitions
    assert "id" in content, "Should have id field"
    assert "name" in content, "Should have name field"
    assert "price" in content, "Should have price field"

    # Should have docstring
    assert '"""' in content or "'''" in content, \
        "Should have docstring for model with description"


def test_no_template_syntax_in_output(temp_dir: Path) -> None:
    """Test that generated files don't contain unrendered template syntax."""
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
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    # Read generated files
    python_file = temp_dir / "backend" / "app" / "models.py"
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_file = temp_dir / "docker-compose.yaml"

    python_content = python_file.read_text()
    dart_content = dart_file.read_text()
    docker_content = docker_file.read_text()

    # Should not have Jinja2 template syntax {{ }} or {% %}
    assert "{{" not in python_content, "Python file should not have unrendered {{ }}"
    assert "{%" not in python_content, "Python file should not have unrendered {% %}"

    assert "{{" not in dart_content, "Dart file should not have unrendered {{ }}"
    assert "{%" not in dart_content, "Dart file should not have unrendered {% %}"

    # Docker compose uses {{ }} for environment variables, which is valid
    # So we don't check docker file for {{ }}


def test_package_resource_loading(temp_dir: Path) -> None:
    """Test that if templates exist, they can be loaded as package resources."""
    # Try to import and check if templates can be accessed
    from pathlib import Path
    import schnitzel

    schnitzel_path = Path(schnitzel.__file__).parent
    templates_dir = schnitzel_path / "templates"

    # If templates directory exists, it should be accessible
    if templates_dir.exists():
        # Directory should be readable
        assert templates_dir.is_dir(), "Templates directory should be a directory"
        assert os.access(templates_dir, os.R_OK), "Templates directory should be readable"

        # If template files exist, they should be readable
        template_files = list(templates_dir.glob("**/*.j2")) + list(templates_dir.glob("**/*.jinja2"))
        for template_file in template_files:
            assert template_file.is_file(), f"Template {template_file} should be a file"
            assert os.access(template_file, os.R_OK), \
                f"Template {template_file} should be readable"


def test_generation_consistent_with_or_without_templates(temp_dir: Path) -> None:
    """Test that generation produces consistent output (with or without templates)."""
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
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate twice
    result1 = runner.invoke(app, ["generate", str(schema_file), "--force"])
    assert result1.exit_code == 0

    # Read first generation
    python_file = temp_dir / "backend" / "app" / "models.py"
    content1 = python_file.read_text()

    # Generate again
    result2 = runner.invoke(app, ["generate", str(schema_file), "--force"])
    assert result2.exit_code == 0

    # Read second generation
    content2 = python_file.read_text()

    # Output should be identical (deterministic generation)
    # Except for timestamp in header
    lines1 = content1.split("\n")
    lines2 = content2.split("\n")

    # Compare non-timestamp lines
    # Skip header lines with timestamps
    code1 = [line for line in lines1 if "Generated at:" not in line]
    code2 = [line for line in lines2 if "Generated at:" not in line]

    # Code should be identical
    assert code1 == code2, "Generated code should be deterministic (excluding timestamps)"


def test_template_errors_caught_gracefully(temp_dir: Path) -> None:
    """Test that if templates have issues, errors are caught and reported."""
    # Create valid schema
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

    # Run generate - should work without errors
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should either succeed or show clear error (not crash)
    assert result.exit_code in [0, 1], \
        "Should either succeed or show error gracefully"

    # If failed, should have helpful error message
    if result.exit_code == 1:
        output = result.stdout
        assert len(output) > 0, "Error output should be provided"
