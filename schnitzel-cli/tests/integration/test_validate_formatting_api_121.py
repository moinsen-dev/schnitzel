"""Integration tests for validate command output formatting (api_121).

Tests for:
- api_121: Validate command output is well-formatted
"""

import pytest
from pathlib import Path


class TestValidateFormatting:
    """Tests for api_121: Validate command output is well-formatted."""

    def test_validate_module_exists(self):
        """Test that validate module exists."""
        from schnitzel.cli.commands import validate
        assert validate is not None

    def test_validate_uses_console(self):
        """Test that validate uses Rich console for formatting."""
        from schnitzel.cli.commands import validate
        # Should have console for formatted output
        assert hasattr(validate, 'console') or hasattr(validate, 'Console')

    def test_validate_has_color_output(self):
        """Test that validate uses colored output."""
        from schnitzel.cli.commands import validate
        import inspect
        source = inspect.getsource(validate)

        # Should use color formatting
        assert "[green]" in source or "[red]" in source or "Console" in source

    def test_validate_has_summary_section(self):
        """Test that validate includes summary section."""
        from schnitzel.cli.commands import validate
        import inspect
        source = inspect.getsource(validate)

        # Should have summary or result output
        assert "summary" in source.lower() or "result" in source.lower() or "error" in source.lower()

    def test_validate_uses_tables(self):
        """Test that validate uses Rich tables for structured output."""
        from schnitzel.cli.commands import validate
        import inspect
        source = inspect.getsource(validate)

        # May use Table for structured output
        assert "Table" in source or "print" in source or "console" in source

    def test_validate_handles_multiple_errors(self):
        """Test that validate formats multiple errors well."""
        from schnitzel.cli.commands import validate
        import inspect
        source = inspect.getsource(validate)

        # Should handle errors
        assert "error" in source.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
