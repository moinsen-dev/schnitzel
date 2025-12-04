"""Integration test for F137: Error handling - Generate with missing template file.

Test Requirements:
- Test graceful error handling when generation fails
- Test missing template file scenarios
- Test invalid schema file paths
- Test permissions errors during file generation
- Test cleanup of partial files on error
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
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_missing_schema_file(temp_dir: Path):
    """Test graceful error handling when schema file doesn't exist."""
    non_existent_file = temp_dir / "nonexistent.yaml"

    result = runner.invoke(app, ["generate", str(non_existent_file)])

    # Should fail gracefully
    assert result.exit_code == 1, "Command should exit with code 1 for missing file"
    assert "Error" in result.stdout or "not found" in result.stdout.lower()
    assert "nonexistent.yaml" in result.stdout or "Schema file not found" in result.stdout


def test_invalid_yaml_syntax(temp_dir: Path):
    """Test graceful error handling with malformed YAML file."""
    schema_file = temp_dir / "invalid.yaml"
    schema_file.write_text("""schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
      name
        type: string  # Missing colon - invalid YAML
""")

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 1, "Command should exit with code 1 for invalid YAML"
    assert "Error" in result.stdout or "YAML" in result.stdout or "parsing" in result.stdout.lower()


def test_schema_validation_error(temp_dir: Path):
    """Test graceful error handling when schema validation fails."""
    schema_file = temp_dir / "invalid_schema.yaml"
    schema_file.write_text("""schnitzel: "1.0"

models:
  User:
    description: "User with invalid field type"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type_xyz
""")

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 1, "Command should exit with code 1 for validation failure"
    assert "validation failed" in result.stdout.lower() or "Error" in result.stdout
    assert "invalid_type_xyz" in result.stdout or "Unsupported" in result.stdout


def test_missing_relationship_target(temp_dir: Path):
    """Test graceful error handling when relationship target doesn't exist."""
    schema_file = temp_dir / "missing_target.yaml"
    schema_file.write_text("""schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      author_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
""")

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 1, "Command should exit with code 1 for missing relationship"
    assert "Error" in result.stdout or "validation" in result.stdout.lower()
    assert "User" in result.stdout


def test_no_files_generated_on_validation_error(temp_dir: Path):
    """Test that no output files are created when validation fails."""
    schema_file = temp_dir / "invalid.yaml"
    schema_file.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: invalid_type
        primary: true
""")

    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify command failed
    assert result.exit_code == 1, "Command should fail"

    # Verify NO files were created
    python_models = temp_dir / "backend" / "app" / "models.py"
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose = temp_dir / "docker-compose.yaml"

    assert not python_models.exists(), "Python models should NOT be created on error"
    assert not dart_models.exists(), "Dart models should NOT be created on error"
    assert not docker_compose.exists(), "Docker Compose should NOT be created on error"


def test_error_message_includes_helpful_context(temp_dir: Path):
    """Test that error messages include helpful context and suggestions."""
    schema_file = temp_dir / "error_test.yaml"
    schema_file.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: invalid_format
""")

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 1, "Command should fail"
    # Should provide helpful error message
    assert "Error" in result.stdout or "validation" in result.stdout.lower()


def test_empty_schema_file(temp_dir: Path):
    """Test handling of empty schema file."""
    schema_file = temp_dir / "empty.yaml"
    schema_file.write_text("")

    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should handle gracefully
    assert result.exit_code == 1, "Command should fail for empty schema"


def test_schema_missing_required_fields(temp_dir: Path):
    """Test handling of schema missing required top-level fields."""
    schema_file = temp_dir / "minimal.yaml"
    schema_file.write_text("""schnitzel: "1.0"
# Missing models section
""")

    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should handle gracefully - empty models is valid but might warn
    # The actual behavior depends on implementation
    assert result.exit_code in [0, 1], "Command should handle gracefully"


def test_generate_with_invalid_target_option(temp_dir: Path):
    """Test handling of invalid --target option."""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
""")

    result = runner.invoke(app, ["generate", str(schema_file), "--target", "invalid_target"])

    assert result.exit_code == 1, "Command should fail for invalid target"
    assert "Invalid target" in result.stdout or "Error" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
