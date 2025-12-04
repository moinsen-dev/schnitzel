"""Integration tests for API_036: Database migration generator creates initial migration."""

import re
import tempfile
from pathlib import Path

import pytest

from schnitzel.generators.infra.migrations import AlembicMigrationGenerator
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


class TestMigrationGeneratorBasic:
    """Test basic migration generation functionality."""

    def test_generate_initial_migration_with_user_model(self):
        """Test generating an initial migration with a User model."""
        # Create a simple schema with User model
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", required=True, unique=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="initial", down_revision=None
        )

        # Verify migration structure
        assert '"""initial' in migration_code
        assert "Revision ID:" in migration_code
        assert "Revises:" in migration_code
        assert "Create Date:" in migration_code

        # Verify imports
        assert "from alembic import op" in migration_code
        assert "import sqlalchemy as sa" in migration_code

        # Verify revision metadata
        assert "revision = " in migration_code
        assert "down_revision = None" in migration_code
        assert "branch_labels = None" in migration_code
        assert "depends_on = None" in migration_code

        # Verify upgrade function
        assert "def upgrade() -> None:" in migration_code
        assert "op.create_table('users'," in migration_code

        # Verify columns
        assert "sa.Column('id', sa.UUID(), nullable=False)" in migration_code
        assert "sa.Column('name', sa.String(), nullable=False)" in migration_code
        assert "sa.Column('email', sa.String(), nullable=False)" in migration_code

        # Verify primary key constraint
        assert "sa.PrimaryKeyConstraint('id')" in migration_code

        # Verify downgrade function
        assert "def downgrade() -> None:" in migration_code
        assert "op.drop_table('users')" in migration_code

    def test_revision_id_format(self):
        """Test that revision ID is 8 characters."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Extract revision ID
        match = re.search(r"revision = ['\"]([^'\"]+)['\"]", migration_code)
        assert match is not None
        revision_id = match.group(1)

        # Verify format (8 hexadecimal characters)
        assert len(revision_id) == 8
        assert all(c in "0123456789abcdef" for c in revision_id.lower())

    def test_down_revision_none_for_initial(self):
        """Test that down_revision is None for initial migration."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="initial", down_revision=None
        )

        assert "down_revision = None" in migration_code
        assert "Revises: \n" in migration_code or "Revises:\n" in migration_code

    def test_down_revision_with_previous_migration(self):
        """Test that down_revision references previous migration."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="add_profile", down_revision="abc12345"
        )

        assert "down_revision = 'abc12345'" in migration_code
        assert "Revises: abc12345" in migration_code


class TestMigrationGeneratorFileOutput:
    """Test migration file generation."""

    def test_generate_migration_to_file(self):
        """Test generating migration and writing to file."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            generator = AlembicMigrationGenerator()
            migration_file, revision_id = generator.generate_migration_to_file(
                schema=schema,
                migration_name="initial",
                migrations_dir=migrations_dir,
                down_revision=None,
            )

            # Verify file was created
            assert migration_file.exists()
            assert migration_file.parent == migrations_dir

            # Verify filename format
            assert migration_file.name.startswith(revision_id)
            assert migration_file.name.endswith(".py")
            assert "initial" in migration_file.name

            # Verify file content
            content = migration_file.read_text(encoding="utf-8")
            assert "def upgrade() -> None:" in content
            assert "def downgrade() -> None:" in content
            assert f"revision = '{revision_id}'" in content

    def test_migrations_directory_created(self):
        """Test that migrations directory is created if it doesn't exist."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / ".schnitzel" / "migrations"

            # Directory shouldn't exist yet
            assert not migrations_dir.exists()

            generator = AlembicMigrationGenerator()
            migration_file, _ = generator.generate_migration_to_file(
                schema=schema,
                migration_name="initial",
                migrations_dir=migrations_dir,
                down_revision=None,
            )

            # Directory should now exist
            assert migrations_dir.exists()
            assert migrations_dir.is_dir()
            assert migration_file.exists()

    def test_filename_sanitization(self):
        """Test that migration names are sanitized for filenames."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            generator = AlembicMigrationGenerator()

            # Test with spaces
            migration_file, _ = generator.generate_migration_to_file(
                schema=schema,
                migration_name="add user profile",
                migrations_dir=migrations_dir,
                down_revision=None,
            )

            assert "add_user_profile" in migration_file.name.lower()
            assert " " not in migration_file.name


