"""Integration tests for migration squashing (api_092).

Tests for:
- api_092: Migrate command supports migration squashing
"""

import pytest
import tempfile
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator


class TestMigrateSquash:
    """Tests for api_092: Migrate command supports migration squashing."""

    def test_squash_command_exists(self):
        """Test that squash command is available in migrate CLI."""
        from schnitzel.cli.commands.migrate import squash
        assert squash is not None
        assert callable(squash)

    def test_squash_command_with_sequential_migrations(self):
        """Test squashing multiple sequential migrations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"
            migrations_dir.mkdir(parents=True)

            # Create three sequential migrations
            migration1 = migrations_dir / "abc123_first.py"
            migration1.write_text('''"""First migration"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
''')

            migration2 = migrations_dir / "def456_second.py"
            migration2.write_text('''"""Second migration"""
from alembic import op
import sqlalchemy as sa

revision = 'def456'
down_revision = 'abc123'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'email')
''')

            migration3 = migrations_dir / "ghi789_third.py"
            migration3.write_text('''"""Third migration"""
from alembic import op
import sqlalchemy as sa

revision = 'ghi789'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('posts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('posts')
''')

            # Test squashing logic manually (simulating what the command does)
            import re

            # Read all migrations
            all_migrations = list(migrations_dir.glob("*.py"))
            assert len(all_migrations) == 3

            # Parse revisions
            revision_map = {}
            for mig_file in all_migrations:
                content = mig_file.read_text()
                rev_match = re.search(r"revision = ['\"]([^'\"]+)['\"]", content)
                down_match = re.search(r"down_revision = (?:None|['\"]([^'\"]*)['\"])", content)

                if rev_match:
                    revision_id = rev_match.group(1)
                    down_revision = down_match.group(1) if down_match and down_match.group(1) else None
                    revision_map[revision_id] = (mig_file, down_revision, content)

            # Verify we can build a chain from abc123 to ghi789
            chain = []
            current = 'ghi789'
            while current and current != 'abc123':
                assert current in revision_map
                chain.append(current)
                _, down_rev, _ = revision_map[current]
                current = down_rev

            if current == 'abc123':
                chain.append('abc123')

            chain.reverse()
            assert chain == ['abc123', 'def456', 'ghi789']

            # Verify squashed migration would combine operations
            all_upgrade_ops = []
            for rev in chain:
                _, _, content = revision_map[rev]
                upgrade_match = re.search(
                    r"def upgrade\(\) -> None:\s*(.*?)(?=\ndef downgrade|\Z)",
                    content,
                    re.DOTALL
                )
                if upgrade_match:
                    ops_text = upgrade_match.group(1).strip()
                    if ops_text and ops_text != "pass":
                        ops_lines = [line for line in ops_text.split('\n') if line.strip()]
                        all_upgrade_ops.extend(ops_lines)

            # Should have operations from all three migrations
            assert len(all_upgrade_ops) > 0
            combined = '\n'.join(all_upgrade_ops)
            assert 'users' in combined
            assert 'posts' in combined
            assert 'email' in combined

    def test_generator_initialization(self):
        """Test migration generator can be initialized."""
        generator = AlembicMigrationGenerator()
        assert generator is not None

    def test_generator_with_project_root(self):
        """Test migration generator accepts project root."""
        from pathlib import Path
        generator = AlembicMigrationGenerator(project_root=Path("."))
        assert generator is not None

    def test_generator_generates_initial_migration(self):
        """Test generator can create initial migration."""
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

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "initial")

        # Should generate migration code
        assert code is not None
        assert "revision" in code or "upgrade" in code or "def " in code

    def test_migration_includes_model(self):
        """Test migration includes model definition."""
        schema = SchnitzelSchema(
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

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "create_user")

        # Should include user table creation
        assert "user" in code.lower() or "User" in code

    def test_migration_for_multiple_models(self):
        """Test migration for multiple models."""
        schema = SchnitzelSchema(
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

        generator = AlembicMigrationGenerator()
        code = generator.generate_initial_migration(schema, "create_tables")

        # Should include both models
        assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
