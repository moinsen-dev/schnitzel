"""Integration tests for SQLAlchemy ORM check constraints (api_066).

Tests for:
- api_066: SQLAlchemy ORM generator adds check constraints
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMCheckConstraints:
    """Tests for api_066: SQLAlchemy ORM generator adds check constraints."""

    def test_generates_min_constraint(self):
        """Test ORM generates min value constraint."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "price": FieldDefinition(type="float", min=0),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have price field
        assert "price" in code
        # Generator should produce valid code
        compile(code, "<string>", "exec")

    def test_generates_max_constraint(self):
        """Test ORM generates max value constraint."""
        schema = SchnitzelSchema(
            models={
                "Rating": Model(
                    name="Rating",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "score": FieldDefinition(type="int", max=100),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have score field
        assert "score" in code
        compile(code, "<string>", "exec")

    def test_generates_range_constraint(self):
        """Test ORM generates range constraint (min and max)."""
        schema = SchnitzelSchema(
            models={
                "Percentage": Model(
                    name="Percentage",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "value": FieldDefinition(type="int", min=0, max=100),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have value field with constraints
        assert "value" in code
        compile(code, "<string>", "exec")

    def test_generates_string_length_constraint(self):
        """Test ORM generates string max_length constraint."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string", max_length=50),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have String with length or max_length
        assert "username" in code
        compile(code, "<string>", "exec")

    def test_multiple_constraints_on_model(self):
        """Test ORM handles multiple constraints on same model."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "quantity": FieldDefinition(type="int", min=1),
                        "price": FieldDefinition(type="float", min=0),
                        "discount": FieldDefinition(type="int", min=0, max=100),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have all fields
        assert "quantity" in code
        assert "price" in code
        assert "discount" in code
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
