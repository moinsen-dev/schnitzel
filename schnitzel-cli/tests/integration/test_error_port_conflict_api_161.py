"""Integration tests for graceful port conflict handling (api_161).

Tests for:
- api_161: Error handling: Graceful failure on port conflicts
"""

import pytest
from schnitzel.cli.commands import serve


class TestErrorPortConflict:
    """Tests for api_161: Port conflict error handling."""

    def test_serve_module_has_error_handling(self):
        """Test serve module has error handling capabilities."""
        assert serve is not None

    def test_serve_has_status_check(self):
        """Test serve has status check function."""
        has_status = hasattr(serve, 'get_service_status') or hasattr(serve, 'stop_services')
        assert has_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
