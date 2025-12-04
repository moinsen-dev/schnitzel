"""Integration tests for serve command service logs (api_098).

Tests for:
- api_098: Serve command displays service logs
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from schnitzel.cli.commands.serve import (
    _stream_service_logs,
    _display_service_logs,
)


class TestServiceLogs:
    """Tests for api_098: Serve command displays service logs."""

    def test_stream_service_logs_returns_process(self):
        """Test that _stream_service_logs returns a Popen process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "docker-compose.yaml").write_text("version: '3'")

            # Mock subprocess.Popen to avoid actually running docker
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_popen.return_value = mock_process

                result = _stream_service_logs(project_dir)

                assert result == mock_process
                mock_popen.assert_called_once()

    def test_stream_logs_with_follow(self):
        """Test that follow flag adds -f to command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = MagicMock()

                _stream_service_logs(project_dir, follow=True)

                # Check that -f was in the command
                call_args = mock_popen.call_args
                cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", [])
                assert "-f" in cmd

    def test_stream_logs_without_follow(self):
        """Test that follow=False omits -f flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = MagicMock()

                _stream_service_logs(project_dir, follow=False)

                call_args = mock_popen.call_args
                cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", [])
                assert "-f" not in cmd

    def test_stream_logs_with_tail(self):
        """Test that tail parameter is passed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = MagicMock()

                _stream_service_logs(project_dir, tail=50)

                call_args = mock_popen.call_args
                cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", [])
                assert "--tail" in cmd
                tail_idx = cmd.index("--tail")
                assert cmd[tail_idx + 1] == "50"

    def test_stream_logs_with_specific_services(self):
        """Test that specific services can be filtered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = MagicMock()

                _stream_service_logs(project_dir, services=["db", "redis"])

                call_args = mock_popen.call_args
                cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", [])
                assert "db" in cmd
                assert "redis" in cmd

    def test_display_logs_runs_subprocess(self):
        """Test that _display_service_logs runs subprocess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Log output here",
                    stderr=""
                )

                _display_service_logs(project_dir)

                mock_run.assert_called_once()

    def test_display_logs_with_lines_parameter(self):
        """Test that lines parameter is passed to --tail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="",
                    stderr=""
                )

                _display_service_logs(project_dir, lines=100)

                call_args = mock_run.call_args
                cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", [])
                assert "--tail" in cmd
                tail_idx = cmd.index("--tail")
                assert cmd[tail_idx + 1] == "100"

    def test_stream_logs_handles_exception(self):
        """Test that exceptions are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen:
                mock_popen.side_effect = Exception("Docker not available")

                result = _stream_service_logs(project_dir)

                assert result is None

    def test_display_logs_handles_timeout(self):
        """Test that timeout is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=30)

                # Should not raise
                _display_service_logs(project_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
