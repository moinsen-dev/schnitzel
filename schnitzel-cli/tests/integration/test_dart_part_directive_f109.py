"""Integration tests for F109 - Dart generator handles part directive for Freezed.

Test Requirements:
- test_part_directive_present - part directives are present in generated code
- test_part_freezed_file - part 'models.freezed.dart' is present
- test_part_g_file - part 'models.g.dart' is present
"""

import tempfile
from pathlib import Path

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart.models import DartModelGenerator


def test_part_directive_present() -> None:
    """Test that part directives are present in generated Dart code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check that part directives are present
        assert "part " in code, "Generated code should contain part directives"


def test_part_freezed_file() -> None:
    """Test that part 'models.freezed.dart' directive is present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check for freezed part directive
        assert "part 'models.freezed.dart';" in code, \
            "Generated code should include part 'models.freezed.dart';"


def test_part_g_file() -> None:
    """Test that part 'models.g.dart' directive is present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check for json_serializable part directive
        assert "part 'models.g.dart';" in code, \
            "Generated code should include part 'models.g.dart';"


def test_both_part_directives() -> None:
    """Test that both part directives are present together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Both directives should be present
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code


def test_part_directives_order() -> None:
    """Test that part directives appear after imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Split into lines
        lines = code.split("\n")

        # Find positions
        import_line_idx = None
        freezed_part_idx = None
        g_part_idx = None

        for i, line in enumerate(lines):
            if "import 'package:freezed_annotation" in line:
                import_line_idx = i
            if "part 'models.freezed.dart';" in line:
                freezed_part_idx = i
            if "part 'models.g.dart';" in line:
                g_part_idx = i

        # Verify order: imports come before part directives
        assert import_line_idx is not None, "Import statement should be present"
        assert freezed_part_idx is not None, "Freezed part directive should be present"
        assert g_part_idx is not None, "Json serializable part directive should be present"

        assert import_line_idx < freezed_part_idx, \
            "Imports should come before part directives"
        assert import_line_idx < g_part_idx, \
            "Imports should come before part directives"


def test_part_directives_with_multiple_models() -> None:
    """Test that part directives are present even with multiple models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
      title:
        type: string

  Comment:
    fields:
      id:
        type: uuid
      content:
        type: string
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Part directives should still be present (only once, not per model)
        assert code.count("part 'models.freezed.dart';") == 1, \
            "Should have exactly one freezed part directive"
        assert code.count("part 'models.g.dart';") == 1, \
            "Should have exactly one json_serializable part directive"


def test_part_directives_format() -> None:
    """Test that part directives are properly formatted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check format: part 'filename'; (with semicolon, single quotes)
        lines = [line.strip() for line in code.split("\n")]

        # Find part directive lines
        part_lines = [line for line in lines if line.startswith("part ")]

        # Should have 2 part directives
        assert len(part_lines) == 2, f"Should have 2 part directives, found {len(part_lines)}"

        # Each should end with semicolon
        for line in part_lines:
            assert line.endswith(";"), f"Part directive should end with semicolon: {line}"

        # Each should use single quotes
        for line in part_lines:
            assert "'" in line, f"Part directive should use single quotes: {line}"


def test_part_directives_in_file_output() -> None:
    """Test that part directives are present when writing to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        # Generate to file
        output_dir = Path(tmpdir) / "output"
        generator = DartModelGenerator()
        output_file, _ = generator.generate_to_file(schema, output_dir)

        # Read generated file
        generated_code = output_file.read_text()

        # Verify part directives are in the file
        assert "part 'models.freezed.dart';" in generated_code
        assert "part 'models.g.dart';" in generated_code
