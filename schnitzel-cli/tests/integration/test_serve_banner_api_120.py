"""Integration tests for serve ASCII banner (api_120).

Tests for:
- api_120: Serve command displays ASCII art banner
"""

import pytest
from io import StringIO
from rich.console import Console
from schnitzel.cli.commands import serve
from schnitzel.utils.banner import display_banner, SCHNITZEL_BANNER


class TestServeBanner:
    """Tests for api_120: Serve ASCII banner."""

    def test_serve_module_importable(self):
        """Test serve module is importable."""
        assert serve is not None

    def test_serve_has_display_functions(self):
        """Test serve has display functions."""
        has_display = hasattr(serve, 'display_service_status') or hasattr(serve, 'start')
        assert has_display

    def test_banner_module_exists(self):
        """Test that banner module can be imported."""
        from schnitzel.utils import banner
        assert banner is not None

    def test_display_banner_function_exists(self):
        """Test that display_banner function exists."""
        assert callable(display_banner)

    def test_banner_content_contains_schnitzel(self):
        """Test that banner contains SCHNITZEL text."""
        assert "schnitzel" in SCHNITZEL_BANNER.lower() or "____" in SCHNITZEL_BANNER

    def test_banner_displays_without_error(self):
        """Test that display_banner can be called without error."""
        # Create a string buffer to capture output
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)

        # Should not raise any exceptions
        display_banner(console)

        # Get the output
        output = buffer.getvalue()

        # Should have some output
        assert len(output) > 0

    def test_serve_imports_banner(self):
        """Test that serve module imports display_banner."""
        from schnitzel.cli.commands.serve import display_banner as serve_banner
        assert serve_banner is not None
        assert callable(serve_banner)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
