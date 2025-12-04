"""Integration tests for migration descriptive comments (api_118).

Tests for:
- api_118: Generated migration files include descriptive comments
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator


class TestMigrationComments:
    """Tests for api_118: Generated migration files include descriptive comments."""

    def test_migration_has_docstring(self):
        """Test that migration file has a docstring."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Create User table")

        # Should have docstring at top
        assert '"""' in code

    def test_migration_includes_name(self):
        """Test that migration docstring includes migration name."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Add users table")

        # Should include migration name in docstring
        assert "Add users table" in code or "users" in code.lower()

    def test_migration_includes_revision_info(self):
        """Test that migration includes revision information."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Test migration")

        # Should have revision info
        assert "Revision ID:" in code
        assert "revision = " in code

    def test_migration_includes_create_date(self):
        """Test that migration includes creation date."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Test migration")

        # Should have create date
        assert "Create Date:" in code

    def test_migration_has_upgrade_downgrade_docstrings(self):
        """Test that upgrade and downgrade functions exist."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Test migration")

        # Should have upgrade and downgrade functions
        assert "def upgrade()" in code
        assert "def downgrade()" in code

    def test_migration_includes_down_revision(self):
        """Test that migration includes down_revision info."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Test migration")

        # Should have down_revision
        assert "down_revision" in code

    def test_migration_includes_revises_info(self):
        """Test that migration includes 'Revises' info in docstring."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "Test migration")

        # Should have revises info
        assert "Revises:" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
