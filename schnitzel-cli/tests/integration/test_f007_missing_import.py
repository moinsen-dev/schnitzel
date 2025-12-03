"""
Integration test for F007: Schema parser raises error when importing non-existent file.

This test validates that the SchemaParser properly handles missing import files
with helpful error messages.
"""

import tempfile
from pathlib import Path

import pytest

from schnitzel.schema.exceptions import ImportError as SchnitzelImportError
from schnitzel.schema.parser import SchemaParser


class TestF007MissingImport:
    """Test schema parser error handling for non-existent imports (F007)."""

    def test_missing_import_raises_error(self) -> None:
        """
        Test F007: Schema parser raises error when importing non-existent file.

        Test Steps:
        1. Create main.yaml with imports: [nonexistent.yaml]
        2. Call SchemaParser.parse('main.yaml')
        3. Verify FileNotFoundError or ImportError is raised
        4. Verify error message includes the missing filename
        5. Verify error message includes the importing file name
        6. Verify helpful suggestion to check file path
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = Path(tmpdir) / "main.yaml"

            # Step 1: Create main.yaml with imports: [nonexistent.yaml]
            main_content = """
schnitzel: 1.0.0
imports:
  - nonexistent.yaml
models:
  Post:
    fields:
      id:
        type: uuid
      title:
        type: string
"""
            main_path.write_text(main_content)

            # Step 2: Call SchemaParser.parse('main.yaml')
            parser = SchemaParser()

            # Step 3: Verify FileNotFoundError or ImportError is raised
            with pytest.raises((FileNotFoundError, SchnitzelImportError)) as exc_info:
                parser.parse(main_path)

            error_msg = str(exc_info.value)

            # Step 4: Verify error message includes the missing filename
            assert "nonexistent.yaml" in error_msg, (
                f"Error message should include missing filename 'nonexistent.yaml'. "
                f"Got: {error_msg}"
            )

            # Step 5: Verify error message includes the importing file name
            assert "main.yaml" in error_msg, (
                f"Error message should include importing file name 'main.yaml'. "
                f"Got: {error_msg}"
            )

            # Step 6: Verify helpful suggestion to check file path
            assert (
                "check" in error_msg.lower() or "path" in error_msg.lower()
            ), (
                f"Error message should include helpful suggestion about checking file path. "
                f"Got: {error_msg}"
            )

    def test_missing_import_with_relative_path(self) -> None:
        """Test error handling for missing import with relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create subdirectory
            models_dir = tmpdir_path / "models"
            models_dir.mkdir()

            main_path = tmpdir_path / "main.yaml"

            # Create main.yaml trying to import non-existent file in subdirectory
            main_content = """
schnitzel: 1.0.0
imports:
  - ./models/missing.yaml
models:
  Post:
    fields:
      id:
        type: uuid
"""
            main_path.write_text(main_content)

            # Parse should raise error
            parser = SchemaParser()
            with pytest.raises((FileNotFoundError, SchnitzelImportError)) as exc_info:
                parser.parse(main_path)

            error_msg = str(exc_info.value)

            # Verify error message contains path information
            assert "missing.yaml" in error_msg or "./models/missing.yaml" in error_msg
            assert "main.yaml" in error_msg

    def test_missing_import_preserves_exception_attributes(self) -> None:
        """Test that ImportError exception has proper attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = Path(tmpdir) / "main.yaml"

            main_content = """
schnitzel: 1.0.0
imports:
  - nonexistent.yaml
models: {}
"""
            main_path.write_text(main_content)

            parser = SchemaParser()

            with pytest.raises(SchnitzelImportError) as exc_info:
                parser.parse(main_path)

            exception = exc_info.value

            # Verify exception has the required attributes
            assert hasattr(exception, "missing_file"), "ImportError should have missing_file attribute"
            assert hasattr(exception, "importing_file"), "ImportError should have importing_file attribute"

            # Verify attribute values
            assert exception.missing_file == "nonexistent.yaml"
            assert exception.importing_file == "main.yaml"

    def test_missing_import_in_nested_file(self) -> None:
        """Test error handling when a nested import file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            main_path = Path(tmpdir) / "main.yaml"

            # Create base.yaml that imports a missing file
            base_content = """
schnitzel: 1.0.0
imports:
  - missing_nested.yaml
models:
  User:
    fields:
      id:
        type: uuid
"""
            base_path.write_text(base_content)

            # Create main.yaml that imports base.yaml
            main_content = """
schnitzel: 1.0.0
imports:
  - base.yaml
models:
  Post:
    fields:
      id:
        type: uuid
"""
            main_path.write_text(main_content)

            # Parse should raise error for the nested missing file
            parser = SchemaParser()
            with pytest.raises((FileNotFoundError, SchnitzelImportError)) as exc_info:
                parser.parse(main_path)

            error_msg = str(exc_info.value)

            # Verify error mentions the missing nested file
            assert "missing_nested.yaml" in error_msg
            # Should mention base.yaml as the importing file (not main.yaml)
            assert "base.yaml" in error_msg

    def test_multiple_missing_imports_first_error_raised(self) -> None:
        """Test that when multiple imports are missing, the first error is raised."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = Path(tmpdir) / "main.yaml"

            # Create main.yaml with multiple missing imports
            main_content = """
schnitzel: 1.0.0
imports:
  - first_missing.yaml
  - second_missing.yaml
models:
  Post:
    fields:
      id:
        type: uuid
"""
            main_path.write_text(main_content)

            parser = SchemaParser()

            with pytest.raises((FileNotFoundError, SchnitzelImportError)) as exc_info:
                parser.parse(main_path)

            error_msg = str(exc_info.value)

            # Should report the first missing import
            assert "first_missing.yaml" in error_msg
            assert "main.yaml" in error_msg
