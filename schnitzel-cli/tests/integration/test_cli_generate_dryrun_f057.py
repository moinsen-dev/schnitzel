"""Integration tests for F057 - Generate command with --dry-run flag.

Test Requirements:
- test_generate_dryrun_option_exists - verify --dry-run and -n flags work
- test_generate_dryrun_does_not_write_files - no files created in dry-run mode
- test_generate_dryrun_shows_planned_files - displays what would be generated
- test_generate_dryrun_shows_target_paths - shows output file paths
- test_generate_dryrun_with_all_targets - shows all targets that would be generated
- test_generate_dryrun_with_python_target - shows only Python files
- test_generate_dryrun_with_flutter_target - shows only Dart files
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


@pytest.fixture
def sample_schema(temp_dir: Path):
    """Create a sample schema file for testing."""
    schema_content = """schnitzel: 1.0.0

models:
  User:
    description: A user in the system
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_generate_dryrun_option_exists(temp_dir: Path, sample_schema: Path) -> None:
    """Test that --dry-run and -n flags are recognized."""
    # Test --dry-run flag
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run"])
    assert result.exit_code == 0, f"--dry-run flag failed: {result.stdout}"
    assert "DRY RUN MODE" in result.stdout, "Missing dry-run mode indicator"

    # Test -n short flag
    result = runner.invoke(app, ["generate", str(sample_schema), "-n"])
    assert result.exit_code == 0, f"-n flag failed: {result.stdout}"
    assert "DRY RUN MODE" in result.stdout, "Missing dry-run mode indicator for -n"


