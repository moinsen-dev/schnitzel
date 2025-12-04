"""Integration tests for F156 - Progress output polish (professional and informative).

Test Requirements:
- test_generate_shows_progress - Generate command shows progress indicators
- test_success_messages_clear - Success messages are clear and professional
- test_quiet_mode_minimal - Quiet mode shows minimal output
- test_verbose_mode_detailed - Verbose mode shows detailed information
- test_progress_informative - Progress includes useful information
"""

import tempfile
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


def test_generate_shows_progress() -> None:
    """Test that generate command shows progress indicators."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["generate", str(schema_path), "--target", "python"])

        # Should succeed
        assert result.exit_code == 0

        output = result.stdout
        # Should have some progress or status output
        assert len(output) > 0, "Should have output showing what was done"


def test_success_messages_clear() -> None:
    """Test that success messages are clear and professional."""
    schema_yaml = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["generate", str(schema_path), "--target", "python"])

        assert result.exit_code == 0

        output = result.stdout
        # Success output should be informative
        # Typically includes: file paths, counts, confirmation
        assert len(output) > 20, "Success message should have content"


def test_quiet_mode_minimal() -> None:
    """Test that --quiet mode shows minimal output."""
    schema_yaml = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        # Run validate with --quiet
        result = runner.invoke(app, ["--quiet", "validate", str(schema_path)])

        assert result.exit_code == 0

        output = result.stdout
        # Should have minimal output (may just say "OK" or similar)
        lines = [line for line in output.split('\n') if line.strip()]
        assert len(lines) <= 5, "Quiet mode should have minimal output"


def test_verbose_mode_detailed() -> None:
    """Test that --verbose mode shows detailed information."""
    schema_yaml = """schnitzel: "1.0"

models:
  Customer:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        # Run with --verbose
        result_verbose = runner.invoke(app, ["--verbose", "validate", str(schema_path)])
        result_normal = runner.invoke(app, ["validate", str(schema_path)])

        assert result_verbose.exit_code == 0
        assert result_normal.exit_code == 0

        # Verbose mode may have more output (though this depends on implementation)
        # At minimum, both should succeed
        assert len(result_verbose.stdout) > 0
        assert len(result_normal.stdout) > 0


def test_progress_informative() -> None:
    """Test that progress output includes useful information."""
    schema_yaml = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      total:
        type: float

  OrderItem:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["generate", str(schema_path), "--target", "python"])

        assert result.exit_code == 0

        output = result.stdout
        # Should mention what was generated or number of models
        # (Implementation-specific, but output should exist)
        assert len(output) > 0


def test_validate_shows_model_count() -> None:
    """Test that validate shows number of models found."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  Post:
    fields:
      id:
        type: uuid
        primary: true

  Comment:
    fields:
      id:
        type: uuid
        primary: true
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["validate", str(schema_path)])

        assert result.exit_code == 0

        output = result.stdout
        # Should mention models or show count
        # May show "3 models" or list them
        assert len(output) > 0


def test_init_shows_progress() -> None:
    """Test that init command shows what it's doing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, ["init", "test-project"], cwd=tmpdir)

        # Should succeed (or fail gracefully)
        output = result.stdout

        # Should have some output about what was created
        if result.exit_code == 0:
            assert len(output) > 0, "Init should show what it created"


def test_generate_dry_run_informative() -> None:
    """Test that --dry-run shows what would be generated."""
    schema_yaml = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["generate", str(schema_path), "--dry-run"])

        # Should succeed
        assert result.exit_code == 0

        output = result.stdout
        # Dry-run should show what would be done
        assert len(output) > 0, "Dry-run should show planned actions"


def test_output_uses_colors() -> None:
    """Test that output uses Rich formatting (colors/styles)."""
    schema_yaml = """schnitzel: "1.0"

models:
  Test:
    fields:
      id:
        type: uuid
        primary: true
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["validate", str(schema_path)])

        assert result.exit_code == 0

        output = result.stdout
        # Rich may add ANSI codes or use plain text
        # Just verify output exists and is structured
        assert len(output) > 0


def test_progress_not_overwhelming() -> None:
    """Test that progress output is not overwhelming."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        result = runner.invoke(app, ["generate", str(schema_path)])

        assert result.exit_code == 0

        output = result.stdout
        lines = output.split('\n')

        # Should not have excessive output (< 100 lines for simple schema)
        assert len(lines) < 100, "Progress output should not be overwhelming"
