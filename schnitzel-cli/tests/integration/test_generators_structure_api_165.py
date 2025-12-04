"""Integration tests for API-165 - Generators module structure is properly organized.

Test Requirements:
1. Verify generators directory structure exists
2. Verify all __init__.py files exist with proper exports
3. Verify python/, dart/, and infra/ subdirectories exist
4. Verify all required generator files exist
5. Verify all generator classes are properly importable
6. Verify module structure follows Python best practices

This test ensures the generators module is properly organized following
Schnitzel's zero-tolerance policy: no errors, no warnings, no TODOs.
"""

import importlib
import inspect
from pathlib import Path

import pytest


@pytest.fixture
def generators_dir():
    """Get the path to the generators directory."""
    import schnitzel
    schnitzel_path = Path(schnitzel.__file__).parent
    return schnitzel_path / "generators"


class TestGeneratorsDirectoryStructure:
    """Test that the generators directory structure is properly organized."""

    def test_generators_directory_exists(self, generators_dir: Path) -> None:
        """Test that the generators directory exists."""
        assert generators_dir.exists(), \
            f"Generators directory should exist at {generators_dir}"
        assert generators_dir.is_dir(), \
            f"Generators path should be a directory: {generators_dir}"

    def test_generators_init_exists(self, generators_dir: Path) -> None:
        """Test that generators/__init__.py exists."""
        init_file = generators_dir / "__init__.py"
        assert init_file.exists(), \
            f"Generators __init__.py should exist at {init_file}"
        assert init_file.is_file(), \
            f"Generators __init__.py should be a file: {init_file}"

    def test_python_subdirectory_exists(self, generators_dir: Path) -> None:
        """Test that the python/ subdirectory exists."""
        python_dir = generators_dir / "python"
        assert python_dir.exists(), \
            f"Python generators subdirectory should exist at {python_dir}"
        assert python_dir.is_dir(), \
            f"Python generators path should be a directory: {python_dir}"

    def test_dart_subdirectory_exists(self, generators_dir: Path) -> None:
        """Test that the dart/ subdirectory exists."""
        dart_dir = generators_dir / "dart"
        assert dart_dir.exists(), \
            f"Dart generators subdirectory should exist at {dart_dir}"
        assert dart_dir.is_dir(), \
            f"Dart generators path should be a directory: {dart_dir}"

    def test_infra_subdirectory_exists(self, generators_dir: Path) -> None:
        """Test that the infra/ subdirectory exists."""
        infra_dir = generators_dir / "infra"
        assert infra_dir.exists(), \
            f"Infra generators subdirectory should exist at {infra_dir}"
        assert infra_dir.is_dir(), \
            f"Infra generators path should be a directory: {infra_dir}"


class TestPythonGeneratorsStructure:
    """Test that the Python generators module is properly structured."""

    def test_python_init_exists(self, generators_dir: Path) -> None:
        """Test that generators/python/__init__.py exists."""
        init_file = generators_dir / "python" / "__init__.py"
        assert init_file.exists(), \
            f"Python generators __init__.py should exist at {init_file}"
        assert init_file.is_file(), \
            f"Python generators __init__.py should be a file: {init_file}"

    def test_python_orm_exists(self, generators_dir: Path) -> None:
        """Test that generators/python/orm.py exists."""
        orm_file = generators_dir / "python" / "orm.py"
        assert orm_file.exists(), \
            f"Python ORM generator should exist at {orm_file}"
        assert orm_file.is_file(), \
            f"Python ORM generator should be a file: {orm_file}"

    def test_python_routes_exists(self, generators_dir: Path) -> None:
        """Test that generators/python/routes.py exists."""
        routes_file = generators_dir / "python" / "routes.py"
        assert routes_file.exists(), \
            f"Python routes generator should exist at {routes_file}"
        assert routes_file.is_file(), \
            f"Python routes generator should be a file: {routes_file}"

    def test_python_models_exists(self, generators_dir: Path) -> None:
        """Test that generators/python/models.py exists."""
        models_file = generators_dir / "python" / "models.py"
        assert models_file.exists(), \
            f"Python models generator should exist at {models_file}"
        assert models_file.is_file(), \
            f"Python models generator should be a file: {models_file}"

    def test_python_init_has_proper_exports(self) -> None:
        """Test that python/__init__.py exports all required classes."""
        from schnitzel.generators.python import (
            PythonModelGenerator,
            PythonRouteGenerator,
            SQLAlchemyORMGenerator,
        )

        # Verify the classes are imported
        assert PythonModelGenerator is not None, \
            "PythonModelGenerator should be exported"
        assert SQLAlchemyORMGenerator is not None, \
            "SQLAlchemyORMGenerator should be exported"
        assert PythonRouteGenerator is not None, \
            "PythonRouteGenerator should be exported"

        # Verify __all__ contains the expected exports
        import schnitzel.generators.python as python_module
        assert hasattr(python_module, "__all__"), \
            "Python generators module should define __all__"
        assert "PythonModelGenerator" in python_module.__all__, \
            "__all__ should include PythonModelGenerator"
        assert "SQLAlchemyORMGenerator" in python_module.__all__, \
            "__all__ should include SQLAlchemyORMGenerator"
        assert "PythonRouteGenerator" in python_module.__all__, \
            "__all__ should include PythonRouteGenerator"

    def test_python_generators_are_classes(self) -> None:
        """Test that all Python generators are proper classes."""
        from schnitzel.generators.python import (
            PythonModelGenerator,
            PythonRouteGenerator,
            SQLAlchemyORMGenerator,
        )

        assert inspect.isclass(PythonModelGenerator), \
            "PythonModelGenerator should be a class"
        assert inspect.isclass(SQLAlchemyORMGenerator), \
            "SQLAlchemyORMGenerator should be a class"
        assert inspect.isclass(PythonRouteGenerator), \
            "PythonRouteGenerator should be a class"


