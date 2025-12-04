"""Integration tests for code generation performance (api_151).

Tests for:
- api_151: Performance test: Code generation completes in reasonable time
"""

import pytest
import time
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestPerformance:
    """Tests for api_151: Performance test: Code generation completes in reasonable time."""

    def test_orm_generator_small_schema_fast(self):
        """Test ORM generator with small schema completes quickly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()

        start = time.time()
        code = generator.generate(schema)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0
        assert code is not None

    def test_orm_generator_medium_schema(self):
        """Test ORM generator with medium schema (10 models)."""
        models = {}
        for i in range(10):
            models[f"Model{i}"] = Model(
                name=f"Model{i}",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "created_at": FieldDefinition(type="datetime"),
                }
            )

        schema = SchnitzelSchema(models=models)
        generator = SQLAlchemyORMGenerator()

        start = time.time()
        code = generator.generate(schema)
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0
        assert code is not None

    def test_routes_generator_performance(self):
        """Test routes generator performance."""
        endpoints = {}
        for i in range(10):
            endpoints[f"/resource{i}"] = {
                "GET": {"name": f"list_resource{i}"},
                "POST": {"name": f"create_resource{i}"}
            }
            endpoints[f"/resource{i}/{{id}}"] = {
                "GET": {"name": f"get_resource{i}"},
                "PUT": {"name": f"update_resource{i}"},
                "DELETE": {"name": f"delete_resource{i}"}
            }

        schema = SchnitzelSchema(
            models={
                "Resource": Model(
                    name="Resource",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints=endpoints
        )

        generator = FastAPIRouteGenerator()

        start = time.time()
        code = generator.generate(schema)
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0
        assert code is not None

    def test_dart_generator_performance(self):
        """Test Dart generator performance."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()

        start = time.time()
        code = generator.generate(schema)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0
        assert code is not None

    def test_generators_dont_slow_down_with_relations(self):
        """Test that relations don't significantly slow generation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                        "profile": Relation(type="hasOne", model="Profile"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                ),
                "Profile": Model(
                    name="Profile",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()

        start = time.time()
        code = generator.generate(schema)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0
        assert "relationship" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
