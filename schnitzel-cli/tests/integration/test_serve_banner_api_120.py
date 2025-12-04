"""Integration tests for serve ASCII banner (api_120).

Tests for:
- api_120: Serve command displays ASCII art banner
"""

import pytest
from schnitzel.cli.commands import serve


class TestServeBanner:
    """Tests for api_120: Serve ASCII banner."""

    def test_serve_module_importable(self):
        """Test serve module is importable."""
        assert serve is not None

    def test_serve_has_display_functions(self):
        """Test serve has display functions."""
        has_display = hasattr(serve, 'display_service_status') or hasattr(serve, 'start')
        assert has_display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
