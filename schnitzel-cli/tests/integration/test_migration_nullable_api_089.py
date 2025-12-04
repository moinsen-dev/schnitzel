"""Integration tests for migration nullable changes (api_089).

Tests for:
- api_089: Database migration generator handles nullable changes
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import (
    AlembicMigrationGenerator,
    SchemaSnapshot,
    SchemaDiff,
)


class TestNullableChanges:
    """Tests for api_089: Database migration generator handles nullable changes."""

    def test_detect_nullable_to_non_nullable(self):
        """Test detecting change from nullable to non-nullable."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string", optional=True),
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
                        "bio": FieldDefinition(type="string", optional=False),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect nullable change
        assert "User" in diff.nullable_changes
        assert "bio" in diff.nullable_changes["User"]
        assert diff.nullable_changes["User"]["bio"]["old"] == True
        assert diff.nullable_changes["User"]["bio"]["new"] == False

    def test_detect_non_nullable_to_nullable(self):
        """Test detecting change from non-nullable to nullable."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string", optional=False, required=True),
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
                        "email": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        assert "User" in diff.nullable_changes
        assert "email" in diff.nullable_changes["User"]
        assert diff.nullable_changes["User"]["email"]["old"] == False
        assert diff.nullable_changes["User"]["email"]["new"] == True

    def test_generate_alter_column_nullable(self):
        """Test that alter_column with nullable is generated."""
        old_schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "description": FieldDefinition(type="text", optional=True),
                    }
                )
            }
        )
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "description": FieldDefinition(type="text", optional=False, required=True),
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)
        generator = AlembicMigrationGenerator()

        upgrade_ops = generator._generate_diff_upgrade_operations(diff)
        downgrade_ops = generator._generate_diff_downgrade_operations(diff)

        # Check upgrade changes nullable
        nullable_change_found = False
        for op in upgrade_ops:
            if "alter_column" in op and "'description'" in op and "nullable=False" in op:
                nullable_change_found = True
                break
        assert nullable_change_found, f"Expected nullable=False in: {upgrade_ops}"

        # Check downgrade reverses
        reverse_found = False
        for op in downgrade_ops:
            if "alter_column" in op and "'description'" in op and "nullable=True" in op:
                reverse_found = True
                break
        assert reverse_found, f"Expected nullable=True in: {downgrade_ops}"

    def test_nullable_change_separate_from_type_change(self):
        """Test that nullable-only changes don't require type change."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "nickname": FieldDefinition(type="string", optional=True),
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
                        "nickname": FieldDefinition(type="string", optional=False),  # Same type, diff nullable
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should be in nullable_changes, NOT in changed_columns (type didn't change)
        assert "User" in diff.nullable_changes
        assert "nickname" in diff.nullable_changes["User"]
        # Type didn't change, so shouldn't be in changed_columns
        assert "User" not in diff.changed_columns or "nickname" not in diff.changed_columns.get("User", {})

    def test_multiple_nullable_changes(self):
        """Test handling multiple nullable changes."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "field1": FieldDefinition(type="string", optional=True),
                        "field2": FieldDefinition(type="string", optional=False),
                        "field3": FieldDefinition(type="string", optional=True),
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
                        "field1": FieldDefinition(type="string", optional=False),  # Changed
                        "field2": FieldDefinition(type="string", optional=True),   # Changed
                        "field3": FieldDefinition(type="string", optional=True),   # Not changed
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        assert "User" in diff.nullable_changes
        assert "field1" in diff.nullable_changes["User"]
        assert "field2" in diff.nullable_changes["User"]
        assert "field3" not in diff.nullable_changes.get("User", {})

    def test_no_change_when_nullable_same(self):
        """Test no change detected when nullable stays the same."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", optional=True),
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
                        "name": FieldDefinition(type="string", optional=True),  # Same
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        assert "User" not in diff.nullable_changes or len(diff.nullable_changes.get("User", {})) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
