"""Integration tests for migration rename functionality (api_086, api_087).

Tests for:
- api_086: Database migration generator handles renamed tables
- api_087: Database migration generator handles renamed columns
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import (
    AlembicMigrationGenerator,
    SchemaSnapshot,
    SchemaDiff,
)


class TestTableRename:
    """Tests for api_086: Database migration generator handles renamed tables."""

    def test_detect_renamed_table_with_hint(self):
        """Test that renamed tables are detected when hints are provided."""
        # Create old schema with "User" model
        old_schema = SchnitzelSchema(
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
        old_snapshot = SchemaSnapshot(old_schema)

        # Create new schema with "Account" model (renamed from User)
        new_schema = SchnitzelSchema(
            models={
                "Account": Model(
                    name="Account",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        # Provide rename hint
        rename_hints = {"tables": {"User": "Account"}}
        diff = SchemaDiff(old_snapshot, new_snapshot, rename_hints=rename_hints)

        # Should detect the rename
        assert "User" in diff.renamed_tables
        assert diff.renamed_tables["User"] == "Account"

        # Should NOT be in added/removed
        assert "Account" not in diff.added_models
        assert "User" not in diff.removed_models

    def test_generate_rename_table_migration(self):
        """Test that rename_table operation is generated."""
        old_schema = SchnitzelSchema(
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
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
            models={
                "Account": Model(
                    name="Account",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        rename_hints = {"tables": {"User": "Account"}}
        diff = SchemaDiff(old_snapshot, new_snapshot, rename_hints=rename_hints)

        generator = AlembicMigrationGenerator()
        upgrade_ops = generator._generate_diff_upgrade_operations(diff)
        downgrade_ops = generator._generate_diff_downgrade_operations(diff)

        # Check upgrade has rename_table
        rename_found = False
        for op in upgrade_ops:
            if "rename_table" in op and "'users'" in op and "'accounts'" in op:
                rename_found = True
                break
        assert rename_found, f"Expected rename_table operation in: {upgrade_ops}"

        # Check downgrade reverses it
        reverse_found = False
        for op in downgrade_ops:
            if "rename_table" in op and "'accounts'" in op and "'users'" in op:
                reverse_found = True
                break
        assert reverse_found, f"Expected reverse rename_table in: {downgrade_ops}"

    def test_without_hint_treated_as_add_remove(self):
        """Test that without hints, rename is treated as add+remove."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
            models={
                "Account": Model(
                    name="Account",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        # No hints provided
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should be treated as add + remove
        assert "Account" in diff.added_models
        assert "User" in diff.removed_models
        assert len(diff.renamed_tables) == 0


class TestColumnRename:
    """Tests for api_087: Database migration generator handles renamed columns."""

    def test_detect_renamed_column_with_hint(self):
        """Test that renamed columns are detected when hints are provided."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
                    }
                )
            }
        )
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "user_name": FieldDefinition(type="string"),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        rename_hints = {"columns": {"User": {"username": "user_name"}}}
        diff = SchemaDiff(old_snapshot, new_snapshot, rename_hints=rename_hints)

        # Should detect the rename
        assert "User" in diff.renamed_columns
        assert diff.renamed_columns["User"]["username"] == "user_name"

        # Should NOT be in added/removed columns
        assert "User" not in diff.added_columns or "user_name" not in diff.added_columns.get("User", {})
        assert "User" not in diff.removed_columns or "username" not in diff.removed_columns.get("User", {})

    def test_generate_rename_column_migration(self):
        """Test that alter_column with new_column_name is generated."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email_addr": FieldDefinition(type="string"),
                    }
                )
            }
        )
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
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
        new_snapshot = SchemaSnapshot(new_schema)

        rename_hints = {"columns": {"User": {"email_addr": "email"}}}
        diff = SchemaDiff(old_snapshot, new_snapshot, rename_hints=rename_hints)

        generator = AlembicMigrationGenerator()
        upgrade_ops = generator._generate_diff_upgrade_operations(diff)
        downgrade_ops = generator._generate_diff_downgrade_operations(diff)

        # Check upgrade has alter_column with new_column_name
        rename_found = False
        for op in upgrade_ops:
            if "alter_column" in op and "new_column_name='email'" in op and "'email_addr'" in op:
                rename_found = True
                break
        assert rename_found, f"Expected column rename in: {upgrade_ops}"

        # Check downgrade reverses it
        reverse_found = False
        for op in downgrade_ops:
            if "alter_column" in op and "new_column_name='email_addr'" in op and "'email'" in op:
                reverse_found = True
                break
        assert reverse_found, f"Expected reverse column rename in: {downgrade_ops}"

    def test_multiple_column_renames(self):
        """Test handling multiple column renames in same table."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "first": FieldDefinition(type="string"),
                        "last": FieldDefinition(type="string"),
                    }
                )
            }
        )
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "first_name": FieldDefinition(type="string"),
                        "last_name": FieldDefinition(type="string"),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        rename_hints = {
            "columns": {
                "User": {
                    "first": "first_name",
                    "last": "last_name"
                }
            }
        }
        diff = SchemaDiff(old_snapshot, new_snapshot, rename_hints=rename_hints)

        assert len(diff.renamed_columns.get("User", {})) == 2
        assert diff.renamed_columns["User"]["first"] == "first_name"
        assert diff.renamed_columns["User"]["last"] == "last_name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
