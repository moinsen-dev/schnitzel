"""Integration tests for F113 - Schema parser validates schema version compatibility.

Test Requirements:
- test_valid_version - Verify valid versions are accepted
- test_invalid_version - Verify invalid versions are rejected
- test_missing_version - Verify missing version is rejected
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app
from schnitzel.schema import SchemaParser
from schnitzel.schema.exceptions import VersionError

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_valid_version(temp_dir: Path) -> None:
    """Test that parser accepts valid schema versions."""
    parser = SchemaParser()

    # Test version "1.0"
    schema_content_1_0 = """schnitzel: "1.0"

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
    schema_file = temp_dir / "schema_1_0.yaml"
    schema_file.write_text(schema_content_1_0)

    # Should parse without error
    schema = parser.parse(schema_file)
    assert schema is not None
    assert schema.schnitzel == "1.0"
    assert "User" in schema.models

    # Test version "1.0.0"
    schema_content_1_0_0 = """schnitzel: "1.0.0"

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
    schema_file_2 = temp_dir / "schema_1_0_0.yaml"
    schema_file_2.write_text(schema_content_1_0_0)

    schema = parser.parse(schema_file_2)
    assert schema is not None
    assert schema.schnitzel == "1.0.0"
    assert "Product" in schema.models


def test_invalid_version(temp_dir: Path) -> None:
    """Test that parser rejects invalid/unsupported schema versions."""
    parser = SchemaParser()

    # Test unsupported version "2.0"
    schema_content = """schnitzel: "2.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema_invalid.yaml"
    schema_file.write_text(schema_content)

    # Should raise VersionError
    with pytest.raises(VersionError) as exc_info:
        parser.parse(schema_file)

    error = exc_info.value
    assert "2.0" in str(error)
    assert "Incompatible" in str(error) or "incompatible" in str(error).lower()
    assert error.schema_version == "2.0"


def test_missing_version(temp_dir: Path) -> None:
    """Test that parser rejects schemas without version field."""
    parser = SchemaParser()

    # Schema without version
    schema_content = """models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema_no_version.yaml"
    schema_file.write_text(schema_content)

    # Should raise VersionError
    with pytest.raises(VersionError) as exc_info:
        parser.parse(schema_file)

    error = exc_info.value
    assert "Missing" in str(error) or "missing" in str(error).lower()
    assert error.schema_version is None


def test_version_error_provides_supported_versions(temp_dir: Path) -> None:
    """Test that VersionError includes list of supported versions."""
    parser = SchemaParser()

    schema_content = """schnitzel: "0.9"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    with pytest.raises(VersionError) as exc_info:
        parser.parse(schema_file)

    error = exc_info.value
    assert error.supported_versions is not None
    assert len(error.supported_versions) > 0
    assert "1.0" in error.supported_versions or "1.0.0" in error.supported_versions


def test_legacy_version_field_supported(temp_dir: Path) -> None:
    """Test that legacy 'version:' field is still supported."""
    parser = SchemaParser()

    # Old style with 'version:' instead of 'schnitzel:'
    schema_content = """version: "1.0"

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
    schema_file = temp_dir / "schema_legacy.yaml"
    schema_file.write_text(schema_content)

    # Should parse successfully
    schema = parser.parse(schema_file)
    assert schema is not None
    assert "User" in schema.models


def test_generate_command_rejects_invalid_version(temp_dir: Path) -> None:
    """Test that generate command properly handles version errors."""
    # Create schema with invalid version
    schema_content = """schnitzel: "3.5.0"

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

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail with version error
    assert result.exit_code == 1
    output_lower = result.stdout.lower()
    assert "version" in output_lower
    assert "error" in output_lower or "✗" in result.stdout


def test_generate_command_rejects_missing_version(temp_dir: Path) -> None:
    """Test that generate command handles missing version."""
    # Create schema without version
    schema_content = """models:
  Product:
    description: "Product model"
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

    # Should fail with version error
    assert result.exit_code == 1
    output_lower = result.stdout.lower()
    assert "version" in output_lower
    assert "missing" in output_lower or "error" in output_lower


def test_feature_schemas_dont_require_version(temp_dir: Path) -> None:
    """Test that feature schemas are exempt from version requirement."""
    parser = SchemaParser()

    # Feature schema without version
    schema_content = """feature:
  name: "auth"
  version: "1.0"
  description: "Authentication feature"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
"""
    schema_file = temp_dir / "feature.yaml"
    schema_file.write_text(schema_content)

    # Should parse successfully
    schema = parser.parse(schema_file)
    assert schema is not None
    assert schema.feature is not None
    assert schema.feature.name == "auth"
    assert "User" in schema.models


def test_version_with_whitespace_normalized(temp_dir: Path) -> None:
    """Test that version strings with whitespace are normalized."""
    parser = SchemaParser()

    # Version with extra whitespace
    schema_content = """schnitzel: " 1.0 "

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

    # Should parse successfully after normalization
    schema = parser.parse(schema_file)
    assert schema is not None
    assert "User" in schema.models


def test_numeric_version_converted_to_string(temp_dir: Path) -> None:
    """Test that numeric versions are converted to strings."""
    parser = SchemaParser()

    # Numeric version (YAML may parse as number)
    schema_content = """schnitzel: 1.0

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

    # Should parse successfully after conversion
    schema = parser.parse(schema_file)
    assert schema is not None
    assert "User" in schema.models
