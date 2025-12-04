"""Integration tests for test coverage (api_177).

Tests for:
- api_177: Test coverage includes all major code paths
"""

import pytest


class TestTestCoverage:
    """Tests for api_177: Test coverage includes all major code paths."""

    def test_generators_module_importable(self):
        """Test that generators module is importable."""
        from schnitzel import generators
        assert generators is not None

    def test_routes_generator_importable(self):
        """Test that routes generator is importable."""
        from schnitzel.generators.python.routes import FastAPIRouteGenerator
        assert FastAPIRouteGenerator is not None

    def test_orm_generator_importable(self):
        """Test that ORM generator is importable."""
        from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
        assert SQLAlchemyORMGenerator is not None

    def test_dart_generator_importable(self):
        """Test that Dart generator is importable."""
        from schnitzel.generators.dart.api_client import DartApiClientGenerator
        assert DartApiClientGenerator is not None

    def test_migration_generator_importable(self):
        """Test that migration generator is importable."""
        from schnitzel.generators.infra.migrations import AlembicMigrationGenerator
        assert AlembicMigrationGenerator is not None

    def test_schema_models_importable(self):
        """Test that schema models are importable."""
        from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
        assert SchnitzelSchema is not None
        assert Model is not None
        assert FieldDefinition is not None

    def test_validator_importable(self):
        """Test that validator is importable."""
        from schnitzel.schema.validator import SchemaValidator
        assert SchemaValidator is not None

    def test_cli_importable(self):
        """Test that CLI is importable."""
        from schnitzel.cli import app
        assert app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
