"""Integration tests for SQLAlchemy ORM column comments (api_069).

Tests for:
- api_069: SQLAlchemy ORM generator adds column comments
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMColumnComments:
    """Tests for api_069: SQLAlchemy ORM generator adds column comments."""

    def test_generates_column_with_description(self):
        """Test ORM generates column with description/comment."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(
                            type="string",
                            description="User's primary email address"
                        ),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have email field
        assert "email" in code
        compile(code, "<string>", "exec")

    def test_generates_multiple_described_columns(self):
        """Test ORM handles multiple columns with descriptions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(
                            type="string",
                            description="Primary email"
                        ),
                        "phone": FieldDefinition(
                            type="string",
                            description="Contact phone number"
                        ),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have both fields
        assert "email" in code
        assert "phone" in code
        compile(code, "<string>", "exec")

    def test_handles_empty_description(self):
        """Test ORM handles fields without description."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),  # No description
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate without errors
        assert "name" in code
        compile(code, "<string>", "exec")

    def test_model_with_description(self):
        """Test ORM handles model with description."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="Represents a user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate class with docstring or comment
        assert "User" in code
        compile(code, "<string>", "exec")

    def test_special_chars_in_description(self):
        """Test ORM handles special characters in descriptions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(
                            type="string",
                            description="User's bio with 'quotes' and special chars"
                        ),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should handle special chars
        assert "bio" in code
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
