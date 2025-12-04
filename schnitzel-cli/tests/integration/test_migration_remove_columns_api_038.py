"""Test for api_038: Database migration generator detects removed columns.

This test verifies:
1. Create initial schema with multiple columns
2. Remove columns from the schema
3. Generate diff migration
4. Verify migration contains DROP COLUMN in upgrade
5. Verify migration contains ADD COLUMN in downgrade (for rollback)
6. Verify column types are preserved in downgrade
"""

import tempfile
from pathlib import Path

import pytest

from schnitzel.generators.infra.migrations import (
    AlembicMigrationGenerator,
    SchemaSnapshot,
    SchemaDiff,
)
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


def test_detect_removed_single_column():
    """Test that migration generator detects and generates DROP COLUMN for single removed column."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Step 1: Create initial schema with User model (id, name, email, age)
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="Application user",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
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
        assert "sa.Column('email', sa.String()" in initial_migration
        assert "sa.Column('age', sa.Integer()" in initial_migration

        # Save initial snapshot
        snapshot_path = generator.save_snapshot(initial_schema, "create_users_table")
        assert snapshot_path.exists()

        # Step 2: Remove email field from User model
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="Application user",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="int", optional=True),
                    },
                )
            }
        )

        # Step 3: Generate diff migration
        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_email",
        )

        # Step 4: Verify migration contains DROP COLUMN in upgrade
        assert "def upgrade() -> None:" in migration_code
        assert "op.drop_column('users', 'email')" in migration_code

        # Step 5: Verify migration contains ADD COLUMN in downgrade (for rollback)
        assert "def downgrade() -> None:" in migration_code
        assert "op.add_column('users'" in migration_code

        # Step 6: Verify column type is preserved in downgrade
        assert "sa.Column('email', sa.String()" in migration_code
        assert "nullable=True" in migration_code

        print("✓ Migration detects removed column")
        print("✓ DROP COLUMN statement is correct in upgrade")
        print("✓ ADD COLUMN statement is correct in downgrade")
        print("✓ Column type is preserved for rollback")


def test_detect_removed_multiple_columns():
    """Test that migration generator handles multiple columns removed at once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema with multiple columns
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "bio": FieldDefinition(type="text", optional=True),
                        "active": FieldDefinition(type="bool", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Remove multiple columns (email, age, bio)
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "active": FieldDefinition(type="bool", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_user_fields",
        )

        # Verify all columns are dropped in upgrade
        assert migration_code.count("op.drop_column('users'") == 3
        assert "op.drop_column('users', 'email')" in migration_code
        assert "op.drop_column('users', 'age')" in migration_code
        assert "op.drop_column('users', 'bio')" in migration_code

        # Verify all columns are added back in downgrade
        assert migration_code.count("op.add_column('users'") == 3
        assert "sa.Column('email', sa.String()" in migration_code
        assert "sa.Column('age', sa.Integer()" in migration_code
        assert "sa.Column('bio', sa.Text()" in migration_code

        print("✓ Migration handles multiple removed columns")
        print("✓ All DROP COLUMN statements are generated")
        print("✓ All ADD COLUMN statements are generated for rollback")


def test_schema_diff_detects_removed_columns():
    """Test that SchemaDiff correctly detects removed columns."""
    # Create old schema (with email and age)
    old_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "email": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                },
            )
        }
    )

    # Create new schema (without email and age)
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

    # Verify diff detects removed columns
    assert not diff.is_empty()
    assert "User" in diff.removed_columns
    assert "email" in diff.removed_columns["User"]
    assert "age" in diff.removed_columns["User"]
    assert len(diff.removed_columns["User"]) == 2

    # Verify no other changes
    assert not diff.added_models
    assert not diff.removed_models
    assert not diff.added_columns

    print("✓ SchemaDiff detects removed columns correctly")
    print("✓ Multiple removed columns are tracked")