class TestDartGeneratorsStructure:
    """Test that the Dart generators module is properly structured."""

    def test_dart_init_exists(self, generators_dir: Path) -> None:
        """Test that generators/dart/__init__.py exists."""
        init_file = generators_dir / "dart" / "__init__.py"
        assert init_file.exists(), \
            f"Dart generators __init__.py should exist at {init_file}"
        assert init_file.is_file(), \
            f"Dart generators __init__.py should be a file: {init_file}"

    def test_dart_api_client_exists(self, generators_dir: Path) -> None:
        """Test that generators/dart/api_client.py exists."""
        api_client_file = generators_dir / "dart" / "api_client.py"
        assert api_client_file.exists(), \
            f"Dart API client generator should exist at {api_client_file}"
        assert api_client_file.is_file(), \
            f"Dart API client generator should be a file: {api_client_file}"

    def test_dart_models_exists(self, generators_dir: Path) -> None:
        """Test that generators/dart/models.py exists."""
        models_file = generators_dir / "dart" / "models.py"
        assert models_file.exists(), \
            f"Dart models generator should exist at {models_file}"
        assert models_file.is_file(), \
            f"Dart models generator should be a file: {models_file}"

    def test_dart_init_has_proper_exports(self) -> None:
        """Test that dart/__init__.py exports all required classes."""
        from schnitzel.generators.dart import (
            DartApiClientGenerator,
            DartModelGenerator,
        )

        # Verify the classes are imported
        assert DartModelGenerator is not None, \
            "DartModelGenerator should be exported"
        assert DartApiClientGenerator is not None, \
            "DartApiClientGenerator should be exported"

        # Verify __all__ contains the expected exports
        import schnitzel.generators.dart as dart_module
        assert hasattr(dart_module, "__all__"), \
            "Dart generators module should define __all__"
        assert "DartModelGenerator" in dart_module.__all__, \
            "__all__ should include DartModelGenerator"
        assert "DartApiClientGenerator" in dart_module.__all__, \
            "__all__ should include DartApiClientGenerator"

    def test_dart_generators_are_classes(self) -> None:
        """Test that all Dart generators are proper classes."""
        from schnitzel.generators.dart import (
            DartApiClientGenerator,
            DartModelGenerator,
        )

        assert inspect.isclass(DartModelGenerator), \
            "DartModelGenerator should be a class"
        assert inspect.isclass(DartApiClientGenerator), \
            "DartApiClientGenerator should be a class"


class TestInfraGeneratorsStructure:
    """Test that the infrastructure generators module is properly structured."""

    def test_infra_init_exists(self, generators_dir: Path) -> None:
        """Test that generators/infra/__init__.py exists."""
        init_file = generators_dir / "infra" / "__init__.py"
        assert init_file.exists(), \
            f"Infra generators __init__.py should exist at {init_file}"
        assert init_file.is_file(), \
            f"Infra generators __init__.py should be a file: {init_file}"

    def test_infra_migrations_exists(self, generators_dir: Path) -> None:
        """Test that generators/infra/migrations.py exists."""
        migrations_file = generators_dir / "infra" / "migrations.py"
        assert migrations_file.exists(), \
            f"Infra migrations generator should exist at {migrations_file}"
        assert migrations_file.is_file(), \
            f"Infra migrations generator should be a file: {migrations_file}"

    def test_infra_init_has_proper_exports(self) -> None:
        """Test that infra/__init__.py exports all required classes."""
        from schnitzel.generators.infra import AlembicMigrationGenerator

        # Verify the class is imported
        assert AlembicMigrationGenerator is not None, \
            "AlembicMigrationGenerator should be exported"

        # Verify __all__ contains the expected exports
        import schnitzel.generators.infra as infra_module
        assert hasattr(infra_module, "__all__"), \
            "Infra generators module should define __all__"
        assert "AlembicMigrationGenerator" in infra_module.__all__, \
            "__all__ should include AlembicMigrationGenerator"

    def test_infra_generators_are_classes(self) -> None:
        """Test that all infra generators are proper classes."""
        from schnitzel.generators.infra import AlembicMigrationGenerator

        assert inspect.isclass(AlembicMigrationGenerator), \
            "AlembicMigrationGenerator should be a class"


