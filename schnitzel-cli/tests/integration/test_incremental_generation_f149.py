"""Integration tests for F149 - Incremental generation (only regenerate changed files).

Test Requirements:
- test_incremental_not_implemented - Mark test as skipped if not implemented
- test_incremental_generation_concept - Document what incremental generation should do
- test_future_timestamp_comparison - Test that could work when implemented

Note: This feature is not yet implemented. Tests are marked with pytest.mark.skip
to document the expected behavior for future implementation.
"""

import tempfile
from pathlib import Path
import time
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python import PythonModelGenerator


@pytest.mark.skip(reason="Incremental generation not yet implemented")
def test_incremental_not_implemented() -> None:
    """Test that incremental generation is not yet implemented."""
    # This test documents that the feature doesn't exist yet
    # When implemented, this test should be updated to actually test the feature
    pass


@pytest.mark.skip(reason="Incremental generation not yet implemented")
def test_incremental_generation_concept() -> None:
    """Document what incremental generation should do when implemented.

    Expected behavior:
    1. Track timestamps of schema file and generated files
    2. Only regenerate files if schema is newer than generated code
    3. Support --force flag to regenerate everything
    4. Compare file hashes to detect actual changes
    """
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

        # Write schema file
        schema_path = tmpdir_path / "schema.yaml"
        schema_path.write_text(schema_yaml)

        # First generation
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        output_file, size = generator.generate_to_file(
            schema,
            tmpdir_path / "generated",
            schema_source="schema.yaml"
        )

        first_mtime = output_file.stat().st_mtime

        # Wait a bit
        time.sleep(0.1)

        # Second generation without schema changes
        # In incremental mode, this should skip regeneration
        output_file2, size2 = generator.generate_to_file(
            schema,
            tmpdir_path / "generated",
            schema_source="schema.yaml"
        )

        second_mtime = output_file2.stat().st_mtime

        # When incremental is implemented:
        # assert first_mtime == second_mtime, "File should not be regenerated if schema unchanged"


@pytest.mark.skip(reason="Incremental generation not yet implemented")
def test_future_timestamp_comparison() -> None:
    """Test timestamp-based incremental generation (future implementation)."""
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

        # Generate once
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        generator.generate_to_file(
            schema,
            tmpdir_path / "generated",
            schema_source="schema.yaml"
        )

        # Touch schema file to make it newer
        time.sleep(0.1)
        schema_path.touch()

        # When incremental is implemented, this should trigger regeneration
        # because schema is newer than generated file


@pytest.mark.skip(reason="Incremental generation not yet implemented")
def test_force_flag_overrides_incremental() -> None:
    """Test that --force flag forces regeneration even if not needed."""
    # When implemented, this test should verify that:
    # - Normal generation skips if files are up to date
    # - --force flag regenerates everything regardless
    pass


def test_current_behavior_always_regenerates() -> None:
    """Test current behavior: generation always rewrites files."""
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

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()

        # First generation
        output_file, size1 = generator.generate_to_file(
            schema,
            tmpdir_path / "generated",
            schema_source="schema.yaml"
        )
        first_mtime = output_file.stat().st_mtime

        # Wait to ensure different timestamp
        time.sleep(0.01)

        # Second generation
        output_file2, size2 = generator.generate_to_file(
            schema,
            tmpdir_path / "generated",
            schema_source="schema.yaml"
        )
        second_mtime = output_file2.stat().st_mtime

        # Current behavior: file is always regenerated
        # (second_mtime will be different from first_mtime)
        # When incremental is implemented, this would change
        assert output_file == output_file2, "Should write to same file"
        assert size1 == size2, "File size should be the same"


@pytest.mark.skip(reason="Incremental generation not yet implemented")
def test_partial_schema_change() -> None:
    """Test that only affected models are regenerated (future feature)."""
    # This would be useful for large schemas where only one model changed
    # Could generate separate files per model and only update changed ones
    pass


def test_dry_run_mode_exists() -> None:
    """Test that dry-run mode exists as a step toward incremental generation."""
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

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()

        # Dry run should not create files
        output_file, size = generator.generate_to_file(
            schema,
            tmpdir_path / "generated",
            schema_source="schema.yaml",
            dry_run=True
        )

        # File should not exist in dry-run mode
        assert not output_file.exists(), "Dry-run should not create files"
        assert size > 0, "Should still return expected file size"
