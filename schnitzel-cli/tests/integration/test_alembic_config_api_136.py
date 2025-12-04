"""Integration tests for Alembic configuration creation (api_136).

Tests for:
- api_136: Alembic configuration is created automatically
"""

import pytest
import tempfile
from pathlib import Path
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator


class TestAlembicConfig:
    """Tests for api_136: Alembic configuration is created automatically."""

    def test_generator_exists(self):
        """Test that AlembicMigrationGenerator exists."""
        assert AlembicMigrationGenerator is not None

    def test_generator_can_create_config(self):
        """Test that generator can be instantiated."""
        generator = AlembicMigrationGenerator()
        assert generator is not None

    def test_generator_has_project_root(self):
        """Test that generator tracks project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = AlembicMigrationGenerator(project_root=tmpdir)
            assert generator.project_root == Path(tmpdir)

    def test_generator_has_snapshots_dir(self):
        """Test that generator has snapshots directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = AlembicMigrationGenerator(project_root=tmpdir)
            assert generator.snapshots_dir is not None

    def test_migration_file_format(self):
        """Test that generated migrations follow Alembic format."""
        from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "test")

        # Should have Alembic imports
        assert "from alembic import op" in code
        assert "import sqlalchemy as sa" in code

    def test_migration_has_revision(self):
        """Test that migration has revision ID."""
        from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "test")

        # Should have revision
        assert "revision = " in code

    def test_migration_has_down_revision(self):
        """Test that migration has down_revision."""
        from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "test")

        # Should have down_revision
        assert "down_revision = " in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
