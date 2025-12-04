"""Integration tests for serve command color scheme (api_119).

Tests for:
- api_119: Serve command output uses consistent color scheme
"""

import pytest
from pathlib import Path


class TestServeColors:
    """Tests for api_119: Serve command output uses consistent color scheme."""

    def test_console_import(self):
        """Test that Rich console is used for colored output."""
        from schnitzel.cli.commands import serve
        # Should import console from rich
        assert hasattr(serve, 'console')

    def test_color_codes_defined(self):
        """Test that color codes are used consistently."""
        from schnitzel.cli.commands import serve
        import inspect
        source = inspect.getsource(serve)

        # Should use Rich color markup
        assert "[green]" in source or "[blue]" in source or "[red]" in source

    def test_success_color_green(self):
        """Test that success messages use green."""
        from schnitzel.cli.commands import serve
        import inspect
        source = inspect.getsource(serve)

        # Success messages should use green
        assert "[green]" in source

    def test_error_color_red(self):
        """Test that error messages use red."""
        from schnitzel.cli.commands import serve
        import inspect
        source = inspect.getsource(serve)

        # Error messages should use red
        assert "[red]" in source

    def test_info_color_blue(self):
        """Test that info messages use blue."""
        from schnitzel.cli.commands import serve
        import inspect
        source = inspect.getsource(serve)

        # Info messages should use blue
        assert "[blue]" in source

    def test_warning_color_yellow(self):
        """Test that warning messages use yellow."""
        from schnitzel.cli.commands import serve
        import inspect
        source = inspect.getsource(serve)

        # Warning messages should use yellow
        assert "[yellow]" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