class TestMainGeneratorsModuleExports:
    """Test that the main generators module exports all generator classes."""

    def test_main_generators_init_exports(self) -> None:
        """Test that generators/__init__.py exports all required classes."""
        from schnitzel.generators import (
            AlembicMigrationGenerator,
            DartApiClientGenerator,
            DartModelGenerator,
            PythonModelGenerator,
            PythonRouteGenerator,
            SQLAlchemyORMGenerator,
        )

        # Verify all classes are imported
        assert PythonModelGenerator is not None
        assert SQLAlchemyORMGenerator is not None
        assert PythonRouteGenerator is not None
        assert DartModelGenerator is not None
        assert DartApiClientGenerator is not None
        assert AlembicMigrationGenerator is not None

    def test_main_generators_all_list(self) -> None:
        """Test that generators/__init__.py defines __all__ with all exports."""
        import schnitzel.generators as generators_module

        assert hasattr(generators_module, "__all__"), \
            "Generators module should define __all__"

        expected_exports = [
            "PythonModelGenerator",
            "SQLAlchemyORMGenerator",
            "PythonRouteGenerator",
            "DartModelGenerator",
            "DartApiClientGenerator",
            "AlembicMigrationGenerator",
        ]

        for export in expected_exports:
            assert export in generators_module.__all__, \
                f"__all__ should include {export}"

    def test_all_generators_importable_from_main_module(self) -> None:
        """Test that all generators can be imported from the main generators module."""
        try:
            from schnitzel.generators import (  # noqa: F401
                AlembicMigrationGenerator,
                DartApiClientGenerator,
                DartModelGenerator,
                PythonModelGenerator,
                PythonRouteGenerator,
                SQLAlchemyORMGenerator,
            )
        except ImportError as e:
            pytest.fail(f"Failed to import generators from main module: {e}")


class TestGeneratorClassesStructure:
    """Test that all generator classes follow proper structure."""

    def test_python_model_generator_has_generate_method(self) -> None:
        """Test that PythonModelGenerator has a generate method."""
        from schnitzel.generators import PythonModelGenerator

        generator = PythonModelGenerator()
        assert hasattr(generator, "generate"), \
            "PythonModelGenerator should have a generate method"
        assert callable(generator.generate), \
            "generate should be a callable method"

    def test_sqlalchemy_orm_generator_has_generate_method(self) -> None:
        """Test that SQLAlchemyORMGenerator has a generate method."""
        from schnitzel.generators import SQLAlchemyORMGenerator

        generator = SQLAlchemyORMGenerator()
        assert hasattr(generator, "generate"), \
            "SQLAlchemyORMGenerator should have a generate method"
        assert callable(generator.generate), \
            "generate should be a callable method"

    def test_python_route_generator_has_generate_method(self) -> None:
        """Test that PythonRouteGenerator has a generate method."""
        from schnitzel.generators import PythonRouteGenerator

        generator = PythonRouteGenerator()
        assert hasattr(generator, "generate"), \
            "PythonRouteGenerator should have a generate method"
        assert callable(generator.generate), \
            "generate should be a callable method"

    def test_dart_model_generator_has_generate_method(self) -> None:
        """Test that DartModelGenerator has a generate method."""
        from schnitzel.generators import DartModelGenerator

        generator = DartModelGenerator()
        assert hasattr(generator, "generate"), \
            "DartModelGenerator should have a generate method"
        assert callable(generator.generate), \
            "generate should be a callable method"

    def test_dart_api_client_generator_has_generate_method(self) -> None:
        """Test that DartApiClientGenerator has a generate method."""
        from schnitzel.generators import DartApiClientGenerator

        generator = DartApiClientGenerator()
        assert hasattr(generator, "generate"), \
            "DartApiClientGenerator should have a generate method"
        assert callable(generator.generate), \
            "generate should be a callable method"

    def test_alembic_migration_generator_has_generate_method(self) -> None:
        """Test that AlembicMigrationGenerator has generate methods."""
        from schnitzel.generators import AlembicMigrationGenerator

        generator = AlembicMigrationGenerator()
        # AlembicMigrationGenerator has specialized generate methods
        assert hasattr(generator, "generate_initial_migration"), \
            "AlembicMigrationGenerator should have a generate_initial_migration method"
        assert callable(generator.generate_initial_migration), \
            "generate_initial_migration should be a callable method"
        assert hasattr(generator, "generate_diff_migration"), \
            "AlembicMigrationGenerator should have a generate_diff_migration method"
        assert callable(generator.generate_diff_migration), \
            "generate_diff_migration should be a callable method"


