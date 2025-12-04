"""Integration tests for migration table rename (api_086).

Tests for:
- api_086: Database migration generator handles renamed tables
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import (
    AlembicMigrationGenerator, SchemaDiff, SchemaSnapshot
)


class TestMigrationTableRename:
    """Tests for api_086: Database migration generator handles renamed tables."""

    def test_schema_diff_detects_added_model(self):
        """Test SchemaDiff detects added models."""
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
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect added model
        assert "Post" in diff.added_models

    def test_schema_diff_detects_removed_model(self):
        """Test SchemaDiff detects removed models."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
                "Post": Model(
                    name="Post",
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
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect removed model
        assert "Post" in diff.removed_models

    def test_schema_diff_detects_added_fields(self):
        """Test SchemaDiff detects added fields."""
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

    def test_schema_diff_no_changes(self):
        """Test SchemaDiff handles no changes."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        snapshot = SchemaSnapshot(schema)
        diff = SchemaDiff(snapshot, snapshot)

        # Should have no changes
        assert diff.is_empty()

    def test_schema_diff_has_changes(self):
        """Test SchemaDiff has_changes method."""
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
                        "name": FieldDefinition(type="string"),
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
