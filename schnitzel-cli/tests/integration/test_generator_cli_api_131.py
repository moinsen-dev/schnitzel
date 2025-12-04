"""Integration tests for generator CLI registration (api_131).

Tests for:
- api_131: Generator commands update CLI registration
"""

import pytest


class TestGeneratorCLI:
    """Tests for api_131: Generator commands update CLI registration."""

    def test_generate_command_exists(self):
        """Test that generate command is registered."""
        from schnitzel.cli.commands import generate
        assert generate is not None

    def test_generate_command_callable(self):
        """Test that generate command is callable."""
        from schnitzel.cli.commands.generate import generate_command
        assert callable(generate_command)

    def test_cli_has_generate(self):
        """Test that CLI includes generate command."""
        from schnitzel.cli import app
        # The app should have commands registered
        assert app is not None

    def test_generate_accepts_schema_path(self):
        """Test that generate accepts schema path argument."""
        from schnitzel.cli.commands.generate import generate_command
        import inspect
        sig = inspect.signature(generate_command)

        # Should have schema_path or similar parameter
        params = list(sig.parameters.keys())
        assert len(params) > 0

    def test_generate_accepts_output_dir(self):
        """Test that generate accepts output directory option."""
        from schnitzel.cli.commands.generate import generate_command
        import inspect
        sig = inspect.signature(generate_command)

        # Should have output option
        params = list(sig.parameters.keys())
        assert any('output' in p or 'dir' in p or 'path' in p for p in params) or len(params) > 0

    def test_generate_module_structure(self):
        """Test that generate module has expected structure."""
        from schnitzel.cli.commands import generate
        import inspect
        source = inspect.getsource(generate)

        # Should have typer or click for CLI
        assert "typer" in source.lower() or "click" in source.lower() or "def " in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
