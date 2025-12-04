"""Integration tests for proper imports (api_168).

Tests for:
- api_168: Generated code includes proper imports
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestProperImports:
    """Tests for api_168: Generated code includes proper imports."""

    def test_orm_has_sqlalchemy_imports(self):
        """Test that ORM code has SQLAlchemy imports."""
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

        # Should import SQLAlchemy
        assert "from sqlalchemy" in code or "import sqlalchemy" in code

    def test_orm_has_mapped_import(self):
        """Test that ORM imports Mapped for type annotations."""
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

        # Should import Mapped
        assert "Mapped" in code

    def test_routes_has_fastapi_imports(self):
        """Test that routes have FastAPI imports."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users": {"GET": {"name": "list_users"}}
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should import FastAPI components
        assert "from fastapi" in code or "import fastapi" in code or "APIRouter" in code

    def test_dart_has_dio_import(self):
        """Test that Dart code has Dio import."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should import Dio
        assert "import" in code
        assert "dio" in code.lower()

    def test_orm_has_uuid_import(self):
        """Test that ORM imports UUID when needed."""
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

        # Should handle UUID type
        assert "UUID" in code or "uuid" in code.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