def test_generate_dryrun_does_not_write_files(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run mode does not create any files."""
    # Run generate with --dry-run
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify no files were created
    backend_dir = temp_dir / "backend" / "app"
    packages_dir = temp_dir / "packages" / "app" / "lib" / "models"
    docker_compose = temp_dir / "docker-compose.yaml"

    assert not backend_dir.exists(), "backend/app directory should not be created in dry-run"
    assert not packages_dir.exists(), "packages directory should not be created in dry-run"
    assert not docker_compose.exists(), "docker-compose.yaml should not be created in dry-run"

    # Verify output mentions no files were written
    assert "No files were written" in result.stdout, "Missing 'no files written' message"


def test_generate_dryrun_shows_planned_files(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run mode displays what would be generated."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify dry-run mode message
    assert "DRY RUN MODE" in result.stdout, "Missing dry-run mode header"
    assert "Files that would be generated" in result.stdout, "Missing files header"

    # Verify file types are shown
    assert "Python models" in result.stdout, "Missing Python models in output"
    assert "Dart models" in result.stdout, "Missing Dart models in output"
    assert "Docker Compose" in result.stdout, "Missing Docker Compose in output"


def test_generate_dryrun_shows_target_paths(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run mode shows output file paths."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify file paths are displayed
    assert "backend/app/models.py" in result.stdout, "Missing Python models path"
    assert "packages/app/lib/models/models.dart" in result.stdout, "Missing Dart models path"
    assert "docker-compose.yaml" in result.stdout, "Missing Docker Compose path"


def test_generate_dryrun_shows_file_sizes(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run mode shows file sizes."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify file sizes are shown
    assert "Size:" in result.stdout, "Missing file size information"
    assert ("bytes" in result.stdout or "KB" in result.stdout), "Missing size unit"

    # Verify summary with total size
    assert "Summary:" in result.stdout, "Missing summary section"
    assert "Total size:" in result.stdout, "Missing total size in summary"


def test_generate_dryrun_with_all_targets(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run with --target all shows all targets."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run", "--target", "all"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify all three targets are shown
    assert "Python models" in result.stdout, "Missing Python in --target all"
    assert "Dart models" in result.stdout, "Missing Dart in --target all"
    assert "Docker Compose" in result.stdout, "Missing Docker in --target all"

    # Verify summary shows 3 files
    assert "Files to generate: 3" in result.stdout, "Should show 3 files for --target all"


def test_generate_dryrun_with_python_target(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run with --target python shows only Python files."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run", "--target", "python"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify Python models are shown
    assert "Python models" in result.stdout, "Missing Python models"
    assert "backend/app/models.py" in result.stdout, "Missing Python path"

    # Verify Dart and Docker are NOT shown
    assert "Dart models" not in result.stdout, "Dart should not appear with --target python"
    assert "Docker Compose" not in result.stdout, "Docker should not appear with --target python"

    # Verify summary shows 1 file
    assert "Files to generate: 1" in result.stdout, "Should show 1 file for --target python"


def test_generate_dryrun_with_flutter_target(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run with --target flutter shows only Dart files."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run", "--target", "flutter"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify Dart models are shown
    assert "Dart models" in result.stdout, "Missing Dart models"
    assert "packages/app/lib/models/models.dart" in result.stdout, "Missing Dart path"

    # Verify Python and Docker are NOT shown
    assert "Python models" not in result.stdout, "Python should not appear with --target flutter"
    assert "Docker Compose" not in result.stdout, "Docker should not appear with --target flutter"

    # Verify summary shows 1 file
    assert "Files to generate: 1" in result.stdout, "Should show 1 file for --target flutter"


def test_generate_dryrun_with_dart_target(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run with --target dart shows only Dart files."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run", "--target", "dart"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify Dart models are shown
    assert "Dart models" in result.stdout, "Missing Dart models"
    assert "packages/app/lib/models/models.dart" in result.stdout, "Missing Dart path"

    # Verify Python and Docker are NOT shown
    assert "Python models" not in result.stdout, "Python should not appear with --target dart"
    assert "Docker Compose" not in result.stdout, "Docker should not appear with --target dart"


def test_generate_dryrun_with_docker_target(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run with --target docker shows only Docker Compose."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run", "--target", "docker"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify Docker Compose is shown
    assert "Docker Compose" in result.stdout, "Missing Docker Compose"
    assert "docker-compose.yaml" in result.stdout, "Missing Docker Compose path"

    # Verify Python and Dart are NOT shown
    assert "Python models" not in result.stdout, "Python should not appear with --target docker"
    assert "Dart models" not in result.stdout, "Dart should not appear with --target docker"

    # Verify summary shows 1 file
    assert "Files to generate: 1" in result.stdout, "Should show 1 file for --target docker"


def test_generate_dryrun_shows_model_count(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run mode shows model count for model generators."""
    result = runner.invoke(app, ["generate", str(sample_schema), "--dry-run"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify model count is shown in summary
    assert "Models: 1" in result.stdout, "Missing model count in summary"


def test_generate_dryrun_with_multiple_models(temp_dir: Path) -> None:
    """Test dry-run with schema containing multiple models."""
    # Create schema with multiple models
    schema_content = """schnitzel: 1.0.0

models:
  User:
    description: A user in the system
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    description: A blog post
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      author_id:
        type: uuid

  Comment:
    description: A comment on a post
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
      post_id:
        type: uuid
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file), "--dry-run"])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify model count shows 3 models
    assert "Models: 3" in result.stdout, "Should show 3 models in summary"


def test_generate_dryrun_with_output_dir(temp_dir: Path, sample_schema: Path) -> None:
    """Test that dry-run respects --output directory option."""
    output_dir = temp_dir / "custom-output"

    result = runner.invoke(app, [
        "generate", str(sample_schema),
        "--dry-run",
        "--output", str(output_dir)
    ])
    assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    # Verify paths include custom output directory (checking for path components)
    # Note: Rich console may wrap long paths with line breaks
    output_normalized = result.stdout.replace("\n", "")  # Remove line breaks for checking
    assert "custom-output" in result.stdout, "Missing custom-output directory in path"
    assert "backend" in output_normalized and "app" in output_normalized and "models.py" in output_normalized, "Missing backend/app/models.py components"
    assert "packages" in output_normalized and "models.dart" in output_normalized, "Missing Dart models components"
    assert "docker-compose.yaml" in output_normalized, "Missing docker-compose.yaml"

    # Verify custom output directory was NOT created
    assert not output_dir.exists(), "Output directory should not be created in dry-run mode"


def test_generate_normal_mode_creates_files(temp_dir: Path, sample_schema: Path) -> None:
    """Test that normal mode (without --dry-run) actually creates files."""
    # Run generate WITHOUT --dry-run
    result = runner.invoke(app, ["generate", str(sample_schema)])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify files WERE created
    backend_file = temp_dir / "backend" / "app" / "models.py"
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_file = temp_dir / "docker-compose.yaml"

    assert backend_file.exists(), "backend/app/models.py should be created in normal mode"
    assert dart_file.exists(), "Dart models should be created in normal mode"
    assert docker_file.exists(), "docker-compose.yaml should be created in normal mode"

    # Verify output does NOT mention dry-run
    assert "DRY RUN MODE" not in result.stdout, "Should not show dry-run message in normal mode"
    assert "No files were written" not in result.stdout, "Should not say no files written in normal mode"


def test_generate_dryrun_combined_with_force(temp_dir: Path, sample_schema: Path) -> None:
    """Test that --dry-run can be combined with --force flag."""
    result = runner.invoke(app, [
        "generate", str(sample_schema),
        "--dry-run",
        "--force"
    ])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify dry-run mode is active
    assert "DRY RUN MODE" in result.stdout, "Dry-run should be active"
    assert "No files were written" in result.stdout, "No files should be written"

    # Verify files were not created even with --force
    backend_dir = temp_dir / "backend" / "app"
    assert not backend_dir.exists(), "Files should not be created even with --force in dry-run"
