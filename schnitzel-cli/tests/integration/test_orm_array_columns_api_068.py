"""Integration test for API_068: SQLAlchemy ORM generator handles array columns.

Test Requirements:
1. Verify ORM generator handles list/array types
2. Verify generated code uses sa.ARRAY(element_type)
3. Create schema with array fields (e.g., tags: {type: list[string]})
4. Verify ARRAY type mapping with correct element type
5. Test different element types (string, int, float)

This test verifies the ORM generator correctly handles array/list field types
and maps them to SQLAlchemy's ARRAY type with proper element types.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMArrayColumns:
    """Test ORM generator correctly handles array/list column types."""

    def test_array_string_type_mapping(self):
        """Test that list[string] maps to sa.ARRAY(sa.String)."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type is used
        assert "sa.ARRAY(sa.String)" in code

        # Verify correct Python type hint
        assert "tags: Mapped[list[str] | None]" in code

        # Verify full column definition
        assert "tags: Mapped[list[str] | None] = mapped_column(sa.ARRAY(sa.String), nullable=True)" in code

    def test_array_int_type_mapping(self):
        """Test that list[int] maps to sa.ARRAY(sa.Integer)."""
        schema = SchnitzelSchema(
            models={
                "DataPoint": Model(
                    name="DataPoint",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "scores": FieldDefinition(type="list<int>", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with Integer
        assert "sa.ARRAY(sa.Integer)" in code

        # Verify correct Python type hint
        assert "scores: Mapped[list[int]]" in code

        # Verify full column definition (required field, so no | None)
        assert "scores: Mapped[list[int]] = mapped_column(sa.ARRAY(sa.Integer), nullable=False)" in code

    def test_array_float_type_mapping(self):
        """Test that list[float] maps to sa.ARRAY(sa.Float)."""
        schema = SchnitzelSchema(
            models={
                "Measurement": Model(
                    name="Measurement",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "readings": FieldDefinition(type="list<float>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with Float
        assert "sa.ARRAY(sa.Float)" in code

        # Verify correct Python type hint
        assert "readings: Mapped[list[float] | None]" in code

        # Verify full column definition
        assert "readings: Mapped[list[float] | None] = mapped_column(sa.ARRAY(sa.Float), nullable=True)" in code

    def test_array_bool_type_mapping(self):
        """Test that list[bool] maps to sa.ARRAY(sa.Boolean)."""
        schema = SchnitzelSchema(
            models={
                "Survey": Model(
                    name="Survey",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "answers": FieldDefinition(type="list<bool>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with Boolean
        assert "sa.ARRAY(sa.Boolean)" in code

        # Verify correct Python type hint
        assert "answers: Mapped[list[bool] | None]" in code

    def test_multiple_array_fields(self):
        """Test model with multiple array fields of different types."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                        "prices": FieldDefinition(type="list<float>", optional=True),
                        "stock_levels": FieldDefinition(type="list<int>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all array types are present
        assert "sa.ARRAY(sa.String)" in code
        assert "sa.ARRAY(sa.Float)" in code
        assert "sa.ARRAY(sa.Integer)" in code

        # Verify all type hints
        assert "tags: Mapped[list[str] | None]" in code
        assert "prices: Mapped[list[float] | None]" in code
        assert "stock_levels: Mapped[list[int] | None]" in code

    def test_array_field_with_required_constraint(self):
        """Test array field with required=True constraint."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "roles": FieldDefinition(type="list<string>", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Required array should not have | None
        assert "roles: Mapped[list[str]] = mapped_column(sa.ARRAY(sa.String), nullable=False)" in code

    def test_array_field_with_optional_constraint(self):
        """Test array field with optional=True constraint."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Optional array should have | None
        assert "tags: Mapped[list[str] | None] = mapped_column(sa.ARRAY(sa.String), nullable=True)" in code

    def test_mixed_array_and_scalar_fields(self):
        """Test model with both array and scalar fields."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                        "view_count": FieldDefinition(type="int", default=0),
                        "ratings": FieldDefinition(type="list<float>", optional=True),
                        "published": FieldDefinition(type="bool", default=False),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify scalar types
        assert "title: Mapped[str] = mapped_column(sa.String" in code
        assert "view_count: Mapped[int] = mapped_column(sa.Integer" in code
        assert "published: Mapped[bool] = mapped_column(sa.Boolean" in code

        # Verify array types
        assert "tags: Mapped[list[str] | None] = mapped_column(sa.ARRAY(sa.String)" in code
        assert "ratings: Mapped[list[float] | None] = mapped_column(sa.ARRAY(sa.Float)" in code

    def test_array_text_type_mapping(self):
        """Test that list[text] maps to sa.ARRAY(sa.Text)."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "paragraphs": FieldDefinition(type="list<text>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with Text
        assert "sa.ARRAY(sa.Text)" in code

        # Text maps to str in Python
        assert "paragraphs: Mapped[list[str] | None]" in code

    def test_complete_model_with_arrays(self):
        """Test complete model generation with array fields."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    description="Product catalog entry",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                        "prices": FieldDefinition(type="list<float>", required=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify class structure
        assert "class Product(Base):" in code
        assert '__tablename__ = "products"' in code
        assert '"""Product catalog entry"""' in code

        # Verify all fields
        assert "id: Mapped[uuid.UUID]" in code
        assert "name: Mapped[str]" in code
        assert "tags: Mapped[list[str] | None]" in code
        assert "prices: Mapped[list[float]]" in code
        assert "created_at: Mapped[datetime]" in code

        # Verify ARRAY types
        assert "sa.ARRAY(sa.String)" in code
        assert "sa.ARRAY(sa.Float)" in code

    def test_array_with_index_constraint(self):
        """Test array field with index=True (should still work)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True, index=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have both ARRAY type and index=True
        assert "sa.ARRAY(sa.String)" in code
        assert "index=True" in code
        assert "tags: Mapped[list[str] | None] = mapped_column(sa.ARRAY(sa.String), index=True, nullable=True)" in code

    def test_imports_not_affected_by_arrays(self):
        """Test that array fields don't add unnecessary imports."""
        schema = SchnitzelSchema(
            models={
                "Simple": Model(
                    name="Simple",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Standard imports should be present
        assert "from __future__ import annotations" in code
        assert "import uuid" in code
        assert "import sqlalchemy as sa" in code
        assert "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column" in code

        # No special imports needed for arrays (ARRAY is part of sa)
        # Just verify the code is valid
        assert "sa.ARRAY" in code

    def test_array_uuid_type_mapping(self):
        """Test that list[uuid] maps to sa.ARRAY(sa.UUID)."""
        schema = SchnitzelSchema(
            models={
                "Group": Model(
                    name="Group",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "member_ids": FieldDefinition(type="list<uuid>", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with UUID
        assert "sa.ARRAY(sa.UUID)" in code

        # Verify correct Python type hint
        assert "member_ids: Mapped[list[uuid.UUID] | None]" in code

    def test_empty_array_not_causing_errors(self):
        """Test that models without array fields still work."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should not contain ARRAY
        assert "sa.ARRAY" not in code

        # Should still be valid
        assert "class User(Base):" in code
        assert "name: Mapped[str]" in code

    def test_array_bracket_format_string(self):
        """Test that list[string] format (Python style) works correctly."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list[string]", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type is used
        assert "sa.ARRAY(sa.String)" in code
        assert "tags: Mapped[list[str] | None]" in code

    def test_array_bracket_format_int(self):
        """Test that list[int] format (Python style) works correctly."""
        schema = SchnitzelSchema(
            models={
                "DataPoint": Model(
                    name="DataPoint",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "values": FieldDefinition(type="list[int]", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with Integer
        assert "sa.ARRAY(sa.Integer)" in code
        assert "values: Mapped[list[int]]" in code

    def test_array_bracket_format_float(self):
        """Test that list[float] format (Python style) works correctly."""
        schema = SchnitzelSchema(
            models={
                "Measurement": Model(
                    name="Measurement",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "readings": FieldDefinition(type="list[float]", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify ARRAY type with Float
        assert "sa.ARRAY(sa.Float)" in code
        assert "readings: Mapped[list[float] | None]" in code

    def test_mixed_bracket_and_angle_formats(self):
        """Test that both list[type] and list<type> formats work in same schema."""
        schema = SchnitzelSchema(
            models={
                "Mixed": Model(
                    name="Mixed",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                        "scores": FieldDefinition(type="list[int]", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Both should generate ARRAY types
        assert "sa.ARRAY(sa.String)" in code
        assert "sa.ARRAY(sa.Integer)" in code
        assert "tags: Mapped[list[str] | None]" in code
        assert "scores: Mapped[list[int] | None]" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
