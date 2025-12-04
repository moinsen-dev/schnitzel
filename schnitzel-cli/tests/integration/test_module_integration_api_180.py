"""Integration tests for module integration (api_180).

Tests for:
- api_180: Module integrates with module_00_foundation
"""

import pytest


class TestModuleIntegration:
    """Tests for api_180: Module integrates with module_00_foundation."""

    def test_schnitzel_package_exists(self):
        """Test that schnitzel package exists."""
        import schnitzel
        assert schnitzel is not None

    def test_cli_module_exists(self):
        """Test that CLI module exists."""
        from schnitzel import cli
        assert cli is not None

    def test_generators_module_exists(self):
        """Test that generators module exists."""
        from schnitzel import generators
        assert generators is not None

    def test_schema_module_exists(self):
        """Test that schema module exists."""
        from schnitzel import schema
        assert schema is not None

    def test_utils_module_exists(self):
        """Test that utils module exists."""
        from schnitzel import utils
        assert utils is not None

    def test_all_generators_accessible(self):
        """Test that all generators are accessible from package."""
        from schnitzel.generators.python.routes import FastAPIRouteGenerator
        from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
        from schnitzel.generators.dart.api_client import DartApiClientGenerator
        from schnitzel.generators.infra.migrations import AlembicMigrationGenerator

        assert FastAPIRouteGenerator is not None
        assert SQLAlchemyORMGenerator is not None
        assert DartApiClientGenerator is not None
        assert AlembicMigrationGenerator is not None

    def test_schema_classes_accessible(self):
        """Test that schema classes are accessible."""
        from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation

        assert SchnitzelSchema is not None
        assert Model is not None
        assert FieldDefinition is not None
        assert Relation is not None

    def test_cli_commands_accessible(self):
        """Test that CLI commands are accessible."""
        from schnitzel.cli.commands import generate, serve, validate, migrate

        assert generate is not None
        assert serve is not None
        assert validate is not None
        assert migrate is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
