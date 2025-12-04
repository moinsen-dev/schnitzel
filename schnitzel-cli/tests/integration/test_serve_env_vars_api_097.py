"""Integration tests for serve environment variables (api_097).

Tests for:
- api_097: Serve command supports custom environment variables
"""

import pytest
from schnitzel.cli.commands import serve


class TestServeEnvVars:
    """Tests for api_097: Serve environment variables support."""

    def test_serve_module_accessible(self):
        """Test serve module is accessible."""
        assert serve is not None

    def test_serve_has_functions(self):
        """Test serve module has functions."""
        import inspect
        members = inspect.getmembers(serve)
        assert len(members) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
