"""Integration tests for migration data handling (api_088).

Tests for:
- api_088: Database migration generator handles data migrations
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import (
    SchemaDiff,
    SchemaSnapshot,
    AlembicMigrationGenerator,
)


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

    def test_data_migration_for_new_column_with_default(self):
        """Test that adding a non-nullable column with default generates data migration."""
        generator = AlembicMigrationGenerator()

        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
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
                        "status": FieldDefinition(
                            type="string", default="active", required=True
                        ),
                    },
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Generate upgrade operations
        upgrade_ops = generator._generate_diff_upgrade_operations(diff)
        migration_code = "\n".join(upgrade_ops)

        # Should contain ADD COLUMN
        assert "op.add_column" in migration_code
        assert "status" in migration_code

        # Should contain data migration UPDATE statement
        assert "op.execute" in migration_code
        assert "UPDATE" in migration_code.upper()
        assert "SET status = 'active'" in migration_code

    def test_data_migration_generator_insert_operation(self):
        """Test generate_data_migration with INSERT operation."""
        generator = AlembicMigrationGenerator()

        data_operations = [
            {
                "operation": "insert",
                "values": {"name": "admin", "role": "superuser"},
            }
        ]

        migration_code = generator.generate_data_migration(
            migration_name="add_admin_user",
            table_name="users",
            data_operations=data_operations,
        )

        # Should contain INSERT statement in upgrade
        assert "INSERT INTO users" in migration_code
        assert "admin" in migration_code
        assert "superuser" in migration_code

        # Should contain DELETE statement in downgrade
        assert "DELETE FROM users" in migration_code

    def test_data_migration_generator_update_operation(self):
        """Test generate_data_migration with UPDATE operation."""
        generator = AlembicMigrationGenerator()

        data_operations = [
            {
                "operation": "update",
                "values": {"status": "active"},
                "where": "status IS NULL",
            }
        ]

        migration_code = generator.generate_data_migration(
            migration_name="populate_status",
            table_name="users",
            data_operations=data_operations,
        )

        # Should contain UPDATE statement in upgrade
        assert "UPDATE users" in migration_code
        assert "SET status = 'active'" in migration_code
        assert "WHERE status IS NULL" in migration_code

        # Should have comment about manual intervention in downgrade
        assert "Manual intervention required" in migration_code

    def test_format_default_value_for_sql(self):
        """Test _format_default_value_for_sql handles different types correctly."""
        generator = AlembicMigrationGenerator()

        # Test string
        assert generator._format_default_value_for_sql("active", "string") == "'active'"

        # Test integer
        assert generator._format_default_value_for_sql(42, "int") == "42"

        # Test boolean
        assert generator._format_default_value_for_sql(True, "bool") == "TRUE"
        assert generator._format_default_value_for_sql(False, "bool") == "FALSE"

        # Test NULL
        assert generator._format_default_value_for_sql(None, "string") == "NULL"

        # Test string with quotes (SQL injection protection)
        assert (
            generator._format_default_value_for_sql("it's", "string") == "'it''s'"
        )

    def test_type_change_generates_warning_comment(self):
        """Test that type changes generate warning comments about data transformation."""
        generator = AlembicMigrationGenerator()

        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "age": FieldDefinition(type="string"),
                    },
                )
            }
        )

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "age": FieldDefinition(type="int"),  # Changed from string to int
                    },
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Generate upgrade operations
        upgrade_ops = generator._generate_diff_upgrade_operations(diff)
        migration_code = "\n".join(upgrade_ops)

        # Should contain warning comment
        assert "Type change" in migration_code
        assert "WARNING" in migration_code
        assert "data transformation" in migration_code

    def test_default_value_changes_tracked(self):
        """Test that default value changes are tracked in SchemaDiff."""
        old_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(type="string", default="user"),
                    },
                )
            }
        )

        new_schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="string", default="member"
                        ),  # Changed default
                    },
                )
            }
        )

        old_snapshot = SchemaSnapshot(old_schema)
        new_snapshot = SchemaSnapshot(new_schema)
        diff = SchemaDiff(old_snapshot, new_snapshot)

        # Should track default value changes
        assert "User" in diff.default_changes
        assert "role" in diff.default_changes["User"]
        assert diff.default_changes["User"]["role"]["old"] == "user"
        assert diff.default_changes["User"]["role"]["new"] == "member"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
