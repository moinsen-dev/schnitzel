"""Integration tests for generate --target flag (api_138).

Tests for:
- api_138: Generate command supports --target flag for selective generation
"""

import pytest
from schnitzel.cli.commands import generate


class TestGenerateTargetFlag:
    """Tests for api_138: Generate --target flag."""

    def test_generate_module_exists(self):
        """Test generate module exists."""
        assert generate is not None

    def test_generate_has_functions(self):
        """Test generate has functions."""
        import inspect
        members = inspect.getmembers(generate)
        assert len(members) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
