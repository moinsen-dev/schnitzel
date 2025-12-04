"""Integration tests for F042 - Init command generates schema.schnitzel.yaml from full template.

Test Requirements:
- test_init_full_template_creates_schema
- test_init_full_template_has_multiple_models
- test_init_full_template_has_relationships
- test_init_full_template_is_valid_yaml
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest
import yaml

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


def test_init_full_template_creates_schema(temp_dir: Path) -> None:
    """Test that init command with --template full creates schema file."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify schema file was created
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    assert schema_file.exists(), "schema.schnitzel.yaml not created"
    assert schema_file.is_file(), "schema.schnitzel.yaml is not a file"

    # Verify schema file has content
    content = schema_file.read_text()
    assert len(content) > 100, "Schema file content is too short"
    assert "schnitzel:" in content, "Schema file missing schnitzel version"


def test_init_full_template_has_multiple_models(temp_dir: Path) -> None:
    """Test that full template includes multiple models (User, Post, Comment)."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify multiple models are present
    assert "User:" in content, "Missing User model"
    assert "Post:" in content, "Missing Post model"
    assert "Comment:" in content, "Missing Comment model"

    # Verify model descriptions
    assert "A user in the system" in content, "Missing User description"
    assert "A blog post" in content, "Missing Post description"
    assert "A comment on a post" in content, "Missing Comment description"


def test_init_full_template_has_relationships(temp_dir: Path) -> None:
    """Test that full template includes relationships between models."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify relationships are present
    assert "relations:" in content, "Missing relations section"
    assert "hasMany" in content, "Missing hasMany relationship type"
    assert "belongsTo" in content, "Missing belongsTo relationship type"

    # Verify specific relationships
    assert "posts:" in content, "Missing posts relationship"
    assert "comments:" in content, "Missing comments relationship"
    assert "author:" in content, "Missing author relationship"
    assert "foreign_key:" in content, "Missing foreign_key specification"


def test_init_full_template_is_valid_yaml(temp_dir: Path) -> None:
    """Test that full template generates valid YAML."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    # Read and parse schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify it's valid YAML
    try:
        schema_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")

    # Verify structure
    assert "schnitzel" in schema_data, "Missing schnitzel version in parsed YAML"
    assert "models" in schema_data, "Missing models in parsed YAML"
    assert isinstance(schema_data["models"], dict), "Models should be a dictionary"

    # Verify models exist
    models = schema_data["models"]
    assert "User" in models, "User model not in parsed YAML"
    assert "Post" in models, "Post model not in parsed YAML"
    assert "Comment" in models, "Comment model not in parsed YAML"


def test_init_full_template_has_field_types(temp_dir: Path) -> None:
    """Test that full template includes various field types."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify different field types
    assert "type: uuid" in content, "Missing uuid field type"
    assert "type: string" in content, "Missing string field type"
    assert "type: text" in content, "Missing text field type"
    assert "type: bool" in content, "Missing bool field type"
    assert "type: datetime" in content, "Missing datetime field type"


def test_init_full_template_has_field_options(temp_dir: Path) -> None:
    """Test that full template includes various field options."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify field options
    assert "primary: true" in content, "Missing primary field option"
    assert "unique: true" in content, "Missing unique field option"
    assert "optional: true" in content, "Missing optional field option"
    assert "default: true" in content, "Missing default field option"
    assert "auto: create" in content, "Missing auto field option"


def test_init_minimal_template_is_default(temp_dir: Path) -> None:
    """Test that minimal template is used by default (no --template flag)."""
    project_name = "test-project"

    # Run init command without template flag
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify it's the minimal template (empty models)
    assert "models: {}" in content, "Should use minimal template by default"
    assert "User:" not in content, "Minimal template should not have User model"
    assert "Post:" not in content, "Minimal template should not have Post model"


def test_init_minimal_template_explicit(temp_dir: Path) -> None:
    """Test that --template minimal works explicitly."""
    project_name = "test-project"

    # Run init command with minimal template explicitly
    result = runner.invoke(app, ["init", project_name, "--template", "minimal"])
    assert result.exit_code == 0

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Verify it's the minimal template
    assert "models: {}" in content, "Minimal template should have empty models"
    assert "User:" not in content, "Minimal template should not have models"


def test_init_invalid_template_fails(temp_dir: Path) -> None:
    """Test that invalid template choice fails gracefully."""
    project_name = "test-project"

    # Run init command with invalid template
    result = runner.invoke(app, ["init", project_name, "--template", "invalid"])

    # Verify command failed
    assert result.exit_code == 1, "Command should fail with invalid template"
    assert "Invalid template" in result.stdout or "invalid" in result.stdout.lower(), \
        "Error message should mention invalid template"


def test_init_full_template_short_flag(temp_dir: Path) -> None:
    """Test that -t shorthand works for --template."""
    project_name = "test-project"

    # Run init command with -t flag
    result = runner.invoke(app, ["init", project_name, "-t", "full"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify schema file has full template content
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()
    assert "User:" in content, "Should have full template content"
    assert "Post:" in content, "Should have full template content"


def test_init_full_template_output_message(temp_dir: Path) -> None:
    """Test that init command shows message about using full template."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    # Verify output mentions full template
    output = result.stdout.lower()
    assert "full" in output or "example" in output, \
        "Output should mention full template or example models"
