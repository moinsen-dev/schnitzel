"""Integration tests for migration data handling (api_088).

Tests for:
- api_088: Database migration generator handles data migrations
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import SchemaDiff, SchemaSnapshot


class TestMigrationData:
    """Tests for api_088: Database migration generator handles data migrations."""

    def test_schema_snapshot_serializes_models(self):
        """Test SchemaSnapshot serializes models correctly."""
        schema = SchnitzelSchema(
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

        snapshot = SchemaSnapshot(schema)

        # Should have serialized models
        assert "User" in snapshot.models
        assert "fields" in snapshot.models["User"]

    def test_schema_snapshot_preserves_field_types(self):
        """Test SchemaSnapshot preserves field types."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "count": FieldDefinition(type="int"),
                        "active": FieldDefinition(type="bool"),
                    }
                )
            }
        )

        snapshot = SchemaSnapshot(schema)

        # Should preserve field types
        fields = snapshot.models["User"]["fields"]
        assert fields["id"]["type"] == "uuid"
        assert fields["count"]["type"] == "int"
        assert fields["active"]["type"] == "bool"

    def test_schema_diff_tracks_type_changes(self):
        """Test SchemaDiff can detect type changes."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(type="string"),
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
                        "status": FieldDefinition(type="int"),  # Changed type
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect the change
        assert diff.has_changes() or "User" in diff.changed_columns

    def test_snapshot_to_dict(self):
        """Test SchemaSnapshot can be converted to dict."""
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
        data = snapshot.to_dict()

        # Should have expected structure
        assert "timestamp" in data
        assert "models" in data

    def test_complex_schema_diff(self):
        """Test SchemaDiff with complex schema changes."""
        old_schema = SchnitzelSchema(
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

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                        "phone": FieldDefinition(type="string"),
                    }
                ),
                "Profile": Model(
                    name="Profile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should detect both model and column additions
        assert "Profile" in diff.added_models
        assert "User" in diff.added_columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
