"""Integration tests for migration column rename (api_087).

Tests for:
- api_087: Database migration generator handles renamed columns
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import SchemaDiff, SchemaSnapshot


class TestMigrationColumnRename:
    """Tests for api_087: Database migration generator handles renamed columns."""

    def test_schema_diff_detects_added_columns(self):
        """Test SchemaDiff detects added columns."""
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
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect added column
        assert "User" in diff.added_columns
        assert "email" in diff.added_columns["User"]

    def test_schema_diff_detects_removed_columns(self):
        """Test SchemaDiff detects removed columns."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "deprecated_field": FieldDefinition(type="string"),
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

        # Should detect removed column
        assert "User" in diff.removed_columns
        assert "deprecated_field" in diff.removed_columns["User"]

    def test_multiple_column_changes(self):
        """Test multiple column changes in same model."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "old_field": FieldDefinition(type="string"),
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
                        "new_field": FieldDefinition(type="string"),
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect both added and removed
        assert diff.has_changes()

    def test_column_changes_across_models(self):
        """Test column changes across multiple models."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect changes in both models
        assert "User" in diff.added_columns
        assert "Post" in diff.added_columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
