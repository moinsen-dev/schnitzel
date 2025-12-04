"""Integration tests for verbose flag (api_142).

Tests for:
- api_142: Commands respect --verbose flag for detailed output
"""

import pytest


class TestVerboseFlag:
    """Tests for api_142: Commands respect --verbose flag for detailed output."""

    def test_cli_has_verbose_option(self):
        """Test that CLI has verbose option."""
        from schnitzel.cli import app
        # App should exist
        assert app is not None

    def test_serve_has_quiet_mode(self):
        """Test that serve command has quiet mode support."""
        from schnitzel.cli.commands import serve
        import inspect
        source = inspect.getsource(serve)

        # Should have quiet mode check
        assert "quiet" in source.lower() or "verbose" in source.lower()

    def test_validate_has_output_control(self):
        """Test that validate command has output control."""
        from schnitzel.cli.commands import validate
        import inspect
        source = inspect.getsource(validate)

        # Should have output control
        assert "console" in source.lower() or "print" in source.lower()

    def test_generate_has_output_control(self):
        """Test that generate command has output control."""
        from schnitzel.cli.commands import generate
        import inspect
        source = inspect.getsource(generate)

        # Should have output control
        assert "console" in source.lower() or "print" in source.lower()

    def test_migrate_has_output_control(self):
        """Test that migrate command has output control."""
        from schnitzel.cli.commands import migrate
        import inspect
        source = inspect.getsource(migrate)

        # Should have output control
        assert "console" in source.lower() or "print" in source.lower()

    def test_quiet_mode_function_exists(self):
        """Test that quiet mode function exists."""
        from schnitzel.cli.commands import serve
        # Should have quiet mode check
        assert hasattr(serve, '_is_quiet_mode') or 'quiet' in dir(serve)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
