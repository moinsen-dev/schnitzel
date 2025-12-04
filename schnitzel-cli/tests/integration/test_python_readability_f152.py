"""Integration tests for F152 - Generated Python code readability.

Test Requirements:
- test_has_imports - Code has proper import statements
- test_has_classes - Code has class definitions
- test_has_docstrings - Code has docstrings for models
- test_has_type_hints - Code has proper type hints
- test_clear_structure - Code has clear, readable structure
"""

import tempfile
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python import PythonModelGenerator


def test_has_imports() -> None:
    """Test that generated Python code has proper import statements."""
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

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have import statements
        assert "import" in code or "from" in code
        assert "from pydantic import BaseModel" in code
        assert "from uuid import UUID" in code
        assert "from datetime import datetime" in code

        # Imports should be at the top
        lines = code.split('\n')
        import_lines = [i for i, line in enumerate(lines) if 'import' in line]
        assert import_lines, "Should have import statements"
        assert max(import_lines) < len(lines) // 2, "Imports should be near top of file"

    finally:
        schema_path.unlink()


def test_has_classes() -> None:
    """Test that generated code has proper class definitions."""
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

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have class definition
        assert "class Product(BaseModel):" in code

        # Class should have fields
        assert "id: UUID" in code
        assert "name: str" in code
        assert "price: float" in code

    finally:
        schema_path.unlink()


def test_has_docstrings() -> None:
    """Test that generated code has docstrings for models with descriptions."""
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
      content:
        type: text
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
        assert '"""A blog article with title and content"""' in code

        # Docstring should be after class definition
        lines = code.split('\n')
        class_line = next(i for i, line in enumerate(lines) if "class Article" in line)
        docstring_line = next(i for i, line in enumerate(lines) if "A blog article" in line)
        assert docstring_line > class_line, "Docstring should be after class definition"

    finally:
        schema_path.unlink()


def test_has_type_hints() -> None:
    """Test that generated code has proper type hints."""
    schema_yaml = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      quantity:
        type: int
      total:
        type: float
      notes:
        type: string
        optional: true
      tags:
        type: list<string>
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have type hints for all fields
        assert "id: UUID" in code
        assert "quantity: int" in code
        assert "total: float" in code
        assert "notes: str | None" in code, "Optional fields should use union syntax"
        assert "tags: list[str]" in code, "List fields should use proper generic syntax"

    finally:
        schema_path.unlink()


def test_clear_structure() -> None:
    """Test that generated code has clear, readable structure."""
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

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Code should be well-structured
        lines = code.split('\n')

        # Should have blank lines between sections
        assert any(line == '' for line in lines), "Should have blank lines"

        # Should have proper indentation (4 spaces for class members)
        class_lines = [line for line in lines if line.startswith('class ')]
        field_lines = [line for line in lines if ': UUID' in line or ': str' in line]

        assert len(class_lines) == 2, "Should have 2 class definitions"
        assert len(field_lines) >= 5, "Should have multiple field definitions"

        # Fields should be indented
        for field_line in field_lines:
            if field_line.strip():
                assert field_line.startswith('    '), "Fields should be indented with 4 spaces"

    finally:
        schema_path.unlink()


def test_readable_field_names() -> None:
    """Test that field names are readable in generated code."""
    schema_yaml = """schnitzel: "1.0"

models:
  Customer:
    fields:
      id:
        type: uuid
        primary: true
      first_name:
        type: string
      last_name:
        type: string
      email_address:
        type: string
      phone_number:
        type: string
        optional: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Field names should be preserved (snake_case)
        assert "first_name: str" in code
        assert "last_name: str" in code
        assert "email_address: str" in code
        assert "phone_number: str | None" in code

        # Should not convert to camelCase
        assert "firstName" not in code
        assert "lastName" not in code

    finally:
        schema_path.unlink()


def test_consistent_formatting() -> None:
    """Test that generated code has consistent formatting."""
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
        min: 0
      description:
        type: text
        optional: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Check for consistent spacing
        lines = code.split('\n')

        # No lines should have trailing whitespace
        for line in lines:
            assert line == line.rstrip(), f"Line should not have trailing whitespace: '{line}'"

        # Should have consistent indentation (4 spaces)
        indented_lines = [line for line in lines if line.startswith(' ') and line.strip()]
        for line in indented_lines:
            # Count leading spaces
            spaces = len(line) - len(line.lstrip())
            assert spaces % 4 == 0, f"Indentation should be multiple of 4: '{line}'"

    finally:
        schema_path.unlink()
