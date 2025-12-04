"""Integration tests for migration Alembic conventions (api_117).

Tests for:
- api_117: Generated migration files follow Alembic conventions
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator


class TestMigrationConventions:
    """Tests for api_117: Migration Alembic conventions."""

    def test_migration_has_revision(self):
        """Test migration includes revision."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "initial")
        assert "revision" in code

    def test_migration_has_upgrade_downgrade(self):
        """Test migration has upgrade/downgrade functions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "initial")
        assert "def upgrade" in code
        assert "def downgrade" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
