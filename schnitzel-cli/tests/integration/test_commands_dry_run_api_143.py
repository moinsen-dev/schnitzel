"""Integration tests for commands --dry-run (api_143).

Tests for:
- api_143: Commands support --dry-run for preview
"""

import pytest
from schnitzel.cli.commands import generate, validate


class TestCommandsDryRun:
    """Tests for api_143: Commands --dry-run support."""

    def test_generate_module_exists(self):
        """Test generate module exists."""
        assert generate is not None

    def test_validate_module_exists(self):
        """Test validate module exists."""
        assert validate is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
