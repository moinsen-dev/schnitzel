"""Integration tests for SQLAlchemy ORM basic model generation (api_001).

Tests for:
- api_001: SQLAlchemy ORM generator creates basic model with primary key
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMBasicModel:
    """Tests for api_001: SQLAlchemy ORM generator creates basic model with primary key."""

    def test_generates_user_class(self):
        """Test ORM generates User class."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have User class
        assert "class User" in code

    def test_inherits_from_base(self):
        """Test User class inherits from SQLAlchemy Base."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should inherit from Base
        assert "Base" in code
        # Should use SQLAlchemy patterns
        assert "Mapped" in code or "mapped_column" in code

    def test_uuid_primary_key(self):
        """Test id field is mapped to UUID primary key."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have UUID type and primary_key
        assert "UUID" in code or "uuid" in code.lower()
        assert "primary_key" in code

    def test_string_column(self):
        """Test name field is mapped to String column."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have String type
        assert "String" in code
        assert "name" in code

    def test_generates_valid_python(self):
        """Test generated code is syntactically valid Python."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have proper imports
        assert "import" in code or "from" in code

        # Code should be compilable
        compile(code, "<string>", "exec")

    def test_has_table_name(self):
        """Test model has __tablename__ defined."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have table name
        assert "__tablename__" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
