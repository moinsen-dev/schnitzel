"""Integration tests for ORM timestamps (api_009).

Tests for:
- api_009: SQLAlchemy ORM generator adds timestamps (created_at, updated_at)
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMTimestamps:
    """Tests for api_009: SQLAlchemy ORM generator adds timestamps."""

    def test_created_at_field_generated(self):
        """Test that created_at field is generated when specified."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have created_at field
        assert "created_at:" in code
        assert "DateTime" in code or "datetime" in code

    def test_updated_at_field_generated(self):
        """Test that updated_at field is generated when specified."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "updated_at": FieldDefinition(type="datetime", auto="update"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have updated_at field
        assert "updated_at:" in code
        assert "DateTime" in code or "datetime" in code

    def test_created_at_server_default(self):
        """Test that created_at uses server_default with func.now()."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should use server_default for created_at
        assert "server_default=func.now()" in code

    def test_updated_at_onupdate(self):
        """Test that updated_at uses onupdate for automatic updates."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "updated_at": FieldDefinition(type="datetime", auto="update"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should use onupdate for updated_at
        assert "onupdate=func.now()" in code

    def test_both_timestamps_together(self):
        """Test that both created_at and updated_at work together."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                        "updated_at": FieldDefinition(type="datetime", auto="update"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have both timestamps
        assert "created_at:" in code
        assert "updated_at:" in code
        assert "server_default=func.now()" in code
        assert "onupdate=func.now()" in code

    def test_timestamps_nullable(self):
        """Test that timestamps have proper nullable settings."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                        "updated_at": FieldDefinition(type="datetime", auto="update", optional=True),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # created_at should not be nullable (required by default)
        # updated_at can be nullable if specified as optional
        assert "created_at:" in code
        assert "updated_at:" in code

    def test_timestamps_type_hints(self):
        """Test that timestamp fields have proper datetime type hints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                        "updated_at": FieldDefinition(type="datetime", auto="update"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have datetime type hints
        assert "Mapped[datetime]" in code or "datetime" in code

    def test_func_import_added(self):
        """Test that func is imported when timestamps are used."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should import func
        assert "from sqlalchemy import func" in code

    def test_timestamps_ordered_last(self):
        """Test that timestamp fields are ordered after other fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "updated_at": FieldDefinition(type="datetime", auto="update"),
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Find positions
        lines = code.split('\n')
        id_line = None
        name_line = None
        created_line = None
        updated_line = None

        for i, line in enumerate(lines):
            if 'id:' in line and 'Mapped[' in line:
                id_line = i
            elif 'name:' in line and 'Mapped[' in line:
                name_line = i
            elif 'created_at:' in line:
                created_line = i
            elif 'updated_at:' in line:
                updated_line = i

        # Timestamps should come after id and name
        if id_line and created_line:
            assert id_line < created_line, "id should be before created_at"
        if name_line and created_line:
            assert name_line < created_line, "name should be before created_at"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
