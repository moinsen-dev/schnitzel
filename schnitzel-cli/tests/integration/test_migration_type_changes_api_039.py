"""Test for api_039: Database migration generator detects column type changes.

This test verifies:
1. Create initial schema with columns of type A
2. Create modified schema with columns changed to type B
3. Generate diff migration
4. Verify type change is detected
5. Verify ALTER COLUMN TYPE statements are generated
6. Verify downgrade reverts the type change
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


def test_detect_column_type_change():
    """Test that migration generator detects and generates ALTER COLUMN TYPE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Step 1: Create initial schema with User model (age: int)
        initial_schema = SchnitzelSchema(
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

        # Initialize migration generator
        generator = AlembicMigrationGenerator(project_root=project_root)

        # Generate initial migration
        initial_migration = generator.generate_initial_migration(
            schema=initial_schema,
            migration_name="create_users_table",
        )

        # Verify initial migration is created correctly
        assert "op.create_table('users'," in initial_migration
        assert "sa.Column('age', sa.Integer()" in initial_migration

        # Save initial snapshot
        snapshot_path = generator.save_snapshot(initial_schema, "create_users_table")
        assert snapshot_path.exists()

        # Step 2: Change age field from int to string
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="Application user",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        # Step 3: Generate diff migration
        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="change_age_to_string",
        )

        # Step 4: Verify type change is detected
        assert "def upgrade() -> None:" in migration_code
        assert "def downgrade() -> None:" in migration_code

        # Step 5: Verify ALTER COLUMN TYPE statement is generated
        assert "op.alter_column('users', 'age'" in migration_code
        assert "type_=sa.String()" in migration_code

        # Step 6: Verify downgrade reverts the type change
        # The downgrade should change it back to Integer
        lines = migration_code.split('\n')
        in_downgrade = False
        found_revert = False
        for line in lines:
            if "def downgrade() -> None:" in line:
                in_downgrade = True
            if in_downgrade and "op.alter_column('users', 'age'" in line:
                # Check the next line or same line for type_=sa.Integer()
                if "type_=sa.Integer()" in line:
                    found_revert = True

        assert found_revert, "Downgrade should revert type back to Integer"

        print("✓ Migration detects column type change")
        print("✓ ALTER COLUMN TYPE statement is correct")
        print("✓ Downgrade reverts the type change")


def test_schema_diff_detects_type_change():
    """Test that SchemaDiff correctly detects column type changes."""
    # Create old schema (age: int)
    old_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "age": FieldDefinition(type="int", optional=True),
                },
            )
        }
    )

    # Create new schema (age: string)
    new_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "age": FieldDefinition(type="string", optional=True),
                },
            )
        }
    )

    # Create snapshots and diff
    old_snapshot = SchemaSnapshot(old_schema)
    new_snapshot = SchemaSnapshot(new_schema)
    diff = SchemaDiff(old_snapshot, new_snapshot)

    # Verify diff detects changed column
    assert not diff.is_empty()
    assert "User" in diff.changed_columns
    assert "age" in diff.changed_columns["User"]

    # Verify old and new types are tracked
    assert diff.changed_columns["User"]["age"]["old"]["type"] == "int"
    assert diff.changed_columns["User"]["age"]["new"]["type"] == "string"

    # Verify no other changes
    assert not diff.added_models
    assert not diff.removed_models
    assert not diff.added_columns
    assert not diff.removed_columns

    print("✓ SchemaDiff detects column type change correctly")


