"""Integration tests for migrations directory (api_137).

Tests for:
- api_137: Migrations are stored in version-controlled directory
"""

import pytest
import tempfile
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator


class TestMigrationsDirectory:
    """Tests for api_137: Migrations are stored in version-controlled directory."""

    def test_migration_to_file_creates_directory(self):
        """Test that generating to file creates directory if needed."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"

            path, revision = generator.generate_migration_to_file(
                schema,
                "Create User table",
                migrations_dir
            )

            # Directory should be created
            assert migrations_dir.exists()

    def test_migration_file_is_python(self):
        """Test that migration file is a Python file."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"

            path, revision = generator.generate_migration_to_file(
                schema,
                "Create User table",
                migrations_dir
            )

            # Should be a .py file
            assert path.suffix == ".py"

    def test_migration_file_has_revision_in_name(self):
        """Test that migration filename includes revision ID."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"

            path, revision = generator.generate_migration_to_file(
                schema,
                "Create User table",
                migrations_dir
            )

            # Filename should include revision
            assert revision in path.name

    def test_migration_file_is_readable(self):
        """Test that migration file is readable Python."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"

            path, revision = generator.generate_migration_to_file(
                schema,
                "Create User table",
                migrations_dir
            )

            # File should be readable
            content = path.read_text()
            assert "def upgrade" in content

    def test_multiple_migrations_stored(self):
        """Test that multiple migrations can be stored."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = AlembicMigrationGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"

            path1, rev1 = generator.generate_migration_to_file(
                schema,
                "First migration",
                migrations_dir
            )

            path2, rev2 = generator.generate_migration_to_file(
                schema,
                "Second migration",
                migrations_dir
            )

            # Both files should exist
            assert path1.exists()
            assert path2.exists()
            assert rev1 != rev2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