def test_removed_column_types_preserved():
    """Test that different column types are correctly preserved in downgrade migration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema with various field types
        initial_schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "description": FieldDefinition(type="text", optional=True),
                        "price": FieldDefinition(type="float", required=True),
                        "stock": FieldDefinition(type="int", optional=True),
                        "active": FieldDefinition(type="bool", required=True),
                        "created_at": FieldDefinition(type="datetime", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Remove various typed columns
        updated_schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_product_fields",
        )

        # Verify upgrade drops columns
        assert "op.drop_column('products', 'description')" in migration_code
        assert "op.drop_column('products', 'price')" in migration_code
        assert "op.drop_column('products', 'stock')" in migration_code
        assert "op.drop_column('products', 'active')" in migration_code
        assert "op.drop_column('products', 'created_at')" in migration_code

        # Verify downgrade preserves correct types
        assert "sa.Column('description', sa.Text()" in migration_code
        assert "sa.Column('price', sa.Float()" in migration_code
        assert "sa.Column('stock', sa.Integer()" in migration_code
        assert "sa.Column('active', sa.Boolean()" in migration_code
        assert "sa.Column('created_at', sa.DateTime()" in migration_code

        print("✓ Column types are correctly preserved in downgrade")
        print("✓ Text, Float, Integer, Boolean, and DateTime types handled")


def test_removed_required_column_nullable_in_downgrade():
    """Test that required columns are correctly marked as non-nullable in downgrade."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema with required and optional fields
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", required=True),
                        "bio": FieldDefinition(type="text", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Remove both required and optional fields
        updated_schema = SchnitzelSchema(
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

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_fields",
        )

        # Verify upgrade drops both columns
        assert "op.drop_column('users', 'email')" in migration_code
        assert "op.drop_column('users', 'bio')" in migration_code

        # Verify downgrade preserves nullable constraints
        # Email was required (nullable=False), bio was optional (nullable=True)
        assert "sa.Column('email', sa.String(), nullable=False)" in migration_code
        assert "sa.Column('bio', sa.Text(), nullable=True)" in migration_code

        print("✓ Nullable constraints are correctly preserved in downgrade")
        print("✓ Required fields restore as nullable=False")
        print("✓ Optional fields restore as nullable=True")


def test_removed_column_from_multiple_models():
    """Test that columns can be removed from multiple models in one migration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema with multiple models
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "title": FieldDefinition(type="string", required=True),
                        "subtitle": FieldDefinition(type="string", optional=True),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Remove columns from both models
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                ),
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_optional_fields",
        )

        # Verify columns from both tables are dropped
        assert "op.drop_column('users', 'email')" in migration_code
        assert "op.drop_column('posts', 'subtitle')" in migration_code

        # Verify downgrade adds columns back to both tables
        assert "op.add_column('users'" in migration_code
        assert "op.add_column('posts'" in migration_code
        assert "sa.Column('email', sa.String()" in migration_code
        assert "sa.Column('subtitle', sa.String()" in migration_code

        print("✓ Migration handles removed columns from multiple models")
        print("✓ Both tables have DROP COLUMN in upgrade")
        print("✓ Both tables have ADD COLUMN in downgrade")


def test_combined_add_and_remove_columns():
    """Test migration when some columns are added and others are removed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema
        initial_schema = SchnitzelSchema(
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

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Remove email, add phone, keep name and age
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="int", optional=True),
                        "phone": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="update_user_fields",
        )

        # Verify upgrade: add phone, drop email
        assert "op.add_column('users'" in migration_code
        assert "sa.Column('phone', sa.String()" in migration_code
        assert "op.drop_column('users', 'email')" in migration_code

        # Verify downgrade: drop phone, add email back
        assert "op.drop_column('users', 'phone')" in migration_code
        assert "sa.Column('email', sa.String()" in migration_code

        print("✓ Migration handles both added and removed columns")
        print("✓ Upgrade adds new column and drops old column")
        print("✓ Downgrade reverses both operations")


def test_migration_file_structure_for_removed_columns():
    """Test that migration file has correct Alembic structure for removed columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
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
                        "name": FieldDefinition(type="string", required=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_email",
        )

        # Verify file structure
        assert '"""remove_email' in migration_code
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

        # Verify operations are in correct functions
        upgrade_section = migration_code.split("def downgrade()")[0]
        downgrade_section = migration_code.split("def downgrade()")[1]

        assert "op.drop_column('users', 'email')" in upgrade_section
        assert "op.add_column('users'" in downgrade_section

        print("✓ Migration file has correct Alembic structure")
        print("✓ DROP COLUMN is in upgrade function")
        print("✓ ADD COLUMN is in downgrade function")


def test_no_error_when_only_removing_columns():
    """Test that migration can be generated when only removing columns (no additions)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "email": FieldDefinition(type="string", optional=True),
                        "phone": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Remove multiple columns, don't add any
        updated_schema = SchnitzelSchema(
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

        # Should not raise error
        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="remove_contact_fields",
        )

        # Verify migration is valid
        assert "def upgrade() -> None:" in migration_code
        assert "def downgrade() -> None:" in migration_code
        assert "op.drop_column('users', 'email')" in migration_code
        assert "op.drop_column('users', 'phone')" in migration_code

        print("✓ Migration generated successfully with only removed columns")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
