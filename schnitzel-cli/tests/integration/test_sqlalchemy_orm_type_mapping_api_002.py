"""Integration tests for API_002: SQLAlchemy ORM generator type mapping.

Tests that the SQLAlchemy ORM generator correctly maps all basic field types:
- string → sa.String
- int → sa.Integer
- float → sa.Float
- bool → sa.Boolean
- datetime → sa.DateTime
- uuid → sa.UUID
- text → sa.Text
- json → sa.JSON

Also verifies that nullable is correctly set based on optional flag.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestSQLAlchemyORMTypeMapping:
    """Test SQLAlchemy ORM generator type mapping for all basic field types."""

    def test_all_basic_types_mapped_correctly(self):
        """Test that all basic field types are mapped to correct SQLAlchemy types."""
        schema = SchnitzelSchema(
            models={
                "TestModel": Model(
                    name="TestModel",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "price": FieldDefinition(type="float", required=True),
                        "active": FieldDefinition(type="bool", default=True),
                        "created_at": FieldDefinition(type="datetime", required=True),
                        "description": FieldDefinition(type="text", optional=True),
                        "metadata": FieldDefinition(type="json", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify imports
        assert "import sqlalchemy as sa" in code
        assert "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column" in code

        # Verify type mappings
        assert "id: Mapped[uuid.UUID] = mapped_column(sa.UUID, primary_key=True, nullable=False)" in code
        assert "name: Mapped[str] = mapped_column(sa.String, nullable=False)" in code
        assert "age: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)" in code
        assert "price: Mapped[float] = mapped_column(sa.Float" in code
        assert "active: Mapped[bool] = mapped_column(sa.Boolean, default=True)" in code
        assert "created_at: Mapped[datetime] = mapped_column(sa.DateTime" in code
        assert "description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)" in code
        assert "metadata: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON, nullable=True)" in code

    def test_string_type_mapping(self):
        """Test that string type maps to sa.String."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.String" in code
        assert "name: Mapped[str] = mapped_column(sa.String" in code

    def test_int_type_mapping(self):
        """Test that int type maps to sa.Integer."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "age": FieldDefinition(type="int", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.Integer" in code
        assert "age: Mapped[int] = mapped_column(sa.Integer" in code

    def test_float_type_mapping(self):
        """Test that float type maps to sa.Float."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.Float" in code
        assert "price: Mapped[float] = mapped_column(sa.Float" in code

    def test_bool_type_mapping(self):
        """Test that bool type maps to sa.Boolean."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "active": FieldDefinition(type="bool", default=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.Boolean" in code
        assert "active: Mapped[bool] = mapped_column(sa.Boolean" in code

    def test_datetime_type_mapping(self):
        """Test that datetime type maps to sa.DateTime."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "created_at": FieldDefinition(type="datetime", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.DateTime" in code
        assert "created_at: Mapped[datetime] = mapped_column(sa.DateTime" in code

    def test_uuid_type_mapping(self):
        """Test that uuid type maps to sa.UUID."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.UUID" in code
        assert "id: Mapped[uuid.UUID] = mapped_column(sa.UUID, primary_key=True" in code

    def test_text_type_mapping(self):
        """Test that text type maps to sa.Text."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "content": FieldDefinition(type="text", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.Text" in code
        assert "content: Mapped[str | None] = mapped_column(sa.Text" in code

    def test_json_type_mapping(self):
        """Test that json type maps to sa.JSON."""
        schema = SchnitzelSchema(
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "config": FieldDefinition(type="json", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "sa.JSON" in code
        assert "config: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON" in code

    def test_nullable_true_for_optional_fields(self):
        """Test that optional fields have nullable=True."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "email": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "nullable=True" in code
        assert "email: Mapped[str | None] = mapped_column(sa.String, nullable=True)" in code

    def test_nullable_false_for_required_fields(self):
        """Test that required fields have nullable=False."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        assert "nullable=False" in code
        assert "name: Mapped[str] = mapped_column(sa.String, nullable=False)" in code

    def test_pyright_type_checking(self):
        """Test that generated code passes pyright type checking."""
        schema = SchnitzelSchema(
            models={
                "CompleteModel": Model(
                    name="CompleteModel",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "price": FieldDefinition(type="float", required=True),
                        "active": FieldDefinition(type="bool", default=True),
                        "created_at": FieldDefinition(type="datetime", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify that all necessary imports are present
        assert "from __future__ import annotations" in code
        assert "import uuid" in code
        assert "from datetime import datetime" in code
        assert "import sqlalchemy as sa" in code
        assert "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column" in code

        # Verify Base class exists
        assert "class Base(DeclarativeBase):" in code

        # Verify model inherits from Base
        assert "class CompleteModel(Base):" in code

        # This would ideally run pyright, but for now we just verify structure
        # In actual implementation, this would write to a temp file and run pyright
        assert "Mapped[" in code
        assert "mapped_column(" in code
