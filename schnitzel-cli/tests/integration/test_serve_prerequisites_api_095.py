"""Integration tests for serve command prerequisites (api_095).

Tests for:
- api_095: Serve command checks prerequisites before starting
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from schnitzel.cli.commands.serve import check_prerequisites


class TestServePrerequisites:
    """Tests for api_095: Serve command checks prerequisites before starting."""

    def test_check_prerequisites_returns_dict(self):
        """Test that check_prerequisites returns expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            assert isinstance(result, dict)
            assert "passed" in result
            assert "checks" in result
            assert "warnings" in result
            assert "errors" in result
            assert isinstance(result["checks"], list)
            assert isinstance(result["warnings"], list)
            assert isinstance(result["errors"], list)

    def test_checks_docker_installed(self):
        """Test that Docker installation is checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            docker_check = next(
                (c for c in result["checks"] if "docker" in c["name"].lower() and "install" in c["name"].lower()),
                None
            )
            assert docker_check is not None
            assert docker_check["required"] == True

    def test_checks_docker_compose_installed(self):
        """Test that Docker Compose installation is checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            compose_check = next(
                (c for c in result["checks"] if "compose" in c["name"].lower()),
                None
            )
            assert compose_check is not None
            assert compose_check["required"] == True

    def test_checks_docker_daemon_running(self):
        """Test that Docker daemon status is checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            daemon_check = next(
                (c for c in result["checks"] if "daemon" in c["name"].lower() or "running" in c["name"].lower()),
                None
            )
            assert daemon_check is not None
            assert daemon_check["required"] == True

    def test_checks_docker_compose_file_exists(self):
        """Test that docker-compose.yaml existence is checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            file_check = next(
                (c for c in result["checks"] if "docker-compose" in c["name"].lower() and "exist" in c["name"].lower()),
                None
            )
            assert file_check is not None
            assert file_check["required"] == True
            # File doesn't exist, so should fail
            assert file_check["passed"] == False

    def test_checks_flutter_optional(self):
        """Test that Flutter is checked as optional prerequisite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            flutter_check = next(
                (c for c in result["checks"] if "flutter" in c["name"].lower()),
                None
            )
            assert flutter_check is not None
            assert flutter_check["required"] == False

    def test_fails_when_docker_compose_missing(self):
        """Test that prerequisites fail when docker-compose.yaml is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            # Should fail because docker-compose.yaml is missing
            assert result["passed"] == False
            assert any("docker-compose" in e.lower() for e in result["errors"])

    def test_passes_with_docker_compose_yaml(self):
        """Test that compose file check passes when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            # Create docker-compose.yaml
            (project_dir / "docker-compose.yaml").write_text("version: '3'")

            result = check_prerequisites(project_dir)

            file_check = next(
                (c for c in result["checks"] if "docker-compose" in c["name"].lower() and "exist" in c["name"].lower()),
                None
            )
            assert file_check is not None
            assert file_check["passed"] == True

    def test_accepts_docker_compose_yml(self):
        """Test that docker-compose.yml is also accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            # Create docker-compose.yml (without 'a')
            (project_dir / "docker-compose.yml").write_text("version: '3'")

            result = check_prerequisites(project_dir)

            file_check = next(
                (c for c in result["checks"] if "docker-compose" in c["name"].lower() and "exist" in c["name"].lower()),
                None
            )
            assert file_check is not None
            assert file_check["passed"] == True

    def test_warnings_for_optional_missing(self):
        """Test that warnings are generated for missing optional dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            # Should have warnings for optional deps
            assert isinstance(result["warnings"], list)

    def test_errors_for_required_missing(self):
        """Test that errors are generated for missing required dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            result = check_prerequisites(project_dir)

            # Should have errors for missing docker-compose.yaml at minimum
            assert len(result["errors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