class TestModuleDocstrings:
    """Test that all modules have proper docstrings."""

    def test_generators_module_has_docstring(self) -> None:
        """Test that generators module has a docstring."""
        import schnitzel.generators as generators_module

        assert generators_module.__doc__ is not None, \
            "Generators module should have a docstring"
        assert len(generators_module.__doc__.strip()) > 0, \
            "Generators module docstring should not be empty"

    def test_python_generators_module_has_docstring(self) -> None:
        """Test that python generators module has a docstring."""
        import schnitzel.generators.python as python_module

        assert python_module.__doc__ is not None, \
            "Python generators module should have a docstring"
        assert len(python_module.__doc__.strip()) > 0, \
            "Python generators module docstring should not be empty"

    def test_dart_generators_module_has_docstring(self) -> None:
        """Test that dart generators module has a docstring."""
        import schnitzel.generators.dart as dart_module

        assert dart_module.__doc__ is not None, \
            "Dart generators module should have a docstring"
        assert len(dart_module.__doc__.strip()) > 0, \
            "Dart generators module docstring should not be empty"

    def test_infra_generators_module_has_docstring(self) -> None:
        """Test that infra generators module has a docstring."""
        import schnitzel.generators.infra as infra_module

        assert infra_module.__doc__ is not None, \
            "Infra generators module should have a docstring"
        assert len(infra_module.__doc__.strip()) > 0, \
            "Infra generators module docstring should not be empty"


class TestNoPycacheInSourceControl:
    """Test that __pycache__ directories are properly ignored."""

    def test_no_pycache_in_git(self, generators_dir: Path) -> None:
        """Test that __pycache__ directories exist but would be ignored by git."""
        # This is more of a structural test - __pycache__ should exist at runtime
        # but should be in .gitignore
        pycache_dirs = list(generators_dir.glob("**/__pycache__"))

        # If __pycache__ exists (which it should at runtime), verify .gitignore
        if pycache_dirs:
            gitignore_path = generators_dir.parent.parent.parent.parent / ".gitignore"
            if gitignore_path.exists():
                gitignore_content = gitignore_path.read_text()
                assert "__pycache__" in gitignore_content or "*.pyc" in gitignore_content, \
                    ".gitignore should include __pycache__ or *.pyc"


class TestNoCircularImports:
    """Test that there are no circular import issues in generators module."""

    def test_can_import_all_generators_in_sequence(self) -> None:
        """Test that all generators can be imported without circular dependencies."""
        import_sequence = [
            "schnitzel.generators",
            "schnitzel.generators.python",
            "schnitzel.generators.python.models",
            "schnitzel.generators.python.orm",
            "schnitzel.generators.python.routes",
            "schnitzel.generators.dart",
            "schnitzel.generators.dart.models",
            "schnitzel.generators.dart.api_client",
            "schnitzel.generators.infra",
            "schnitzel.generators.infra.migrations",
        ]

        for module_name in import_sequence:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")


class TestZeroTolerancePolicy:
    """Test that the module follows Schnitzel's zero-tolerance policy."""

    def test_no_todo_comments_in_init_files(self, generators_dir: Path) -> None:
        """Test that __init__.py files do not contain TODO comments."""
        init_files = list(generators_dir.glob("**/__init__.py"))
        todos_found = []

        for init_file in init_files:
            content = init_file.read_text()
            if "TODO" in content or "FIXME" in content or "XXX" in content:
                relative_path = init_file.relative_to(generators_dir)
                todos_found.append(str(relative_path))

        if todos_found:
            pytest.fail(
                "Found TODO/FIXME/XXX comments in __init__.py files (zero-tolerance policy):\n"
                + "\n".join(todos_found)
            )

    def test_all_files_have_proper_encoding(self, generators_dir: Path) -> None:
        """Test that all Python files can be read with UTF-8 encoding."""
        py_files = list(generators_dir.glob("**/*.py"))
        encoding_errors = []

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                assert content is not None
            except UnicodeDecodeError as e:
                relative_path = py_file.relative_to(generators_dir)
                encoding_errors.append(f"{relative_path}: {e}")

        if encoding_errors:
            pytest.fail(
                "Found encoding errors in Python files:\n"
                + "\n".join(encoding_errors)
            )
