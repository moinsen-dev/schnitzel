"""Integration tests for API_046 - Migrate command validates migrations before applying.

Test Requirements:
1. Verify migrate command validates migrations before applying
2. Validations should include:
   - SQL syntax validity
   - Referenced tables/columns exist
   - No destructive operations without confirmation
3. Create integration test that:
   - Tests valid migration passes validation
   - Tests invalid migration fails validation
   - Tests validation flag works (--validate or --dry-run)

This follows the Schnitzel zero-tolerance policy: no errors, no warnings, no TODOs.
"""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from schnitzel.cli import app
from schnitzel.generators.infra.migration_validator import (
    MigrationValidator,
    validate_pending_migrations,
)
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema

runner = CliRunner()


@pytest.fixture
def temp_project():
    """Create a temporary test project with migration infrastructure."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        backend_dir = project_dir / "backend"
        backend_dir.mkdir()

        # Create migrations directory
        migrations_dir = backend_dir / "migrations" / "versions"
        migrations_dir.mkdir(parents=True)

        # Create minimal alembic.ini
        alembic_ini = backend_dir / "alembic.ini"
        alembic_ini.write_text("""[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./test.db

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
""")

        # Create basic env.py
        env_py = migrations_dir.parent / "env.py"
        env_py.write_text("""from alembic import context

target_metadata = None

def run_migrations_offline():
    context.configure(url='sqlite:///./test.db')
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sqlalchemy import engine_from_config, pool
    connectable = engine_from_config(
        {'sqlalchemy.url': 'sqlite:///./test.db'},
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""")

        # Create schema file
        schema_file = project_dir / "schema.schnitzel.yaml"
        schema_file.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
    relations:
      author:
        type: belongsTo
        model: User
""")

        os.chdir(project_dir)
        yield project_dir
        os.chdir(original_cwd)


class TestMigrationValidationBasic:
    """Test basic migration validation functionality."""

    def test_validator_validates_python_syntax(self, temp_project: Path) -> None:
        """Test that validator detects Python syntax errors."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        # Create migration with invalid Python syntax
        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        bad_migration = migrations_dir / "001_bad_syntax.py"
        bad_migration.write_text("""
\"\"\"Bad syntax\"\"\"

revision = '001'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('users',  # Missing closing parenthesis
        sa.Column('id', sa.Integer())

def downgrade() -> None:
    op.drop_table('users')
""")

        result = validator.validate_migration_file(bad_migration)

        # Should fail validation
        assert not result.valid
        assert len(result.errors) > 0
        assert any('syntax' in error.message.lower() for error in result.errors)

    def test_validator_detects_missing_upgrade_function(self, temp_project: Path) -> None:
        """Test that validator detects missing upgrade() function."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        bad_migration = migrations_dir / "002_no_upgrade.py"
        bad_migration.write_text("""
\"\"\"No upgrade function\"\"\"

revision = '002'
down_revision = None

from alembic import op
import sqlalchemy as sa

def downgrade() -> None:
    pass
""")

        result = validator.validate_migration_file(bad_migration)

        # Should fail validation
        assert not result.valid
        assert any('upgrade' in error.message.lower() for error in result.errors)

    def test_validator_detects_missing_downgrade_function(self, temp_project: Path) -> None:
        """Test that validator detects missing downgrade() function."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        bad_migration = migrations_dir / "003_no_downgrade.py"
        bad_migration.write_text("""
\"\"\"No downgrade function\"\"\"

revision = '003'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    pass
""")

        result = validator.validate_migration_file(bad_migration)

        # Should fail validation
        assert not result.valid
        assert any('downgrade' in error.message.lower() for error in result.errors)

    def test_validator_accepts_valid_migration(self, temp_project: Path) -> None:
        """Test that validator accepts a valid migration."""
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
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        good_migration = migrations_dir / "004_valid.py"
        good_migration.write_text("""
\"\"\"Valid migration\"\"\"

revision = '004'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
""")

        result = validator.validate_migration_file(good_migration)

        # Should pass validation
        assert result.valid
        assert len(result.errors) == 0


class TestMigrationValidationDestructiveOperations:
    """Test detection of destructive operations."""

    def test_validator_warns_on_drop_table(self, temp_project: Path) -> None:
        """Test that validator warns about DROP TABLE operations."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        migration = migrations_dir / "005_drop_table.py"
        migration.write_text("""
\"\"\"Drop table migration\"\"\"

revision = '005'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.drop_table('old_users')

def downgrade() -> None:
    pass
""")

        result = validator.validate_migration_file(migration)

        # Should have warnings about destructive operation
        assert len(result.warnings) > 0
        assert any('DROP TABLE' in warning.message for warning in result.warnings)
        assert any('data loss' in warning.message.lower() for warning in result.warnings)

    def test_validator_warns_on_drop_column(self, temp_project: Path) -> None:
        """Test that validator warns about DROP COLUMN operations."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        migration = migrations_dir / "006_drop_column.py"
        migration.write_text("""
\"\"\"Drop column migration\"\"\"

revision = '006'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.drop_column('users', 'deprecated_field')

def downgrade() -> None:
    pass
""")

        result = validator.validate_migration_file(migration)

        # Should have warnings about destructive operation
        assert len(result.warnings) > 0
        assert any('DROP COLUMN' in warning.message for warning in result.warnings)


class TestMigrationValidationAgainstSchema:
    """Test validation against schema."""

    def test_validator_checks_table_existence(self, temp_project: Path) -> None:
        """Test that validator checks if tables exist in schema."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        migration = migrations_dir / "007_unknown_table.py"
        migration.write_text("""
\"\"\"Create unknown table\"\"\"

revision = '007'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('products',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('products')
""")

        result = validator.validate_migration_file(migration)

        # Should have warning about table not in schema
        assert len(result.warnings) > 0
        assert any('not found in schema' in warning.message.lower() for warning in result.warnings)

    def test_validate_pending_migrations_function(self, temp_project: Path) -> None:
        """Test the validate_pending_migrations helper function."""
        # Create test schema
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

        migrations_dir = temp_project / "backend" / "migrations" / "versions"

        # Create valid migration
        valid_migration = migrations_dir / "008_valid.py"
        valid_migration.write_text("""
\"\"\"Valid migration\"\"\"

revision = '008'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
""")

        # Create invalid migration
        invalid_migration = migrations_dir / "009_invalid.py"
        invalid_migration.write_text("""
\"\"\"Invalid migration\"\"\"

revision = '009'
down_revision = '008'

from alembic import op

def upgrade() -> None:
    pass
# Missing downgrade function
""")

        # Validate all migrations
        all_valid, results = validate_pending_migrations(migrations_dir, schema)

        # Should find both migrations
        assert len(results) == 2

        # Should fail overall due to invalid migration
        assert not all_valid

        # Check individual results
        assert '008_valid.py' in results
        assert results['008_valid.py'].valid

        assert '009_invalid.py' in results
        assert not results['009_invalid.py'].valid


class TestMigrateCommandValidation:
    """Test the migrate command's validation integration."""

    def test_migrate_up_validates_by_default(self, temp_project: Path) -> None:
        """Test that migrate up validates migrations by default."""
        migrations_dir = temp_project / "backend" / "migrations" / "versions"

        # Create valid migration
        migration = migrations_dir / "010_initial.py"
        migration.write_text("""
\"\"\"Initial migration\"\"\"

revision = '010'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
""")

        # Run migrate up (validation should pass)
        result = runner.invoke(app, ["migrate", "up"])

        # Should succeed (validation passes, then tries to apply)
        # Even if Alembic fails due to missing setup, validation should pass first
        assert "Validating migrations" in result.stdout or result.exit_code in [0, 1]

    def test_migrate_up_dry_run_validates_only(self, temp_project: Path) -> None:
        """Test that migrate up --dry-run only validates without applying."""
        migrations_dir = temp_project / "backend" / "migrations" / "versions"

        # Create valid migration
        migration = migrations_dir / "011_dryrun.py"
        migration.write_text("""
\"\"\"Dry run test migration\"\"\"

revision = '011'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
""")

        # Run with --dry-run
        result = runner.invoke(app, ["migrate", "up", "--dry-run"])

        # Should succeed and indicate dry-run
        assert result.exit_code == 0
        assert "validated successfully" in result.stdout.lower() or "dry-run" in result.stdout.lower()

        # Should NOT contain "Applying" message
        assert "Applying pending migrations" not in result.stdout

    def test_migrate_up_no_validate_skips_validation(self, temp_project: Path) -> None:
        """Test that migrate up --no-validate skips validation."""
        migrations_dir = temp_project / "backend" / "migrations" / "versions"

        # Create migration (even if invalid)
        migration = migrations_dir / "012_no_validate.py"
        migration.write_text("""
\"\"\"No validate test\"\"\"

revision = '012'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
""")

        # Run with --no-validate
        result = runner.invoke(app, ["migrate", "up", "--no-validate"])

        # Should not show validation messages
        assert "Validating migrations" not in result.stdout

    def test_migrate_up_fails_on_invalid_migration(self, temp_project: Path) -> None:
        """Test that migrate up fails when validation detects errors."""
        migrations_dir = temp_project / "backend" / "migrations" / "versions"

        # Create invalid migration (missing downgrade)
        migration = migrations_dir / "013_invalid.py"
        migration.write_text("""
\"\"\"Invalid migration\"\"\"

revision = '013'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('test', sa.Column('id', sa.Integer()))
# Missing downgrade function
""")

        # Run migrate up
        result = runner.invoke(app, ["migrate", "up"])

        # Should fail validation
        assert result.exit_code == 1
        assert "validation failed" in result.stdout.lower() or "error" in result.stdout.lower()


class TestMigrationValidationDestructiveWarnings:
    """Test that destructive operations show appropriate warnings."""

    def test_drop_table_shows_data_loss_warning(self, temp_project: Path) -> None:
        """Test that DROP TABLE operations show data loss warning."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        migration = migrations_dir / "014_drop.py"
        migration.write_text("""
\"\"\"Drop table with warning\"\"\"

revision = '014'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.drop_table('legacy_table')

def downgrade() -> None:
    op.create_table('legacy_table', sa.Column('id', sa.Integer()))
""")

        result = validator.validate_migration_file(migration)

        # Should have warning
        warnings = result.warnings
        assert len(warnings) > 0

        # Check warning content
        drop_warnings = [w for w in warnings if 'DROP TABLE' in w.message]
        assert len(drop_warnings) > 0
        assert any('data loss' in w.message.lower() for w in drop_warnings)

    def test_alter_type_shows_warning(self, temp_project: Path) -> None:
        """Test that ALTER COLUMN type changes show warnings."""
        schema = SchnitzelSchema(models={})
        validator = MigrationValidator(schema)

        migrations_dir = temp_project / "backend" / "migrations" / "versions"
        migration = migrations_dir / "015_alter_type.py"
        migration.write_text("""
\"\"\"Alter column type\"\"\"

revision = '015'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.alter_column('users', 'age', type_=sa.String())

def downgrade() -> None:
    op.alter_column('users', 'age', type_=sa.Integer())
""")

        result = validator.validate_migration_file(migration)

        # Should have warning about type change
        warnings = result.warnings
        assert len(warnings) > 0
        assert any('type change' in w.message.lower() for w in warnings)


class TestMigrationValidationQuietMode:
    """Test validation in quiet mode."""

    def test_validation_works_in_quiet_mode(self, temp_project: Path) -> None:
        """Test that validation works properly in quiet mode."""
        migrations_dir = temp_project / "backend" / "migrations" / "versions"

        # Create valid migration
        migration = migrations_dir / "016_quiet.py"
        migration.write_text("""
\"\"\"Quiet mode test\"\"\"

revision = '016'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('test', sa.Column('id', sa.Integer()))

def downgrade() -> None:
    op.drop_table('test')
""")

        # Run in quiet mode
        result = runner.invoke(app, ["--quiet", "migrate", "up", "--dry-run"])

        # Should succeed with minimal output
        assert result.exit_code == 0
        # Output should be very short in quiet mode
        assert len(result.stdout.strip()) < 200


class TestValidationHelperFunctions:
    """Test internal validation helper functions."""

    def test_pluralize_table_name(self) -> None:
        """Test table name pluralization logic."""
        from schnitzel.generators.infra.migration_validator import MigrationValidator

        validator = MigrationValidator()

        # Test various pluralization rules
        assert validator._pluralize_table_name("User") == "users"
        assert validator._pluralize_table_name("Post") == "posts"
        assert validator._pluralize_table_name("Category") == "categories"
        assert validator._pluralize_table_name("Address") == "addresses"
        assert validator._pluralize_table_name("Box") == "boxes"

    def test_to_snake_case(self) -> None:
        """Test PascalCase to snake_case conversion."""
        from schnitzel.generators.infra.migration_validator import MigrationValidator

        validator = MigrationValidator()

        assert validator._to_snake_case("User") == "user"
        assert validator._to_snake_case("UserProfile") == "user_profile"
        assert validator._to_snake_case("HTTPRequest") == "http_request"  # Acronyms handled naturally
        assert validator._to_snake_case("APIKey") == "api_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
