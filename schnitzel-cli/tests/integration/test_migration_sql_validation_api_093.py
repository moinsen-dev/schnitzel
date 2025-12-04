"""Integration tests for migration SQL syntax validation (api_093).

Tests for:
- api_093: Migrate command validates SQL syntax before execution
"""

import pytest
import tempfile
from pathlib import Path
from schnitzel.generators.infra.migrations import MigrationValidator


class TestSQLSyntaxValidation:
    """Tests for api_093: Migrate command validates SQL syntax before execution."""

    def test_valid_migration_passes(self):
        """Test that valid migration passes validation."""
        valid_migration = '''"""Valid Migration"""
from alembic import op
import sqlalchemy as sa

revision = 'valid123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
'''
        validator = MigrationValidator("/tmp")
        errors = validator.validate_sql_syntax(valid_migration)

        assert len(errors) == 0

    def test_unbalanced_parentheses_detected(self):
        """Test detection of unbalanced parentheses."""
        invalid_migration = '''"""Invalid Migration"""
from alembic import op
import sqlalchemy as sa

revision = 'invalid1'
down_revision = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False
    )

def downgrade() -> None:
    pass
'''
        validator = MigrationValidator("/tmp")
        errors = validator.validate_sql_syntax(invalid_migration)

        # Should detect either syntax error or unbalanced parens
        assert len(errors) > 0

    def test_invalid_nullable_value_detected(self):
        """Test detection of invalid nullable value."""
        invalid_migration = '''"""Invalid Migration"""
from alembic import op
import sqlalchemy as sa

revision = 'invalid2'
down_revision = None

def upgrade() -> None:
    op.add_column('users', sa.Column('name', sa.String(), nullable=Maybe))

def downgrade() -> None:
    pass
'''
        validator = MigrationValidator("/tmp")
        errors = validator.validate_sql_syntax(invalid_migration)

        # Should detect either Python syntax error or invalid nullable
        assert len(errors) > 0

    def test_python_syntax_error_detected(self):
        """Test detection of Python syntax errors."""
        invalid_migration = '''"""Invalid Migration"""
from alembic import op

revision = 'syntax01'
down_revision = None

def upgrade() -> None:
    op.create_table('users'
        # Missing closing paren

def downgrade() -> None:
    pass
'''
        validator = MigrationValidator("/tmp")
        errors = validator.validate_sql_syntax(invalid_migration)

        syntax_errors = [e for e in errors if "syntax error" in e.lower()]
        assert len(syntax_errors) > 0

    def test_validate_migration_file_exists(self):
        """Test validation of migration file that exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''"""Test Migration"""
from alembic import op
import sqlalchemy as sa

revision = 'test1234'
down_revision = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
''')
            f.flush()

            validator = MigrationValidator("/tmp")
            is_valid, errors = validator.validate_migration_file(Path(f.name))

            assert is_valid == True
            assert len(errors) == 0

    def test_validate_migration_file_missing_revision(self):
        """Test validation fails when revision is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''"""Missing revision"""
from alembic import op

# No revision = line

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
''')
            f.flush()

            validator = MigrationValidator("/tmp")
            is_valid, errors = validator.validate_migration_file(Path(f.name))

            assert is_valid == False
            assert any("revision" in e.lower() for e in errors)

    def test_validate_migration_file_missing_upgrade(self):
        """Test validation fails when upgrade function is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''"""Missing upgrade"""
revision = 'miss_up1'
down_revision = None

# No upgrade function

def downgrade() -> None:
    pass
''')
            f.flush()

            validator = MigrationValidator("/tmp")
            is_valid, errors = validator.validate_migration_file(Path(f.name))

            assert is_valid == False
            assert any("upgrade" in e.lower() for e in errors)

    def test_validate_migration_file_missing_downgrade(self):
        """Test validation fails when downgrade function is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''"""Missing downgrade"""
revision = 'miss_dn1'
down_revision = None

def upgrade() -> None:
    pass

# No downgrade function
''')
            f.flush()

            validator = MigrationValidator("/tmp")
            is_valid, errors = validator.validate_migration_file(Path(f.name))

            assert is_valid == False
            assert any("downgrade" in e.lower() for e in errors)

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        validator = MigrationValidator("/tmp")
        is_valid, errors = validator.validate_migration_file(Path("/nonexistent/migration.py"))

        assert is_valid == False
        assert any("not exist" in e.lower() for e in errors)

    def test_validate_complex_valid_migration(self):
        """Test validation of complex but valid migration."""
        complex_migration = '''"""Complex Migration"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'complex1'
down_revision = 'previous'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Add column
    op.add_column('profiles', sa.Column('avatar_url', sa.String(500), nullable=True))

    # Alter column
    op.alter_column('posts', 'title', type_=sa.String(500), nullable=False)


def downgrade() -> None:
    op.alter_column('posts', 'title', type_=sa.String(200), nullable=True)
    op.drop_column('profiles', 'avatar_url')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
'''
        validator = MigrationValidator("/tmp")
        errors = validator.validate_sql_syntax(complex_migration)

        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
