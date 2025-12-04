"""Integration tests for templates handling single model (api_128).

Tests for:
- api_128: Templates handle edge case: single model
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestTemplatesSingleModel:
    """Tests for api_128: Templates handle edge case: single model."""

    def test_orm_generator_single_model(self):
        """Test ORM generator with single model."""
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

        # Should generate valid code with User model
        assert "User" in code
        assert "class" in code

    def test_routes_generator_single_model(self):
        """Test routes generator with single model."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid routes
        assert "list_users" in code or "/users" in code or "@router" in code

    def test_dart_generator_single_model(self):
        """Test Dart generator with single model."""
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

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate valid Dart code
        assert "class" in code

    def test_single_model_with_all_field_types(self):
        """Test single model with various field types."""
        schema = SchnitzelSchema(
            models={
                "AllTypes": Model(
                    name="AllTypes",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int"),
                        "score": FieldDefinition(type="float"),
                        "active": FieldDefinition(type="bool"),
                        "created_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should handle all types
        assert "AllTypes" in code

    def test_single_model_minimal(self):
        """Test single model with only primary key."""
        schema = SchnitzelSchema(
            models={
                "Minimal": Model(
                    name="Minimal",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generators = [
            SQLAlchemyORMGenerator(),
            FastAPIRouteGenerator(),
            DartApiClientGenerator(),
        ]

        for generator in generators:
            code = generator.generate(schema)
            assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
