"""Integration tests for migration conflict handling (api_091).

Tests for:
- api_091: Migrate command handles migration conflicts
"""

import pytest
import tempfile
from pathlib import Path
from schnitzel.generators.infra.migrations import MigrationValidator, MigrationConflict


class TestMigrationConflicts:
    """Tests for api_091: Migrate command handles migration conflicts."""

    def test_detect_duplicate_revision(self):
        """Test detection of duplicate revision IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            # Create two migrations with same revision
            migration1 = '''"""Migration 1"""
revision = 'abc12345'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
'''
            migration2 = '''"""Migration 2"""
revision = 'abc12345'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
'''
            (migrations_dir / "001_first.py").write_text(migration1)
            (migrations_dir / "002_second.py").write_text(migration2)

            validator = MigrationValidator(migrations_dir)
            conflicts = validator.detect_conflicts()

            assert len(conflicts) >= 1
            duplicate_conflicts = [c for c in conflicts if c.conflict_type == "duplicate_revision"]
            assert len(duplicate_conflicts) == 1
            assert "abc12345" in duplicate_conflicts[0].description

    def test_detect_branching_conflict(self):
        """Test detection of branching (multiple migrations from same parent)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            # Create base migration
            base = '''"""Base"""
revision = 'base1234'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
'''
            # Create two migrations branching from same parent
            branch1 = '''"""Branch 1"""
revision = 'branch_a'
down_revision = 'base1234'

def upgrade():
    pass

def downgrade():
    pass
'''
            branch2 = '''"""Branch 2"""
revision = 'branch_b'
down_revision = 'base1234'

def upgrade():
    pass

def downgrade():
    pass
'''
            (migrations_dir / "001_base.py").write_text(base)
            (migrations_dir / "002_branch_a.py").write_text(branch1)
            (migrations_dir / "003_branch_b.py").write_text(branch2)

            validator = MigrationValidator(migrations_dir)
            conflicts = validator.detect_conflicts()

            branching_conflicts = [c for c in conflicts if c.conflict_type == "branching"]
            assert len(branching_conflicts) == 1
            assert "base1234" in branching_conflicts[0].description
            assert len(branching_conflicts[0].migrations) == 2

    def test_detect_missing_dependency(self):
        """Test detection of missing migration dependency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            # Create migration that depends on non-existent revision
            orphan = '''"""Orphan Migration"""
revision = 'orphan12'
down_revision = 'missing!'

def upgrade():
    pass

def downgrade():
    pass
'''
            (migrations_dir / "001_orphan.py").write_text(orphan)

            validator = MigrationValidator(migrations_dir)
            conflicts = validator.detect_conflicts()

            missing_conflicts = [c for c in conflicts if c.conflict_type == "missing_dependency"]
            assert len(missing_conflicts) == 1
            assert "missing!" in missing_conflicts[0].description

    def test_no_conflicts_for_valid_chain(self):
        """Test that valid migration chain has no conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            # Create valid chain of migrations
            m1 = '''"""First"""
revision = 'aaaa1111'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
'''
            m2 = '''"""Second"""
revision = 'bbbb2222'
down_revision = 'aaaa1111'

def upgrade():
    pass

def downgrade():
    pass
'''
            m3 = '''"""Third"""
revision = 'cccc3333'
down_revision = 'bbbb2222'

def upgrade():
    pass

def downgrade():
    pass
'''
            (migrations_dir / "001_first.py").write_text(m1)
            (migrations_dir / "002_second.py").write_text(m2)
            (migrations_dir / "003_third.py").write_text(m3)

            validator = MigrationValidator(migrations_dir)
            conflicts = validator.detect_conflicts()

            assert len(conflicts) == 0

    def test_conflict_contains_file_paths(self):
        """Test that conflicts include the involved file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            migration1 = '''"""M1"""
revision = 'same1234'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
'''
            migration2 = '''"""M2"""
revision = 'same1234'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
'''
            file1 = migrations_dir / "conflict_one.py"
            file2 = migrations_dir / "conflict_two.py"
            file1.write_text(migration1)
            file2.write_text(migration2)

            validator = MigrationValidator(migrations_dir)
            conflicts = validator.detect_conflicts()

            assert len(conflicts) >= 1
            conflict = conflicts[0]
            assert "conflict_one.py" in str(conflict.migrations)
            assert "conflict_two.py" in str(conflict.migrations)

    def test_empty_directory_no_conflicts(self):
        """Test that empty directory returns no conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir)

            validator = MigrationValidator(migrations_dir)
            conflicts = validator.detect_conflicts()

            assert len(conflicts) == 0

    def test_nonexistent_directory_no_conflicts(self):
        """Test that nonexistent directory returns no conflicts."""
        validator = MigrationValidator("/nonexistent/path/migrations")
        conflicts = validator.detect_conflicts()

        assert len(conflicts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
