"""Test for api_037: Database migration generator detects added columns.

This test verifies:
1. Create initial schema snapshot
2. Add new field to User model (email: string)
3. Run schnitzel migrate diff --name "add_email"
4. Verify migration contains ALTER TABLE ADD COLUMN
5. Verify column type and constraints are correct
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from schnitzel.generators.infra.migrations import (
    AlembicMigrationGenerator,
    SchemaSnapshot,
    SchemaDiff,
)
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


def test_detect_added_column():
    """Test that migration generator detects and generates ALTER TABLE ADD COLUMN."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Step 1: Create initial schema with User model (id, name)
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="Application user",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                )
            }
        )

        # Initialize migration generator
        generator = AlembicMigrationGenerator(project_root=project_root)

        # Generate initial migration
        initial_migration = generator.generate_initial_migration(
            schema=initial_schema,
            migration_name="create_users_table",
        )

        # Verify initial migration is created correctly
        assert "op.create_table('users'," in initial_migration
        assert "sa.Column('id', sa.UUID()" in initial_migration
        assert "sa.Column('name', sa.String()" in initial_migration

        # Save initial snapshot
        snapshot_path = generator.save_snapshot(initial_schema, "create_users_table")
        assert snapshot_path.exists()

        # Step 2: Add email field to User model
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="Application user",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        # Step 3: Generate diff migration
        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="add_email",
        )

        # Step 4: Verify migration contains ALTER TABLE ADD COLUMN
        assert "def upgrade() -> None:" in migration_code
        assert "def downgrade() -> None:" in migration_code
        assert "op.add_column('users'" in migration_code

        # Step 5: Verify column type and constraints are correct
        # The migration should add email column with correct type
        assert "sa.Column('email', sa.String()" in migration_code
        assert "nullable=True" in migration_code

        # Verify downgrade removes the column
        assert "op.drop_column('users', 'email')" in migration_code

        print("✓ Migration detects added column")
        print("✓ ALTER TABLE ADD COLUMN statement is correct")
        print("✓ Column type and constraints are correct")


def test_schema_snapshot_save_and_load():
    """Test that schema snapshots can be saved and loaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test schema
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

        # Create snapshot
        snapshot = SchemaSnapshot(schema)

        # Save to file
        snapshot_path = Path(tmpdir) / "test_snapshot.json"
        snapshot.save(snapshot_path)

        assert snapshot_path.exists()

        # Load from file
        loaded_snapshot = SchemaSnapshot.load(snapshot_path)

        # Verify loaded snapshot matches original
        assert "User" in loaded_snapshot.models
        assert "id" in loaded_snapshot.models["User"]["fields"]
        assert "name" in loaded_snapshot.models["User"]["fields"]

        print("✓ Schema snapshot can be saved and loaded correctly")


def test_schema_diff_detects_added_column():
    """Test that SchemaDiff correctly detects added columns."""
    # Create old schema (without email)
    old_schema = SchnitzelSchema(
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

    # Create new schema (with email)
    new_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "email": FieldDefinition(type="string", optional=True),
                },
            )
        }
    )

    # Create snapshots and diff
    old_snapshot = SchemaSnapshot(old_schema)
    new_snapshot = SchemaSnapshot(new_schema)
    diff = SchemaDiff(old_snapshot, new_snapshot)

    # Verify diff detects added column
    assert not diff.is_empty()
    assert "User" in diff.added_columns
    assert "email" in diff.added_columns["User"]

    # Verify no other changes
    assert not diff.added_models
    assert not diff.removed_models
    assert not diff.removed_columns

    print("✓ SchemaDiff detects added column correctly")


def test_schema_diff_detects_removed_column():
    """Test that SchemaDiff correctly detects removed columns."""
    # Create old schema (with email)
    old_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "email": FieldDefinition(type="string", optional=True),
                },
            )
        }
    )

    # Create new schema (without email)
    new_schema = SchnitzelSchema(
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

    # Create snapshots and diff
    old_snapshot = SchemaSnapshot(old_schema)
    new_snapshot = SchemaSnapshot(new_schema)
    diff = SchemaDiff(old_snapshot, new_snapshot)

    # Verify diff detects removed column
    assert not diff.is_empty()
    assert "User" in diff.removed_columns
    assert "email" in diff.removed_columns["User"]

    # Verify no other changes
    assert not diff.added_models
    assert not diff.removed_models
    assert not diff.added_columns

    print("✓ SchemaDiff detects removed column correctly")


def test_multiple_columns_added():
    """Test that migration handles multiple columns added at once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Add multiple columns
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="add_user_fields",
        )

        # Verify all columns are added
        assert migration_code.count("op.add_column('users'") == 3
        assert "sa.Column('name'" in migration_code
        assert "sa.Column('email'" in migration_code
        assert "sa.Column('age'" in migration_code

        # Verify all columns are dropped in downgrade
        assert migration_code.count("op.drop_column('users'") == 3

        print("✓ Migration handles multiple columns added simultaneously")


def test_no_changes_raises_error():
    """Test that generating a diff migration with no changes raises an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create schema
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(schema, "initial")

        # Try to generate migration with same schema (no changes)
        with pytest.raises(ValueError, match="No schema changes detected"):
            generator.generate_diff_migration(
                schema=schema,
                migration_name="no_changes",
            )

        print("✓ Raises error when no changes detected")


def test_column_type_constraints():
    """Test that different column types and constraints are correctly generated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Add various field types
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "email": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "is_active": FieldDefinition(type="bool", required=False, optional=True),
                        "balance": FieldDefinition(type="float", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="add_fields",
        )

        # Verify types
        assert "sa.Column('email', sa.String(), nullable=False)" in migration_code
        assert "sa.Column('age', sa.Integer(), nullable=True)" in migration_code
        assert "sa.Column('is_active', sa.Boolean(), nullable=True)" in migration_code
        assert "sa.Column('balance', sa.Float(), nullable=True)" in migration_code

        print("✓ Column types and constraints are correctly generated")


def test_migration_file_structure():
    """Test that generated migration file has correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "email": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="add_email",
        )

        # Verify file structure
        assert '"""add_email' in migration_code
        assert "Revision ID:" in migration_code
        assert "Revises:" in migration_code
        assert "Create Date:" in migration_code

        # Verify imports
        assert "from alembic import op" in migration_code
        assert "import sqlalchemy as sa" in migration_code

        # Verify revision variables
        assert "revision =" in migration_code
        assert "down_revision =" in migration_code
        assert "branch_labels = None" in migration_code
        assert "depends_on = None" in migration_code

        # Verify functions
        assert "def upgrade() -> None:" in migration_code
        assert "def downgrade() -> None:" in migration_code

        print("✓ Migration file has correct Alembic structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
