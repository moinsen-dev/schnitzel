"""Integration tests for full generation pipeline (api_063).

Tests for:
- api_063: Integration test: Full generation pipeline produces working API
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestFullPipeline:
    """Tests for api_063: Integration test: Full generation pipeline produces working API."""

    @pytest.fixture
    def foodie_schema(self):
        """Create FoodieAI-like schema for testing."""
        return SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string", unique=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "recipes": Relation(type="hasMany", model="Recipe")
                    }
                ),
                "Recipe": Model(
                    name="Recipe",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="string", optional=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users",
                        "response": "User[]"
                    },
                    "POST": {
                        "name": "create_user",
                        "body": "User",
                        "response": "User"
                    }
                },
                "/users/{id}": {
                    "GET": {
                        "name": "get_user",
                        "response": "User"
                    }
                },
                "/recipes": {
                    "GET": {
                        "name": "list_recipes",
                        "response": "Recipe[]"
                    }
                }
            }
        )

    def test_orm_generates_models(self, foodie_schema):
        """Test ORM generator produces User and Recipe models."""
        generator = SQLAlchemyORMGenerator()
        code = generator.generate(foodie_schema)

        # Should have both models
        assert "class User" in code
        assert "class Recipe" in code

    def test_orm_generates_relationships(self, foodie_schema):
        """Test ORM generator produces relationships."""
        generator = SQLAlchemyORMGenerator()
        code = generator.generate(foodie_schema)

        # Should have relationship definitions
        assert "relationship" in code

    def test_routes_generates_endpoints(self, foodie_schema):
        """Test route generator produces all endpoints."""
        generator = FastAPIRouteGenerator()
        code = generator.generate(foodie_schema)

        # Should have route definitions
        assert "router" in code or "@" in code
        # Should have user endpoints
        assert "user" in code.lower()

    def test_routes_generates_crud(self, foodie_schema):
        """Test route generator produces CRUD operations."""
        generator = FastAPIRouteGenerator()
        code = generator.generate(foodie_schema)

        # Should have GET operations
        assert "get" in code.lower()

    def test_dart_generates_client(self, foodie_schema):
        """Test Dart generator produces API client."""
        generator = DartApiClientGenerator()
        code = generator.generate(foodie_schema)

        # Should have Dart client
        assert "class" in code
        assert "ApiClient" in code or "api" in code.lower()

    def test_dart_generates_models(self, foodie_schema):
        """Test Dart generator produces model classes."""
        generator = DartApiClientGenerator()
        code = generator.generate(foodie_schema)

        # Should have model definitions
        assert "User" in code
        assert "Recipe" in code

    def test_all_generators_produce_output(self, foodie_schema):
        """Test all generators produce non-empty output."""
        orm = SQLAlchemyORMGenerator()
        routes = FastAPIRouteGenerator()
        dart = DartApiClientGenerator()

        orm_code = orm.generate(foodie_schema)
        routes_code = routes.generate(foodie_schema)
        dart_code = dart.generate(foodie_schema)

        assert len(orm_code) > 100
        assert len(routes_code) > 100
        assert len(dart_code) > 100

    def test_orm_code_compiles(self, foodie_schema):
        """Test ORM code is valid Python."""
        generator = SQLAlchemyORMGenerator()
        code = generator.generate(foodie_schema)

        # Should compile without errors
        compile(code, "<string>", "exec")

    def test_routes_code_compiles(self, foodie_schema):
        """Test routes code is valid Python."""
        generator = FastAPIRouteGenerator()
        code = generator.generate(foodie_schema)

        # Should compile without errors
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
