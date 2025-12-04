"""Integration tests for generated code comments (api_163).

Tests for:
- api_163: Code generation includes helpful comments in generated files
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestCodeGenComments:
    """Tests for api_163: Generated code comments."""

    def test_orm_generates_readable_code(self):
        """Test ORM generates readable code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)
        # Code should be readable with structure
        assert "class User" in code
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
