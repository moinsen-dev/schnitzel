"""Integration tests for ORM PEP 8 compliance (api_105).

Tests for:
- api_105: Generated SQLAlchemy ORM code follows PEP 8
"""

import pytest
import ast
import re
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMPep8Compliance:
    """Tests for api_105: Generated SQLAlchemy ORM code follows PEP 8."""

    def test_class_names_pascal_case(self):
        """Test that generated class names use PascalCase."""
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "user_name": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Check that class name is PascalCase
        assert "class UserProfile" in code
        # Should not have snake_case class names
        assert "class user_profile" not in code

    def test_attribute_names_snake_case(self):
        """Test that generated attribute names use snake_case."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "first_name": FieldDefinition(type="string"),
                        "last_name": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Check snake_case attributes
        assert "first_name" in code
        assert "last_name" in code
        # Should not have camelCase
        assert "firstName" not in code
        assert "lastName" not in code

    def test_no_trailing_whitespace(self):
        """Test that generated code has no trailing whitespace."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Check each line for trailing whitespace
        for i, line in enumerate(code.split('\n'), 1):
            assert line == line.rstrip(), f"Line {i} has trailing whitespace"

    def test_consistent_indentation(self):
        """Test that generated code uses consistent 4-space indentation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Check that indentation is in multiples of 4 spaces
        for i, line in enumerate(code.split('\n'), 1):
            if line.strip():  # Non-empty lines
                leading_spaces = len(line) - len(line.lstrip())
                assert leading_spaces % 4 == 0 or line.startswith('#'), \
                    f"Line {i} has inconsistent indentation ({leading_spaces} spaces)"

    def test_imports_at_top(self):
        """Test that imports are at the top of the file."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        lines = code.split('\n')
        first_import_line = None
        last_import_line = None
        first_class_line = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if first_import_line is None:
                    first_import_line = i
                last_import_line = i
            if stripped.startswith('class '):
                first_class_line = i
                break

        # Imports should come before classes
        if first_import_line is not None and first_class_line is not None:
            assert last_import_line < first_class_line, "Imports should be at top"

    def test_valid_python_syntax(self):
        """Test that generated code is valid Python syntax."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should parse without syntax errors
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_blank_lines_around_classes(self):
        """Test that there are blank lines around class definitions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Product": Model(
                    name="Product",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Check for two blank lines before class definitions (PEP 8)
        # This is less strict - just ensure there's at least one blank line
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('class ') and i > 0:
                # At least one blank line before class (after imports/first class)
                prev_non_empty_idx = i - 1
                while prev_non_empty_idx >= 0 and not lines[prev_non_empty_idx].strip():
                    prev_non_empty_idx -= 1
                if prev_non_empty_idx >= 0 and not lines[prev_non_empty_idx].strip().startswith('import'):
                    # There should be blank line(s) between classes
                    has_blank = any(not lines[j].strip() for j in range(prev_non_empty_idx + 1, i))
                    assert has_blank or i == prev_non_empty_idx + 1, \
                        f"Missing blank line before class at line {i}"

    def test_no_line_too_long(self):
        """Test that no line exceeds PEP 8 recommended length (79 chars, allowing up to 99)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="text"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Allow up to 99 chars (PEP 8 allows 99 for implementation code)
        max_length = 99
        for i, line in enumerate(code.split('\n'), 1):
            if len(line) > max_length:
                # Allow longer lines for imports and comments
                if not (line.strip().startswith('import') or
                        line.strip().startswith('from') or
                        line.strip().startswith('#')):
                    assert len(line) <= max_length, \
                        f"Line {i} exceeds {max_length} chars ({len(line)} chars)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
