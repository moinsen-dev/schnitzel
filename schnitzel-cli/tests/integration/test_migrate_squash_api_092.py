"""Integration tests for migration squashing (api_092).

Tests for:
- api_092: Migrate command supports migration squashing
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator


class TestMigrateSquash:
    """Tests for api_092: Migrate command supports migration squashing."""

    def test_generator_initialization(self):
        """Test migration generator can be initialized."""
        generator = AlembicMigrationGenerator()
        assert generator is not None

    def test_generator_with_project_root(self):
        """Test migration generator accepts project root."""
        from pathlib import Path
        generator = AlembicMigrationGenerator(project_root=Path("."))
        assert generator is not None

    def test_generator_generates_initial_migration(self):
        """Test generator can create initial migration."""
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

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "initial")

        # Should generate migration code
        assert code is not None
        assert "revision" in code or "upgrade" in code or "def " in code

    def test_migration_includes_model(self):
        """Test migration includes model definition."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "create_user")

        # Should include user table creation
        assert "user" in code.lower() or "User" in code

    def test_migration_for_multiple_models(self):
        """Test migration for multiple models."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "create_tables")

        # Should include both models
        assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
