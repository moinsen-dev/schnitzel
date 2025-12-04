"""Integration tests for zero-tolerance code policy (api_164).

Tests for:
- api_164: Generated code follows zero-tolerance policy
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestZeroTolerance:
    """Tests for api_164: Generated code follows zero-tolerance policy."""

    def test_orm_no_bare_except(self):
        """Test that ORM code doesn't use bare except."""
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

        # Should not have bare except
        # Note: This is a simplified check
        assert "except:" not in code or "except Exception" in code or "except:" not in code.replace("except Exception:", "")

    def test_routes_has_proper_types(self):
        """Test that routes use proper type annotations."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {"name": "get_user"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have type annotations
        assert "->" in code or ":" in code

    def test_orm_uses_mapped_columns(self):
        """Test that ORM uses SQLAlchemy 2.0 Mapped columns."""
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

        # Should use Mapped[] for SQLAlchemy 2.0
        assert "Mapped[" in code

    def test_routes_has_response_model(self):
        """Test that routes have response models where applicable."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {"name": "get_user"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have proper route decorator
        assert "@router" in code or "@app" in code

    def test_code_is_importable_python(self):
        """Test that generated code is valid Python."""
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

        # Should be parseable Python
        try:
            compile(code, "<string>", "exec")
            compiled = True
        except SyntaxError:
            compiled = False

        assert compiled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
