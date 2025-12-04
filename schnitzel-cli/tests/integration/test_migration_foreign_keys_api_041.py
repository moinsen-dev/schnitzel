"""Integration tests for API_041: Database migration generator creates foreign keys.

Test Requirements:
1. Verify migration generator detects relationships (belongsTo)
2. Verify it generates ADD FOREIGN KEY statements
3. Create integration test that:
   - Creates schema with relationships (User has many Posts)
   - Generates migration
   - Verifies FOREIGN KEY constraint is generated
   - Verifies REFERENCES clause points to correct table
"""

import re
import tempfile
from pathlib import Path

import pytest

from schnitzel.generators.infra.migrations import AlembicMigrationGenerator
from schnitzel.schema.models import FieldDefinition, Model, Relation, SchnitzelSchema


class TestMigrationForeignKeyGeneration:
    """Test that migration generator creates foreign key constraints for relationships."""

    def test_belongsto_generates_foreign_key_column(self):
        """Test that belongsTo relationship generates a foreign key column."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    description="A blog post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                        "content": FieldDefinition(type="text", required=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="create_users_and_posts", down_revision=None
        )

        # Verify foreign key column is generated in Post table
        assert "author_id" in migration_code, "Foreign key column 'author_id' should be generated"

        # Verify ForeignKey constraint is present
        assert "sa.ForeignKey(" in migration_code, "ForeignKey constraint should be present"

        # Verify ForeignKey references the correct table and column
        assert "sa.ForeignKey('users.id')" in migration_code, "ForeignKey should reference 'users.id'"

    def test_foreign_key_column_type_matches_primary_key(self):
        """Test that foreign key column type matches the referenced primary key type."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify the foreign key column has UUID type (matching User.id)
        assert "sa.Column('author_id', sa.UUID()," in migration_code, \
            "Foreign key column should have UUID type matching referenced primary key"

    def test_foreign_key_nullable_by_default(self):
        """Test that foreign key columns are nullable by default (optional relationship)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify foreign key column is nullable
        assert "sa.Column('author_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True)" in migration_code, \
            "Foreign key column should be nullable by default"

    def test_custom_foreign_key_name(self):
        """Test that custom foreign_key names are respected in migration."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User",
                            foreign_key="author_id",
                        ),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify custom foreign key name is used
        assert "author_id" in migration_code, "Custom foreign_key name should be used"
        assert "sa.ForeignKey('users.id')" in migration_code

    def test_default_foreign_key_name_generation(self):
        """Test that foreign key name is auto-generated as relation_name + '_id' when not specified."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "createdBy": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify foreign key name is auto-generated from relation name
        # createdBy -> created_by_id (camelCase to snake_case + _id)
        assert "created_by_id" in migration_code, \
            "Foreign key name should be auto-generated as snake_case(relation_name) + '_id'"

    def test_multiple_foreign_keys_in_same_model(self):
        """Test that a model can have multiple foreign key relationships."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Category": Model(
                    name="Category",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                        "category": Relation(type="belongsTo", model="Category"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify both foreign keys are generated
        assert "author_id" in migration_code, "First foreign key should be generated"
        assert "category_id" in migration_code, "Second foreign key should be generated"

        # Verify both ForeignKey constraints reference correct tables
        assert "sa.ForeignKey('users.id')" in migration_code
        assert "sa.ForeignKey('categories.id')" in migration_code

    def test_foreign_key_references_pluralized_table_name(self):
        """Test that foreign key references use pluralized table names."""
        schema = SchnitzelSchema(
            models={
                "Company": Model(
                    name="Company",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Employee": Model(
                    name="Employee",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "company": Relation(type="belongsTo", model="Company"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify ForeignKey references pluralized table name
        # Company -> companies (not companys)
        assert "sa.ForeignKey('companies.id')" in migration_code, \
            "ForeignKey should reference pluralized table name 'companies'"


class TestMigrationTableCreationOrder:
    """Test that tables are created in the correct order to respect foreign key constraints."""

    def test_parent_table_created_before_child_table(self):
        """Test that tables without foreign keys are created before tables with foreign keys."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Find positions of CREATE TABLE statements
        users_pos = migration_code.index("op.create_table('users',")
        posts_pos = migration_code.index("op.create_table('posts',")

        # User table must be created before Post table
        assert users_pos < posts_pos, \
            "Parent table (users) must be created before child table (posts) with foreign key"

    def test_tables_dropped_in_reverse_order(self):
        """Test that tables are dropped in reverse order in downgrade (respecting FK constraints)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Find downgrade function
        downgrade_start = migration_code.index("def downgrade() -> None:")
        downgrade_section = migration_code[downgrade_start:]

        # Find positions of DROP TABLE statements in downgrade section
        posts_drop = downgrade_section.index("op.drop_table('posts')")
        users_drop = downgrade_section.index("op.drop_table('users')")

        # Post table must be dropped before User table (reverse of creation order)
        assert posts_drop < users_drop, \
            "Child table (posts) must be dropped before parent table (users) in downgrade"

    def test_complex_dependency_chain(self):
        """Test table creation order with complex dependency chain."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
                "Comment": Model(
                    name="Comment",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "post": Relation(type="belongsTo", model="Post"),
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Find positions of CREATE TABLE statements
        users_pos = migration_code.index("op.create_table('users',")
        posts_pos = migration_code.index("op.create_table('posts',")
        comments_pos = migration_code.index("op.create_table('comments',")

        # Users must be created first (no dependencies)
        # Posts can be created after Users
        # Comments must be created last (depends on both Users and Posts)
        assert users_pos < posts_pos, "User table must be created before Post table"
        assert posts_pos < comments_pos, "Post table must be created before Comment table"
        assert users_pos < comments_pos, "User table must be created before Comment table"


class TestMigrationForeignKeyIntegration:
    """Integration tests for complete foreign key generation workflow."""

    def test_complete_user_post_schema_migration(self):
        """Test complete migration generation for User-Post schema with all assertions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string", required=True, unique=True),
                        "email": FieldDefinition(type="string", required=True, unique=True),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    },
                ),
                "Post": Model(
                    name="Post",
                    description="A blog post written by a user",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                        "content": FieldDefinition(type="text", required=True),
                        "published": FieldDefinition(type="bool", default=False),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                        "updated_at": FieldDefinition(type="datetime", auto="update"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema,
            migration_name="create_users_and_posts",
            down_revision=None,
        )

        # Verify migration structure
        assert '"""create_users_and_posts' in migration_code
        assert "Revision ID:" in migration_code
        assert "from alembic import op" in migration_code
        assert "import sqlalchemy as sa" in migration_code
        assert "def upgrade() -> None:" in migration_code
        assert "def downgrade() -> None:" in migration_code

        # Verify User table creation
        assert "op.create_table('users'," in migration_code
        assert "sa.Column('id', sa.UUID(), nullable=False)" in migration_code
        assert "sa.Column('username', sa.String(), nullable=False)" in migration_code
        assert "sa.Column('email', sa.String(), nullable=False)" in migration_code

        # Verify Post table creation
        assert "op.create_table('posts'," in migration_code
        assert "sa.Column('title', sa.String(), nullable=False)" in migration_code
        assert "sa.Column('content', sa.Text(), nullable=False)" in migration_code

        # Verify foreign key in Post table
        assert "author_id" in migration_code
        assert "sa.Column('author_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True)" in migration_code

        # Verify table creation order
        users_pos = migration_code.index("op.create_table('users',")
        posts_pos = migration_code.index("op.create_table('posts',")
        assert users_pos < posts_pos

        # Verify downgrade operations
        assert "op.drop_table('posts')" in migration_code
        assert "op.drop_table('users')" in migration_code

    def test_migration_file_generation_with_foreign_keys(self):
        """Test that migration files are correctly written to disk with foreign keys."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            generator = AlembicMigrationGenerator()
            migration_file, revision_id = generator.generate_migration_to_file(
                schema=schema,
                migration_name="create_users_posts",
                migrations_dir=migrations_dir,
                down_revision=None,
            )

            # Verify file was created
            assert migration_file.exists()
            assert migration_file.is_file()

            # Verify filename
            assert migration_file.name.endswith(".py")
            assert revision_id in migration_file.name
            assert "create_users_posts" in migration_file.name

            # Read and verify content
            content = migration_file.read_text(encoding="utf-8")

            # Verify foreign key is in the generated file
            assert "author_id" in content
            assert "sa.ForeignKey('users.id')" in content
            assert "op.create_table('users'," in content
            assert "op.create_table('posts'," in content

    def test_no_foreign_keys_for_hasmany_relation(self):
        """Test that hasMany relationships do not generate foreign key columns in the parent model."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                    },
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify that User table does NOT have a posts_id foreign key column
        # (hasMany does not create FK in parent table)
        users_table_start = migration_code.index("op.create_table('users',")
        users_table_end = migration_code.index(")", users_table_start + 50)
        users_table_section = migration_code[users_table_start:users_table_end]

        assert "posts_id" not in users_table_section, \
            "hasMany relationship should not create foreign key in parent table"

        # Verify that Post table DOES have author_id foreign key
        assert "author_id" in migration_code
        assert "sa.ForeignKey('users.id')" in migration_code


class TestMigrationForeignKeyEdgeCases:
    """Test edge cases for foreign key generation."""

    def test_self_referential_relationship(self):
        """Test foreign key generation for self-referential relationships."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                    relations={
                        "manager": Relation(type="belongsTo", model="User"),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify self-referential foreign key is generated
        assert "manager_id" in migration_code
        assert "sa.ForeignKey('users.id')" in migration_code

    def test_model_without_relationships(self):
        """Test that models without relationships do not generate foreign keys."""
        schema = SchnitzelSchema(
            models={
                "Tag": Model(
                    name="Tag",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                    },
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Verify no ForeignKey constraints are generated
        assert "sa.ForeignKey(" not in migration_code, \
            "No foreign keys should be generated for model without relationships"

    def test_empty_relations_dict(self):
        """Test that empty relations dict does not cause errors."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={},
                ),
            }
        )

        generator = AlembicMigrationGenerator()
        migration_code = generator.generate_initial_migration(
            schema=schema, migration_name="test", down_revision=None
        )

        # Should not contain any foreign keys
        assert "sa.ForeignKey(" not in migration_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