def test_multiple_type_changes():
    """Test that migration handles multiple column type changes at once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema
        initial_schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "price": FieldDefinition(type="int", required=True),
                        "quantity": FieldDefinition(type="int", required=True),
                        "is_active": FieldDefinition(type="bool", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Change multiple column types
        updated_schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "price": FieldDefinition(type="float", required=True),
                        "quantity": FieldDefinition(type="string", required=True),
                        "is_active": FieldDefinition(type="int", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="change_product_types",
        )

        # Verify all type changes are detected
        # Count should be 6: 3 in upgrade + 3 in downgrade
        assert migration_code.count("op.alter_column('products'") == 6

        # Check upgrade section has the new types
        upgrade_section = migration_code.split("def downgrade()")[0]
        assert "type_=sa.Float()" in upgrade_section
        assert "type_=sa.String()" in upgrade_section
        assert upgrade_section.count("type_=sa.Integer()") == 1  # is_active changed to int

        # Check downgrade section has the old types
        downgrade_section = migration_code.split("def downgrade()")[1]
        assert downgrade_section.count("type_=sa.Integer()") == 2  # price and quantity reverted
        assert "type_=sa.Boolean()" in downgrade_section  # is_active reverted

        print("✓ Migration handles multiple type changes simultaneously")


def test_type_change_with_other_changes():
    """Test migration with type changes combined with added/removed columns."""
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
                        "age": FieldDefinition(type="int", optional=True),
                        "old_field": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Change age type, add email, remove old_field
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="string", optional=True),
                        "email": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="mixed_changes",
        )

        # Verify type change
        assert "op.alter_column('users', 'age'" in migration_code
        assert "type_=sa.String()" in migration_code

        # Verify column addition
        assert "op.add_column('users'" in migration_code
        assert "sa.Column('email'" in migration_code

        # Verify column removal
        assert "op.drop_column('users', 'old_field')" in migration_code

        print("✓ Migration handles mixed changes (type change + add + remove)")


def test_no_type_change_no_migration():
    """Test that no migration is generated when types don't change."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "name": FieldDefinition(type="string", required=True),
                        "age": FieldDefinition(type="int", optional=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(schema, "initial")

        # Same schema, no changes
        with pytest.raises(ValueError, match="No schema changes detected"):
            generator.generate_diff_migration(
                schema=schema,
                migration_name="no_changes",
            )

        print("✓ No migration generated when types don't change")


def test_type_change_different_types():
    """Test various type change scenarios."""
    test_cases = [
        ("int", "string", "sa.Integer()", "sa.String()"),
        ("string", "text", "sa.String()", "sa.Text()"),
        ("int", "float", "sa.Integer()", "sa.Float()"),
        ("bool", "string", "sa.Boolean()", "sa.String()"),
        ("string", "uuid", "sa.String()", "sa.UUID()"),
        ("int", "bool", "sa.Integer()", "sa.Boolean()"),
    ]

    for old_type, new_type, old_sa_type, new_sa_type in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initial schema
            initial_schema = SchnitzelSchema(
                models={
                    "Test": Model(
                        name="Test",
                        fields={
                            "id": FieldDefinition(type="uuid", primary=True, required=True),
                            "field": FieldDefinition(type=old_type, optional=True),
                        },
                    )
                }
            )

            generator = AlembicMigrationGenerator(project_root=project_root)
            generator.save_snapshot(initial_schema, "initial")

            # Change type
            updated_schema = SchnitzelSchema(
                models={
                    "Test": Model(
                        name="Test",
                        fields={
                            "id": FieldDefinition(type="uuid", primary=True, required=True),
                            "field": FieldDefinition(type=new_type, optional=True),
                        },
                    )
                }
            )

            migration_code = generator.generate_diff_migration(
                schema=updated_schema,
                migration_name=f"change_{old_type}_to_{new_type}",
            )

            # Verify type change
            assert "op.alter_column('tests', 'field'" in migration_code
            assert f"type_={new_sa_type}" in migration_code

            print(f"✓ Type change {old_type} -> {new_type} works correctly")


def test_type_change_preserves_nullable():
    """Test that type changes preserve nullable constraints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema with required field
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "score": FieldDefinition(type="int", required=True),
                    },
                )
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Change type but keep required
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "score": FieldDefinition(type="float", required=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="change_score_type",
        )

        # Verify nullable constraint is preserved
        assert "op.alter_column('users', 'score'" in migration_code
        assert "type_=sa.Float()" in migration_code
        assert "nullable=False" in migration_code

        print("✓ Type change preserves nullable constraints")


def test_migration_file_structure_with_type_change():
    """Test that generated migration file has correct structure with type changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "age": FieldDefinition(type="int", optional=True),
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
                        "age": FieldDefinition(type="string", optional=True),
                    },
                )
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="change_age_type",
        )

        # Verify file structure
        assert '"""change_age_type' in migration_code
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

        print("✓ Migration file with type change has correct Alembic structure")


def test_schema_diff_unchanged_columns():
    """Test that SchemaDiff doesn't flag unchanged columns as changed."""
    # Create old schema
    old_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "age": FieldDefinition(type="int", optional=True),
                },
            )
        }
    )

    # Create new schema with same types
    new_schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", required=True),
                    "age": FieldDefinition(type="int", optional=True),
                },
            )
        }
    )

    # Create snapshots and diff
    old_snapshot = SchemaSnapshot(old_schema)
    new_snapshot = SchemaSnapshot(new_schema)
    diff = SchemaDiff(old_snapshot, new_snapshot)

    # Verify no changes detected
    assert diff.is_empty()
    assert not diff.changed_columns

    print("✓ SchemaDiff correctly identifies unchanged columns")


def test_type_change_multiple_models():
    """Test type changes across multiple models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Initial schema with multiple models
        initial_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "age": FieldDefinition(type="int", optional=True),
                    },
                ),
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "price": FieldDefinition(type="int", required=True),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator(project_root=project_root)
        generator.save_snapshot(initial_schema, "initial")

        # Change types in both models
        updated_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "age": FieldDefinition(type="string", optional=True),
                    },
                ),
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True, required=True),
                        "price": FieldDefinition(type="float", required=True),
                    },
                ),
            }
        )

        migration_code = generator.generate_diff_migration(
            schema=updated_schema,
            migration_name="change_types_multiple_models",
        )

        # Verify both changes
        assert "op.alter_column('users', 'age'" in migration_code
        assert "op.alter_column('products', 'price'" in migration_code

        print("✓ Type changes detected across multiple models")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
