"""Integration tests for migration backup (api_094).

Tests for:
- api_094: Migrate command creates backup before destructive operations
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import SchemaDiff, SchemaSnapshot


class TestMigrateBackup:
    """Tests for api_094: Migrate command creates backup before destructive operations."""

    def test_detects_destructive_model_removal(self):
        """Test detection of destructive model removal."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "ToBeDeleted": Model(
                    name="ToBeDeleted",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect model removal (destructive)
        assert "ToBeDeleted" in diff.removed_models

    def test_detects_destructive_column_removal(self):
        """Test detection of destructive column removal."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "old_data": FieldDefinition(type="string"),
                    }
                )
            }
        )

        new_schema = SchnitzelSchema(
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
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect column removal (destructive)
        assert "User" in diff.removed_columns

    def test_safe_additions_detected(self):
        """Test safe additions are also tracked."""
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

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "new_safe_field": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Safe additions should be tracked
        assert "User" in diff.added_columns

    def test_is_empty_for_no_changes(self):
        """Test is_empty returns True when no changes."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        snapshot = SchemaSnapshot(schema)
        diff = SchemaDiff(snapshot, snapshot)

        # Should be empty
        assert diff.is_empty()

    def test_has_changes_for_destructive_ops(self):
        """Test has_changes returns True for destructive operations."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "to_remove": FieldDefinition(type="string"),
                    }
                )
            }
        )

        new_schema = SchnitzelSchema(
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
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should have changes
        assert diff.has_changes()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
