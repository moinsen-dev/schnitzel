"""Integration tests for ORM type hints (api_106).

Tests for:
- api_106: Generated SQLAlchemy ORM includes type hints
"""

import pytest
import ast
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMTypeHints:
    """Tests for api_106: Generated SQLAlchemy ORM includes type hints."""

    def test_uuid_field_has_type_hint(self):
        """Test that UUID fields have proper type hints."""
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

        # Should use Mapped[UUID] type hint
        assert "Mapped[" in code
        assert "UUID" in code

    def test_string_field_has_type_hint(self):
        """Test that string fields have proper type hints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have str type hint
        assert "Mapped[str]" in code or "str" in code

    def test_int_field_has_type_hint(self):
        """Test that int fields have proper type hints."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "quantity": FieldDefinition(type="int"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have int type hint
        assert "Mapped[int]" in code or ": int" in code

    def test_bool_field_has_type_hint(self):
        """Test that bool fields have proper type hints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "is_active": FieldDefinition(type="bool"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have bool type hint
        assert "Mapped[bool]" in code or ": bool" in code

    def test_datetime_field_has_type_hint(self):
        """Test that datetime fields have proper type hints."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have datetime type hint
        assert "datetime" in code

    def test_optional_field_has_optional_type_hint(self):
        """Test that optional fields have Optional type hint."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string", optional=True),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should indicate optional (either Optional[] or | None)
        # SQLAlchemy 2.0 uses Mapped[str | None] or Mapped[Optional[str]]
        assert "None" in code or "Optional" in code

    def test_mapped_column_syntax(self):
        """Test that SQLAlchemy 2.0 Mapped/mapped_column syntax is used."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should use SQLAlchemy 2.0 syntax
        assert "Mapped[" in code
        assert "mapped_column" in code

    def test_valid_type_annotations(self):
        """Test that type annotations are valid Python."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int"),
                        "is_active": FieldDefinition(type="bool"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should parse without errors (type hints are valid)
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"Type hints produce invalid syntax: {e}")

    def test_imports_for_type_hints(self):
        """Test that necessary imports for type hints are included."""
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

        # Should import Mapped from sqlalchemy.orm
        assert "from sqlalchemy.orm" in code
        assert "Mapped" in code

    def test_float_field_has_type_hint(self):
        """Test that float fields have proper type hints."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "price": FieldDefinition(type="float"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have float type hint
        assert "Mapped[float]" in code or ": float" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
