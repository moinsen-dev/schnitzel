"""
Test circular import detection in schema parser (F005).

This test verifies that the schema parser properly detects and reports
circular imports with a clear error message showing the dependency chain.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from schnitzel.schema import SchemaParser, CircularImportError


class TestCircularImports:
    """Test cases for circular import detection."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_circular_import_two_files(self, temp_dir):
        """
        Test F005 - Step 1-7: Detect circular import between two files.

        Test steps:
        1. Create a.yaml with imports: [b.yaml]
        2. Create b.yaml with imports: [a.yaml]
        3. Call SchemaParser.parse('a.yaml')
        4. Verify CircularImportError is raised
        5. Verify error message shows the circular dependency chain
        6. Verify error includes both file names
        7. Verify parser stops gracefully without infinite loop
        """
        # Step 1: Create a.yaml with imports: [b.yaml]
        a_yaml = temp_dir / "a.yaml"
        a_yaml.write_text("""
project_name: TestProject
imports:
  - b.yaml
models:
  ModelA:
    fields:
      id:
        type: uuid
      name:
        type: string
""")

        # Step 2: Create b.yaml with imports: [a.yaml]
        b_yaml = temp_dir / "b.yaml"
        b_yaml.write_text("""
imports:
  - a.yaml
models:
  ModelB:
    fields:
      id:
        type: uuid
      title:
        type: string
""")

        # Step 3: Call SchemaParser.parse('a.yaml')
        parser = SchemaParser()

        # Step 4: Verify CircularImportError is raised
        with pytest.raises(CircularImportError) as exc_info:
            parser.parse(a_yaml)

        error = exc_info.value

        # Step 5: Verify error message shows the circular dependency chain
        error_message = str(error)
        assert "Circular import detected" in error_message
        assert "Import chain:" in error_message

        # Step 6: Verify error includes both file names
        assert "a.yaml" in error_message
        assert "b.yaml" in error_message

        # Step 7: Verify parser stops gracefully without infinite loop
        # (If we got here without hanging, this passes)
        assert error.import_chain is not None
        assert len(error.import_chain) >= 2

    def test_circular_import_three_files(self, temp_dir):
        """Test circular import detection with three files (a -> b -> c -> a)."""
        # Create a.yaml -> imports b.yaml
        a_yaml = temp_dir / "a.yaml"
        a_yaml.write_text("""
project_name: TestProject
imports:
  - b.yaml
models:
  ModelA:
    fields:
      id:
        type: uuid
""")

        # Create b.yaml -> imports c.yaml
        b_yaml = temp_dir / "b.yaml"
        b_yaml.write_text("""
imports:
  - c.yaml
models:
  ModelB:
    fields:
      id:
        type: uuid
""")

        # Create c.yaml -> imports a.yaml (creates cycle)
        c_yaml = temp_dir / "c.yaml"
        c_yaml.write_text("""
imports:
  - a.yaml
models:
  ModelC:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()

        with pytest.raises(CircularImportError) as exc_info:
            parser.parse(a_yaml)

        error_message = str(exc_info.value)
        assert "Circular import detected" in error_message
        # All three files should appear in the chain
        assert "a.yaml" in error_message
        assert "b.yaml" in error_message
        assert "c.yaml" in error_message

    def test_circular_import_helpful_tip(self, temp_dir):
        """Test that error message includes helpful tip."""
        a_yaml = temp_dir / "a.yaml"
        a_yaml.write_text("""
project_name: TestProject
imports:
  - b.yaml
models: {}
""")

        b_yaml = temp_dir / "b.yaml"
        b_yaml.write_text("""
imports:
  - a.yaml
models: {}
""")

        parser = SchemaParser()

        with pytest.raises(CircularImportError) as exc_info:
            parser.parse(a_yaml)

        error_message = str(exc_info.value)
        assert "tip:" in error_message.lower()
        assert "break the cycle" in error_message.lower()

    def test_no_circular_import_linear_chain(self, temp_dir):
        """Test that linear import chains (no cycles) work correctly."""
        # Create a.yaml -> imports b.yaml
        a_yaml = temp_dir / "a.yaml"
        a_yaml.write_text("""
schnitzel: "1.0"
imports:
  - b.yaml
models:
  ModelA:
    fields:
      id:
        type: uuid
""")

        # Create b.yaml -> imports c.yaml (no cycle)
        b_yaml = temp_dir / "b.yaml"
        b_yaml.write_text("""
imports:
  - c.yaml
models:
  ModelB:
    fields:
      id:
        type: uuid
""")

        # Create c.yaml (leaf node, no imports)
        c_yaml = temp_dir / "c.yaml"
        c_yaml.write_text("""
models:
  ModelC:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()

        # This should NOT raise CircularImportError
        schema = parser.parse(a_yaml)

        # Verify all models were loaded
        assert "ModelA" in schema.models
        assert "ModelB" in schema.models
        assert "ModelC" in schema.models

    def test_self_import(self, temp_dir):
        """Test that a file importing itself is detected as circular."""
        a_yaml = temp_dir / "a.yaml"
        a_yaml.write_text("""
project_name: TestProject
imports:
  - a.yaml
models:
  ModelA:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()

        with pytest.raises(CircularImportError) as exc_info:
            parser.parse(a_yaml)

        error_message = str(exc_info.value)
        assert "Circular import detected" in error_message
        assert "a.yaml" in error_message
