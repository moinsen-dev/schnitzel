"""Integration tests for migration no changes detection (api_156).

Tests for:
- api_156: Unit test: Migration generator detects no changes correctly
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import SchemaDiff, SchemaSnapshot


class TestMigrationNoChanges:
    """Tests for api_156: Migration no changes detection."""

    def test_detects_no_changes_same_schema(self):
        """Test detects no changes when comparing same schema."""
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
        assert diff.is_empty()

    def test_detects_changes_when_modified(self):
        """Test detects changes when schema is modified."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
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
                        "name": FieldDefinition(type="string")
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)
        assert not diff.is_empty()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
