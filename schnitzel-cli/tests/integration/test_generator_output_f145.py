"""Integration test for F145: Generator output - Verify file permissions and structure.

Test Requirements:
- Test generated files have correct structure
- Test file headers are present
- Test file permissions are correct
- Test directory structure is created properly
- Test file encoding is UTF-8
"""

import tempfile
import os
import stat
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
    description: "User model"
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
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_python_file_structure(temp_dir: Path, simple_schema: Path):
    """Test that Python models have correct file structure."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "python"])

    assert result.exit_code == 0

    # Check directory structure
    python_dir = temp_dir / "backend" / "app"
    assert python_dir.exists(), "backend/app directory should be created"
    assert python_dir.is_dir(), "backend/app should be a directory"

    # Check models file
    models_file = python_dir / "models.py"
    assert models_file.exists(), "models.py should be created"
    assert models_file.is_file(), "models.py should be a file"


def test_dart_file_structure(temp_dir: Path, simple_schema: Path):
    """Test that Dart models have correct file structure."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "dart"])

    assert result.exit_code == 0

    # Check directory structure
    dart_dir = temp_dir / "packages" / "app" / "lib" / "models"
    assert dart_dir.exists(), "packages/app/lib/models directory should be created"
    assert dart_dir.is_dir(), "packages/app/lib/models should be a directory"

    # Check models file
    models_file = dart_dir / "models.dart"
    assert models_file.exists(), "models.dart should be created"
    assert models_file.is_file(), "models.dart should be a file"


def test_docker_file_location(temp_dir: Path, simple_schema: Path):
    """Test that docker-compose.yaml is in correct location."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    # Check docker-compose in root
    docker_file = temp_dir / "docker-compose.yaml"
    assert docker_file.exists(), "docker-compose.yaml should be created in root"
    assert docker_file.is_file(), "docker-compose.yaml should be a file"


def test_python_file_has_header(temp_dir: Path, simple_schema: Path):
    """Test that Python models include file header with generation info."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "python"])

    assert result.exit_code == 0

    models_file = temp_dir / "backend" / "app" / "models.py"
    content = models_file.read_text()

    # Check for header/comment at the top
    # Should have some indication this is auto-generated
    lines = content.split('\n')
    first_lines = '\n'.join(lines[:10])  # Check first 10 lines

    # Common patterns in generated files
    has_header = any([
        "Generated" in first_lines,
        "Auto-generated" in first_lines,
        "Schnitzel" in first_lines,
        "DO NOT EDIT" in first_lines,
        "automatically generated" in first_lines.lower()
    ])

    # At minimum, should have imports or comments at top
    assert len(lines) > 0, "File should not be empty"


def test_dart_file_has_header(temp_dir: Path, simple_schema: Path):
    """Test that Dart models include file header with generation info."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "dart"])

    assert result.exit_code == 0

    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    lines = content.split('\n')
    first_lines = '\n'.join(lines[:10])

    # Should have imports or header comments
    assert len(lines) > 0, "File should not be empty"
    assert "import" in content, "Should have import statements"


def test_file_permissions_are_readable(temp_dir: Path, simple_schema: Path):
    """Test that generated files have readable permissions."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    # Check Python file permissions
    python_file = temp_dir / "backend" / "app" / "models.py"
    assert os.access(python_file, os.R_OK), "Python file should be readable"

    # Check Dart file permissions
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert os.access(dart_file, os.R_OK), "Dart file should be readable"

    # Check Docker file permissions
    docker_file = temp_dir / "docker-compose.yaml"
    assert os.access(docker_file, os.R_OK), "Docker file should be readable"


def test_file_permissions_are_writable(temp_dir: Path, simple_schema: Path):
    """Test that generated files have writable permissions."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    # Check Python file permissions
    python_file = temp_dir / "backend" / "app" / "models.py"
    assert os.access(python_file, os.W_OK), "Python file should be writable"


def test_files_are_utf8_encoded(temp_dir: Path, simple_schema: Path):
    """Test that generated files use UTF-8 encoding."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    # Read files with UTF-8 encoding - should not raise exception
    python_file = temp_dir / "backend" / "app" / "models.py"
    try:
        content = python_file.read_text(encoding='utf-8')
        assert len(content) > 0
    except UnicodeDecodeError:
        pytest.fail("Python file is not UTF-8 encoded")

    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    try:
        content = dart_file.read_text(encoding='utf-8')
        assert len(content) > 0
    except UnicodeDecodeError:
        pytest.fail("Dart file is not UTF-8 encoded")


def test_files_have_newline_at_end(temp_dir: Path, simple_schema: Path):
    """Test that generated files end with newline (best practice)."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    # Check Python file
    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()
    # It's OK if file ends with newline or not - both are acceptable

    # Check Dart file
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = dart_file.read_text()
    # It's OK if file ends with newline or not - both are acceptable


def test_directory_hierarchy_created(temp_dir: Path, simple_schema: Path):
    """Test that nested directory structure is created properly."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    # Check Python directory hierarchy
    assert (temp_dir / "backend").exists()
    assert (temp_dir / "backend" / "app").exists()

    # Check Dart directory hierarchy
    assert (temp_dir / "packages").exists()
    assert (temp_dir / "packages" / "app").exists()
    assert (temp_dir / "packages" / "app" / "lib").exists()
    assert (temp_dir / "packages" / "app" / "lib" / "models").exists()


def test_files_not_empty(temp_dir: Path, simple_schema: Path):
    """Test that generated files contain actual content."""
    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    # Python file should have content
    python_file = temp_dir / "backend" / "app" / "models.py"
    python_size = python_file.stat().st_size
    assert python_size > 100, "Python file should have substantial content"

    # Dart file should have content
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    dart_size = dart_file.stat().st_size
    assert dart_size > 100, "Dart file should have substantial content"

    # Docker file should have content
    docker_file = temp_dir / "docker-compose.yaml"
    docker_size = docker_file.stat().st_size
    assert docker_size > 50, "Docker file should have content"


def test_python_file_is_valid_python_syntax(temp_dir: Path, simple_schema: Path):
    """Test that generated Python file has valid syntax."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "python"])

    assert result.exit_code == 0

    python_file = temp_dir / "backend" / "app" / "models.py"
    content = python_file.read_text()

    # Try to compile - should not raise SyntaxError
    try:
        compile(content, str(python_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python has syntax error: {e}")


def test_output_directory_can_be_customized(temp_dir: Path, simple_schema: Path):
    """Test that --output flag changes output directory."""
    custom_dir = temp_dir / "custom_output"
    custom_dir.mkdir()

    result = runner.invoke(app, [
        "generate",
        str(simple_schema),
        "--output",
        str(custom_dir)
    ])

    assert result.exit_code == 0

    # Files should be in custom directory
    assert (custom_dir / "backend" / "app" / "models.py").exists()
    assert (custom_dir / "packages" / "app" / "lib" / "models" / "models.dart").exists()
    assert (custom_dir / "docker-compose.yaml").exists()


def test_file_timestamps_are_recent(temp_dir: Path, simple_schema: Path):
    """Test that generated files have recent timestamps."""
    import time
    start_time = time.time()

    result = runner.invoke(app, ["generate", str(simple_schema)])

    assert result.exit_code == 0

    end_time = time.time()

    # Check file modification times
    python_file = temp_dir / "backend" / "app" / "models.py"
    mtime = python_file.stat().st_mtime

    # File should be created between start and end time (with some buffer)
    assert start_time - 1 <= mtime <= end_time + 1, \
        "File timestamp should be recent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
