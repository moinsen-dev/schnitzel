"""Integration tests for F147 - Freezed code generation with build_runner compatibility.

Test Requirements:
- test_has_freezed_annotation - Models have @freezed annotation
- test_has_part_directives - Has part directives for .freezed.dart and .g.dart
- test_has_const_factory - Has const factory constructors
- test_has_fromjson - Has fromJson factory method
- test_build_runner_compatible - Generated code works with build_runner
"""

import tempfile
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart import DartModelGenerator


def test_has_freezed_annotation() -> None:
    """Test that generated Dart models have @freezed annotation."""
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
        assert "@freezed" in code, "Should have @freezed annotation"

        # Should have freezed_annotation import
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code

        # Should have the mixin
        assert "with _$Product" in code

    finally:
        schema_path.unlink()


def test_has_part_directives() -> None:
    """Test that generated code has part directives for build_runner."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      username:
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

        # Should have part directives
        assert "part 'models.freezed.dart';" in code, "Should have .freezed.dart part directive"
        assert "part 'models.g.dart';" in code, "Should have .g.dart part directive"

    finally:
        schema_path.unlink()


def test_has_const_factory() -> None:
    """Test that generated models have const factory constructors."""
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
        type: text
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
        assert "const factory Article(" in code, "Should have const factory constructor"
        assert "= _Article;" in code, "Should have private implementation class"

    finally:
        schema_path.unlink()


def test_has_fromjson() -> None:
    """Test that generated models have fromJson factory method."""
    schema_yaml = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      published:
        type: bool
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have fromJson factory
        assert "factory Post.fromJson(Map<String, dynamic> json)" in code
        assert "_$PostFromJson(json)" in code

    finally:
        schema_path.unlink()


def test_build_runner_compatible() -> None:
    """Test that generated code structure is compatible with build_runner."""
    schema_yaml = """schnitzel: "1.0"

models:
  Category:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
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

        # Check all required elements for build_runner
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code
        assert "@freezed" in code
        assert "const factory Category(" in code
        assert ".fromJson(Map<String, dynamic> json)" in code

    finally:
        schema_path.unlink()


def test_multiple_models_freezed() -> None:
    """Test that all models in a schema get @freezed annotation."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
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

        # Count @freezed annotations - should be 3 (one per model)
        freezed_count = code.count("@freezed")
        assert freezed_count == 3, f"Should have 3 @freezed annotations, found {freezed_count}"

        # Check each model has factory
        assert "const factory User(" in code
        assert "const factory Post(" in code
        assert "const factory Comment(" in code

        # Check each model has fromJson
        assert "factory User.fromJson" in code
        assert "factory Post.fromJson" in code
        assert "factory Comment.fromJson" in code

    finally:
        schema_path.unlink()


def test_freezed_with_relationships() -> None:
    """Test that relationships work correctly with Freezed."""
    schema_yaml = """schnitzel: "1.0"

models:
  Author:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
    relations:
      books:
        type: hasMany
        model: Book

  Book:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      author_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: Author
        foreign_key: author_id
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should still have @freezed for both models
        assert code.count("@freezed") == 2

        # Should have relationships in factory constructors
        assert "List<Book>? books," in code or "books," in code
        assert "Author? author," in code or "author," in code

    finally:
        schema_path.unlink()
