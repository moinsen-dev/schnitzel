"""Integration tests for F041 - Init command generates schema.schnitzel.yaml from minimal template.

Test Requirements:
- test_init_creates_minimal_template_by_default
- test_init_minimal_template_is_valid_yaml
- test_init_with_full_template_has_user_model

Note: "minimal" = bare bones starting point (empty models)
      "full" = comprehensive example with User, Post, Comment models
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


def test_init_creates_minimal_template_by_default(temp_dir: Path) -> None:
    """Test that init command creates minimal template by default."""
    project_name = "test-project"

    # Run init command without --template flag
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify schema file was created
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    assert schema_file.exists(), "schema.schnitzel.yaml not created"

    # Read schema content
    content = schema_file.read_text()

    # Verify it has the minimal template structure
    assert "models" in content, "Should have models section"
    # Minimal template is a bare-bones starting point


def test_init_minimal_template_is_valid_yaml(temp_dir: Path) -> None:
    """Test that minimal template generates valid YAML that can be parsed."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name, "--template", "minimal"])
    assert result.exit_code == 0

    # Read and parse schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # This should not raise an exception
    try:
        schema = yaml.safe_load(content)
    except yaml.YAMLError as e:
        pytest.fail(f"Generated schema is not valid YAML: {e}")

    # Verify basic structure
    assert isinstance(schema, dict), "Schema should be a dictionary"
    assert "version" in schema or "schnitzel" in schema, "Schema should have version field"
    assert "models" in schema, "Schema should have models field"


def test_init_with_full_template_has_user_model(temp_dir: Path) -> None:
    """Test that init command with 'full' template creates comprehensive schema with User model."""
    project_name = "test-project"

    # Run init command with full template
    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read schema file
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Parse YAML
    schema = yaml.safe_load(content)

    # Verify User model exists
    assert "models" in schema, "Schema should have models section"
    assert "User" in schema["models"], "Full template should have User model"

    # Verify User model structure
    user_model = schema["models"]["User"]
    assert "description" in user_model, "User model should have description"
    assert "fields" in user_model, "User model should have fields"

    # Verify User fields
    fields = user_model["fields"]
    assert "id" in fields, "User should have id field"
    assert "name" in fields, "User should have name field"
    assert "email" in fields, "User should have email field"
    assert "created_at" in fields, "User should have created_at field"


def test_init_full_template_has_relationships(temp_dir: Path) -> None:
    """Test that full template includes relationship examples."""
    project_name = "test-project"

    result = runner.invoke(app, ["init", project_name, "--template", "full"])
    assert result.exit_code == 0

    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    schema = yaml.safe_load(schema_file.read_text())

    # Verify relationships exist
    user_model = schema["models"]["User"]
    assert "relations" in user_model, "User should have relations"
    assert "posts" in user_model["relations"], "User should have posts relation"


def test_init_with_invalid_template_fails(temp_dir: Path) -> None:
    """Test that init command fails with invalid template option."""
    project_name = "test-project"

    # Run init command with invalid template
    result = runner.invoke(app, ["init", project_name, "--template", "invalid"])

    # Verify command failed
    assert result.exit_code == 1, "Command should fail with invalid template"
    assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower(), \
        "Error message should mention invalid template"


def test_init_template_option_short_flag(temp_dir: Path) -> None:
    """Test that init command accepts -t short flag for template option."""
    project_name = "test-project"

    # Run init command with -t short flag for full template
    result = runner.invoke(app, ["init", project_name, "-t", "full"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify schema file was created with full template
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()
    assert "User:" in content, "Should have User model when using -t full"
