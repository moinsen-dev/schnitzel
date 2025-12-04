"""Integration tests for templates handling empty schema (api_127).

Tests for:
- api_127: Templates handle edge case: empty schema
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestTemplatesEmptySchema:
    """Tests for api_127: Templates handle edge case: empty schema."""

    def test_routes_generator_handles_empty_models(self):
        """Test that routes generator handles empty models dict."""
        schema = SchnitzelSchema(models={})

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should still generate valid code (may be minimal)
        assert code is not None

    def test_orm_generator_handles_empty_models(self):
        """Test that ORM generator handles empty models dict."""
        schema = SchnitzelSchema(models={})

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should still generate valid code (imports at minimum)
        assert code is not None

    def test_dart_generator_handles_empty_models(self):
        """Test that Dart generator handles empty models dict."""
        schema = SchnitzelSchema(models={})

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should still generate valid code
        assert code is not None

    def test_routes_generator_handles_empty_endpoints(self):
        """Test that routes generator handles empty endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={}
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should still generate valid code
        assert code is not None

    def test_schema_with_no_fields(self):
        """Test handling model with no fields."""
        # This should not normally happen, but test graceful handling
        schema = SchnitzelSchema(
            models={
                "Empty": Model(name="Empty", fields={})
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should handle gracefully
        assert code is not None

    def test_complete_empty_schema(self):
        """Test completely empty schema."""
        schema = SchnitzelSchema()

        generators = [
            FastAPIRouteGenerator(),
            SQLAlchemyORMGenerator(),
            DartApiClientGenerator(),
        ]

        for generator in generators:
            code = generator.generate(schema)
            assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