class TestMigrationGeneratorTableCreation:
    """Test CREATE TABLE generation."""

    def test_create_table_with_multiple_fields(self):
        """Test CREATE TABLE with multiple field types."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                        "content": FieldDefinition(type="text", required=True),
                        "published": FieldDefinition(type="bool", default=False),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="create_posts", down_revision=None
        )

        # Verify table name (pluralized)
        assert "op.create_table('posts'," in migration_code

        # Verify all columns are present
        assert "sa.Column('id', sa.UUID(), nullable=False)" in migration_code
        assert "sa.Column('title', sa.String(), nullable=False)" in migration_code
        assert "sa.Column('content', sa.Text(), nullable=False)" in migration_code
        assert "sa.Column('published', sa.Boolean(), nullable=False)" in migration_code
        assert "sa.Column('created_at', sa.DateTime(), nullable=False)" in migration_code

    def test_table_name_pluralization(self):
        """Test that table names are correctly pluralized."""
        test_cases = [
            ("User", "users"),
            ("Post", "posts"),
            ("Category", "categories"),
            ("Address", "addresses"),
        ]

        for model_name, expected_table_name in test_cases:
            schema = SchnitzelSchema(
                models={
                    model_name: Model(
                        name=model_name,
                        fields={
                            "id": FieldDefinition(type="uuid", primary=True),
                        },
                    )
                }
            )

            generator = AlembicMigrationGenerator()
            migration_code = generator.generate_initial_migration(
                schema=schema, migration_name="test", down_revision=None
            )

            assert f"op.create_table('{expected_table_name}'," in migration_code
            assert f"op.drop_table('{expected_table_name}')" in migration_code

    def test_nullable_fields(self):
        """Test that optional fields are marked as nullable."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "bio": FieldDefinition(type="text", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Required field should be nullable=False
        assert "sa.Column('name', sa.String(), nullable=False)" in migration_code

        # Optional field should be nullable=True
        assert "sa.Column('bio', sa.Text(), nullable=True)" in migration_code


class TestMigrationGeneratorMultipleModels:
    """Test migration generation with multiple models."""

    def test_multiple_models_creates_multiple_tables(self):
        """Test that multiple models generate multiple CREATE TABLE statements."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="initial", down_revision=None
        )

        # Verify both tables are created
        assert "op.create_table('users'," in migration_code
        assert "op.create_table('posts'," in migration_code

        # Verify both tables are dropped in downgrade
        assert "op.drop_table('users')" in migration_code
        assert "op.drop_table('posts')" in migration_code

    def test_models_with_relationships(self):
        """Test migration generation with foreign key relationships."""
        from schnitzel.schema.models import Relation

        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="initial", down_revision=None
        )

        # Verify foreign key column is created
        assert "author_id" in migration_code
        assert "sa.ForeignKey('users.id')" in migration_code

        # Verify User table is created before Post table (dependency order)
        users_pos = migration_code.index("op.create_table('users',")
        posts_pos = migration_code.index("op.create_table('posts',")
        assert users_pos < posts_pos


class TestMigrationGeneratorDataTypes:
    """Test different data type mappings."""

    def test_string_type_mapping(self):
        """Test string type is mapped to sa.String()."""
        schema = SchnitzelSchema(
            models={
                "Test": Model(
                    name="Test",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "text": FieldDefinition(type="string"),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        assert "sa.Column('text', sa.String()" in migration_code

    def test_integer_type_mapping(self):
        """Test integer type is mapped to sa.Integer()."""
        schema = SchnitzelSchema(
            models={
                "Test": Model(
                    name="Test",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "count": FieldDefinition(type="int"),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        assert "sa.Column('count', sa.Integer()" in migration_code

    def test_boolean_type_mapping(self):
        """Test boolean type is mapped to sa.Boolean()."""
        schema = SchnitzelSchema(
            models={
                "Test": Model(
                    name="Test",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "active": FieldDefinition(type="bool"),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        assert "sa.Column('active', sa.Boolean()" in migration_code

    def test_datetime_type_mapping(self):
        """Test datetime type is mapped to sa.DateTime()."""
        schema = SchnitzelSchema(
            models={
                "Test": Model(
                    name="Test",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime"),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        assert "sa.Column('created_at', sa.DateTime()" in migration_code

    def test_text_type_mapping(self):
        """Test text type is mapped to sa.Text()."""
        schema = SchnitzelSchema(
            models={
                "Test": Model(
                    name="Test",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "description": FieldDefinition(type="text"),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        assert "sa.Column('description', sa.Text()" in migration_code


class TestMigrationGeneratorEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_schema(self):
        """Test migration generation with empty schema."""
        schema = SchnitzelSchema(models={})

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="empty", down_revision=None
        )

        # Should still generate valid migration structure
        assert "def upgrade() -> None:" in migration_code
        assert "def downgrade() -> None:" in migration_code
        assert "pass" in migration_code  # No operations

    def test_model_with_no_fields(self):
        """Test migration with model that has no fields."""
        schema = SchnitzelSchema(
            models={
                "Empty": Model(
                    name="Empty",
                    fields={},
                )
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Should still create table even without columns
        assert "op.create_table('empties'," in migration_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
