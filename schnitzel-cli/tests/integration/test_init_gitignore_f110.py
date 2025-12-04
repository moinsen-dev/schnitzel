"""Integration tests for F110 - Init command creates .gitignore with appropriate entries.

Test Requirements:
- test_gitignore_created - .gitignore file is created
- test_gitignore_contains_entries - .gitignore contains appropriate entries for Python, Dart, etc.
"""

import tempfile
from pathlib import Path
from typer.testing import CliRunner

from schnitzel.cli import app


runner = CliRunner()


def test_gitignore_created() -> None:
    """Test that .gitignore file is created during init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        # Run init command
        result = runner.invoke(app, ["init", str(full_path)])

        # Check command succeeded
        assert result.exit_code == 0, f"Init command failed: {result.stdout}"

        # Check .gitignore exists
        gitignore_file = full_path / ".gitignore"

        assert gitignore_file.exists(), ".gitignore should be created"
        assert gitignore_file.is_file(), ".gitignore should be a file"


def test_gitignore_contains_entries() -> None:
    """Test that .gitignore contains appropriate entries for Python, Dart, etc."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        # Run init command
        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        # Read .gitignore
        gitignore_file = full_path / ".gitignore"
        gitignore_content = gitignore_file.read_text()

        # Check for Python entries
        assert "__pycache__/" in gitignore_content, "Should ignore Python cache"
        assert "*.py[cod]" in gitignore_content, "Should ignore compiled Python files"
        assert ".venv/" in gitignore_content, "Should ignore virtual environments"
        assert ".env" in gitignore_content, "Should ignore environment files"

        # Check for Dart/Flutter entries
        assert ".dart_tool/" in gitignore_content, "Should ignore Dart tools"
        assert "*.freezed.dart" in gitignore_content, "Should ignore Freezed generated files"
        assert "*.g.dart" in gitignore_content, "Should ignore json_serializable generated files"
        assert ".flutter-plugins" in gitignore_content, "Should ignore Flutter plugins"

        # Check for IDE entries
        assert ".vscode/" in gitignore_content, "Should ignore VS Code directory"
        assert ".idea/" in gitignore_content, "Should ignore IntelliJ directory"
        assert ".DS_Store" in gitignore_content, "Should ignore macOS files"

        # Check for Database entries
        assert "*.db" in gitignore_content, "Should ignore database files"
        assert "*.sqlite" in gitignore_content, "Should ignore SQLite files"

        # Check for Docker entries
        assert "docker-compose.override.yaml" in gitignore_content, "Should ignore Docker overrides"

        # Check for generated files
        assert "backend/app/models.py" in gitignore_content, "Should ignore generated backend models"
        assert "packages/app/lib/models/models.dart" in gitignore_content, "Should ignore generated Dart models"


def test_gitignore_python_entries() -> None:
    """Test that .gitignore contains comprehensive Python entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # Python-specific entries
        python_entries = [
            "__pycache__/",
            "*.py[cod]",
            "*.so",
            ".Python",
            "build/",
            "dist/",
            "*.egg-info/",
            "venv/",
            ".venv/",
            "ENV/",
            "env/",
            ".env"
        ]

        for entry in python_entries:
            assert entry in gitignore_content, f"Python entry '{entry}' should be in .gitignore"


def test_gitignore_dart_flutter_entries() -> None:
    """Test that .gitignore contains comprehensive Dart/Flutter entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # Dart/Flutter-specific entries
        dart_entries = [
            ".dart_tool/",
            ".flutter-plugins",
            ".flutter-plugins-dependencies",
            ".packages",
            ".pub-cache/",
            ".pub/",
            "build/",
            "*.freezed.dart",
            "*.g.dart"
        ]

        for entry in dart_entries:
            assert entry in gitignore_content, f"Dart/Flutter entry '{entry}' should be in .gitignore"


def test_gitignore_ide_entries() -> None:
    """Test that .gitignore contains IDE-specific entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # IDE entries
        ide_entries = [
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            ".DS_Store"
        ]

        for entry in ide_entries:
            assert entry in gitignore_content, f"IDE entry '{entry}' should be in .gitignore"


def test_gitignore_generated_files() -> None:
    """Test that .gitignore ignores generated model files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # Generated files should be ignored
        assert "backend/app/models.py" in gitignore_content, \
            "Generated Python models should be in .gitignore"
        assert "packages/app/lib/models/models.dart" in gitignore_content, \
            "Generated Dart models should be in .gitignore"


def test_gitignore_has_comments() -> None:
    """Test that .gitignore has section comments for organization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # Should have section comments
        assert "# Python" in gitignore_content, "Should have Python section comment"
        assert "# Dart / Flutter" in gitignore_content, "Should have Dart/Flutter section comment"
        assert "# IDEs" in gitignore_content, "Should have IDEs section comment"
        assert "# Database" in gitignore_content, "Should have Database section comment"
        assert "# Docker" in gitignore_content, "Should have Docker section comment"
        assert "# Generated files" in gitignore_content, "Should have Generated files section comment"
        assert "# Logs" in gitignore_content, "Should have Logs section comment"


def test_gitignore_format() -> None:
    """Test that .gitignore is properly formatted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # Should not be empty
        assert len(gitignore_content) > 0, ".gitignore should not be empty"

        # Should have multiple lines
        lines = gitignore_content.strip().split("\n")
        assert len(lines) > 10, ".gitignore should have multiple entries"

        # Should start with a comment
        assert lines[0].startswith("#"), ".gitignore should start with a comment"


def test_gitignore_with_force_flag() -> None:
    """Test that .gitignore is recreated when using --force flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        # Create project first time
        result1 = runner.invoke(app, ["init", str(full_path)])
        assert result1.exit_code == 0

        gitignore_file = full_path / ".gitignore"

        # Modify .gitignore
        gitignore_file.write_text("# Modified")

        # Recreate with --force
        result2 = runner.invoke(app, ["init", str(full_path), "--force"])
        assert result2.exit_code == 0

        # .gitignore should be recreated with original content
        gitignore_content = gitignore_file.read_text()
        assert "# Python" in gitignore_content, "Should have original content"
        assert "# Modified" not in gitignore_content, "Modified content should be replaced"


def test_gitignore_logs_entries() -> None:
    """Test that .gitignore contains log file entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        project_name = "test-project"
        full_path = tmppath / project_name

        result = runner.invoke(app, ["init", str(full_path)])
        assert result.exit_code == 0

        gitignore_content = (full_path / ".gitignore").read_text()

        # Log entries
        assert "*.log" in gitignore_content, "Should ignore log files"
        assert "logs/" in gitignore_content, "Should ignore logs directory"
