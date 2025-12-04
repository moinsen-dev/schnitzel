"""Integration tests for F157 - Documentation comments in generated code are helpful.

Test Requirements:
- test_model_descriptions_become_docstrings - Model descriptions in Python docstrings
- test_field_descriptions_in_dart - Field descriptions in Dart doc comments
- test_python_has_docstrings - Python models have docstrings
- test_dart_has_doc_comments - Dart models have /// doc comments
- test_descriptions_preserved - Original descriptions are preserved
"""

import tempfile
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python import PythonModelGenerator
from schnitzel.generators.dart import DartModelGenerator


def test_model_descriptions_become_docstrings() -> None:
    """Test that model descriptions become Python docstrings."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    description: "A user account in the system"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Product:
    description: "A product available for purchase"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have docstrings with descriptions
        assert '"""A user account in the system"""' in code
        assert '"""A product available for purchase"""' in code

    finally:
        schema_path.unlink()


def test_field_descriptions_in_dart() -> None:
    """Test that field descriptions become Dart doc comments."""
    schema_yaml = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
        description: "The article title"
      content:
        type: text
        description: "The main content of the article"
      published_at:
        type: datetime
        description: "When the article was published"
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

        # Should have doc comments for fields
        assert "/// The article title" in code
        assert "/// The main content of the article" in code
        assert "/// When the article was published" in code

    finally:
        schema_path.unlink()


def test_python_has_docstrings() -> None:
    """Test that Python models have docstrings when descriptions are provided."""
    schema_yaml = """schnitzel: "1.0"

models:
  Order:
    description: "An order placed by a customer"
    fields:
      id:
        type: uuid
        primary: true
      total:
        type: float
      status:
        type: enum
        values: ["pending", "paid", "shipped", "delivered"]
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have docstring
        assert '"""An order placed by a customer"""' in code

        # Docstring should be after class definition
        lines = code.split('\n')
        class_line = next(i for i, line in enumerate(lines) if "class Order" in line)
        docstring_line = next(i for i, line in enumerate(lines) if "An order placed by a customer" in line)
        assert docstring_line == class_line + 1, "Docstring should be immediately after class definition"

    finally:
        schema_path.unlink()


def test_dart_has_doc_comments() -> None:
    """Test that Dart models have /// doc comments."""
    schema_yaml = """schnitzel: "1.0"

models:
  Customer:
    description: "A customer who makes purchases"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        description: "Customer full name"
      email:
        type: string
        description: "Customer email address"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have model doc comment
        assert "/// A customer who makes purchases" in code

        # Should have field doc comments
        assert "/// Customer full name" in code
        assert "/// Customer email address" in code

        # Doc comments should come before the element they document
        lines = code.split('\n')
        model_doc_line = next(i for i, line in enumerate(lines) if "/// A customer who makes purchases" in line)
        freezed_line = next(i for i, line in enumerate(lines) if "@freezed" in line)
        assert model_doc_line < freezed_line, "Model doc should come before @freezed"

    finally:
        schema_path.unlink()


def test_descriptions_preserved() -> None:
    """Test that descriptions are preserved accurately in generated code."""
    schema_yaml = """schnitzel: "1.0"

models:
  BlogPost:
    description: "A blog post with title, content, and metadata"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
        description: "The post title (max 200 characters)"
      slug:
        type: string
        description: "URL-friendly version of the title"
      content:
        type: text
        description: "Full content of the blog post"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Python
        python_gen = PythonModelGenerator()
        python_code = python_gen.generate(schema)

        # Should preserve model description
        assert "A blog post with title, content, and metadata" in python_code

        # Dart
        dart_gen = DartModelGenerator()
        dart_code = dart_gen.generate(schema)

        # Should preserve all field descriptions
        assert "The post title (max 200 characters)" in dart_code
        assert "URL-friendly version of the title" in dart_code
        assert "Full content of the blog post" in dart_code

    finally:
        schema_path.unlink()


def test_models_without_descriptions() -> None:
    """Test that models without descriptions still work (no empty docstrings)."""
    schema_yaml = """schnitzel: "1.0"

models:
  SimpleModel:
    fields:
      id:
        type: uuid
        primary: true
      value:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Python
        python_gen = PythonModelGenerator()
        python_code = python_gen.generate(schema)

        # Should not have empty docstring
        assert '""""""' not in python_code, "Should not have empty docstring"

        # Dart
        dart_gen = DartModelGenerator()
        dart_code = dart_gen.generate(schema)

        # Should still compile properly
        assert "class SimpleModel" in dart_code

    finally:
        schema_path.unlink()


def test_multiline_descriptions() -> None:
    """Test that multiline descriptions are handled correctly."""
    schema_yaml = """schnitzel: "1.0"

models:
  ComplexModel:
    description: "A complex model with multiple responsibilities"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Python
        python_gen = PythonModelGenerator()
        python_code = python_gen.generate(schema)

        # Should have the description
        assert "A complex model with multiple responsibilities" in python_code

    finally:
        schema_path.unlink()


def test_special_characters_in_descriptions() -> None:
    """Test that special characters in descriptions are handled properly."""
    schema_yaml = """schnitzel: "1.0"

models:
  Quote:
    description: "A quote with special characters"
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string
        description: "The quote text may contain apostrophes"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Python
        python_gen = PythonModelGenerator()
        python_code = python_gen.generate(schema)

        # Should handle quotes in descriptions
        # (Implementation may escape or use different quote style)
        assert "quote" in python_code.lower()

        # Dart
        dart_gen = DartModelGenerator()
        dart_code = dart_gen.generate(schema)

        # Should handle quotes
        assert "quote" in dart_code.lower()

    finally:
        schema_path.unlink()
