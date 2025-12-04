"""Integration tests for generate command detecting schema changes (api_139).

Tests for:
- api_139: Generate command detects schema changes and regenerates
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import SchemaSnapshot, SchemaDiff


class TestGenerateDetectChanges:
    """Tests for api_139: Generate command detects schema changes and regenerates."""

    def test_detect_new_model(self):
        """Test detecting addition of new model."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
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
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect new model
        assert "Post" in diff.added_models

    def test_detect_removed_model(self):
        """Test detecting removal of model."""
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
        old_snapshot = SchemaSnapshot(old_schema)

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect removed model
        assert "Post" in diff.removed_models

    def test_detect_new_column(self):
        """Test detecting addition of column."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
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
                        "email": FieldDefinition(type="string")
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect new column
        assert "User" in diff.added_columns
        assert "email" in diff.added_columns["User"]

    def test_detect_no_changes(self):
        """Test detecting when there are no changes."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )
        old_snapshot = SchemaSnapshot(schema)
        new_snapshot = SchemaSnapshot(schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect no changes
        assert diff.is_empty()

    def test_has_changes_method(self):
        """Test has_changes method returns correct value."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
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
                        "name": FieldDefinition(type="string")
                    }
                )
            }
        )
        new_snapshot = SchemaSnapshot(new_schema)

        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should have changes
        assert diff.has_changes()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
