"""Integration tests for F153 - Generated Dart code readability.

Test Requirements:
- test_has_imports - Code has proper import statements
- test_has_freezed_annotation - Code has @freezed annotations
- test_has_factory_constructors - Code has factory constructors
- test_has_part_directives - Code has part directives
- test_clear_structure - Code has clear, readable structure
"""

import tempfile
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart import DartModelGenerator


def test_has_imports() -> None:
    """Test that generated Dart code has proper import statements."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      created_at:
        type: datetime
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have import statements
        assert "import" in code
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code

        # Imports should be at the top
        lines = code.split('\n')
        import_lines = [i for i, line in enumerate(lines) if 'import' in line]
        assert import_lines, "Should have import statements"
        first_non_comment = next(i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('//'))
        assert import_lines[0] <= first_non_comment + 5, "Imports should be near top of file"

    finally:
        schema_path.unlink()


def test_has_freezed_annotation() -> None:
    """Test that generated code has @freezed annotations."""
    schema_yaml = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @freezed annotation
        assert "@freezed" in code

        # Should have class with mixin
        assert "class Product with _$Product" in code

    finally:
        schema_path.unlink()


def test_has_factory_constructors() -> None:
    """Test that generated code has factory constructors."""
    schema_yaml = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have const factory constructor
        assert "const factory Article(" in code
        assert "= _Article;" in code

        # Should have fromJson factory
        assert "factory Article.fromJson(Map<String, dynamic> json)" in code
        assert "_$ArticleFromJson(json)" in code

    finally:
        schema_path.unlink()


def test_has_part_directives() -> None:
    """Test that generated code has part directives for build_runner."""
    schema_yaml = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      total:
        type: float
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have part directives
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code

        # Part directives should be near the top (after imports)
        lines = code.split('\n')
        part_lines = [i for i, line in enumerate(lines) if line.startswith("part ")]
        import_lines = [i for i, line in enumerate(lines) if line.startswith("import ")]

        assert part_lines, "Should have part directives"
        if import_lines:
            assert min(part_lines) > max(import_lines), "Part directives should come after imports"

    finally:
        schema_path.unlink()


def test_clear_structure() -> None:
    """Test that generated Dart code has clear, readable structure."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    description: "A user of the system"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string

  Post:
    description: "A post created by a user"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      author_id:
        type: uuid
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Code should be well-structured
        lines = code.split('\n')

        # Should have blank lines between models
        assert any(line == '' for line in lines), "Should have blank lines"

        # Should have documentation comments
        assert "/// A user of the system" in code
        assert "/// A post created by a user" in code

        # Should have 2 @freezed annotations (one per model)
        assert code.count("@freezed") == 2

        # Should have 2 class definitions
        assert "class User with" in code
        assert "class Post with" in code

    finally:
        schema_path.unlink()


def test_readable_field_names() -> None:
    """Test that field names use proper snake_case mapping."""
    schema_yaml = """schnitzel: "1.0"

models:
  Customer:
    fields:
      id:
        type: uuid
        primary: true
      firstName:
        type: string
      lastName:
        type: string
      emailAddress:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # CamelCase fields should be preserved in Dart
        assert "firstName" in code
        assert "lastName" in code
        assert "emailAddress" in code

        # Should have @JsonKey annotations for snake_case JSON mapping
        assert "@JsonKey(name: 'first_name')" in code
        assert "@JsonKey(name: 'last_name')" in code
        assert "@JsonKey(name: 'email_address')" in code

    finally:
        schema_path.unlink()


def test_consistent_formatting() -> None:
    """Test that generated Dart code has consistent formatting."""
    schema_yaml = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
      description:
        type: string
        optional: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Check for consistent spacing
        lines = code.split('\n')

        # No lines should have trailing whitespace (except blank lines)
        for line in lines:
            if line.strip():
                assert line == line.rstrip(), f"Line should not have trailing whitespace: '{line}'"

        # Should have consistent indentation (2 spaces for Dart)
        indented_lines = [line for line in lines if line.startswith(' ') and line.strip()]
        for line in indented_lines:
            # Count leading spaces
            spaces = len(line) - len(line.lstrip())
            assert spaces % 2 == 0, f"Dart indentation should be multiple of 2: '{line}'"

    finally:
        schema_path.unlink()


def test_doc_comments_placement() -> None:
    """Test that documentation comments are properly placed."""
    schema_yaml = """schnitzel: "1.0"

models:
  Article:
    description: "A blog article with title and content"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
        description: "The article title"
      content:
        type: string
        description: "The article content"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have model documentation comment
        assert "/// A blog article with title and content" in code

        # Should have field documentation comments
        assert "/// The article title" in code
        assert "/// The article content" in code

        # Doc comments should come before the element they document
        lines = code.split('\n')

        # Find model doc comment
        model_doc_line = next(i for i, line in enumerate(lines) if "/// A blog article" in line)
        freezed_line = next(i for i, line in enumerate(lines) if "@freezed" in line)
        assert model_doc_line < freezed_line, "Model doc should be before @freezed"

    finally:
        schema_path.unlink()
