"""Integration tests for F101: Python generator handles List fields (array type).

Test Requirements:
- test_list_field_generates - verify list<string> generates list[str]
- test_list_type_correct - verify list<int> generates list[int]
- test_list_with_different_element_types - verify various element types work
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python import PythonModelGenerator


class TestPythonListFields:
    """Test Python model generator with list/array fields."""

    def test_list_field_generates(self):
        """Test that list<string> field generates list[str] in Python."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify list[str] type is generated
        assert "tags: list[str]" in code
        assert "from uuid import UUID" in code

    def test_list_type_correct(self):
        """Test that list<int> generates list[int] type."""
        schema = SchnitzelSchema(
            models={
                "Survey": Model(
                    name="Survey",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "ratings": FieldDefinition(type="list<int>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify list[int] type is generated
        assert "ratings: list[int]" in code

    def test_list_with_different_element_types(self):
        """Test that list fields work with various element types."""
        schema = SchnitzelSchema(
            models={
                "Analytics": Model(
                    name="Analytics",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                        "scores": FieldDefinition(type="list<float>"),
                        "counts": FieldDefinition(type="list<int>"),
                        "flags": FieldDefinition(type="list<bool>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify all list types are generated correctly
        assert "tags: list[str]" in code
        assert "scores: list[float]" in code
        assert "counts: list[int]" in code
        assert "flags: list[bool]" in code

    def test_list_field_optional(self):
        """Test that optional list fields generate correctly."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify optional list type with union syntax
        assert "tags: list[str] | None = None" in code

    def test_list_field_with_default(self):
        """Test that list fields with default values generate correctly."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "features": FieldDefinition(type="list<string>", default=[]),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify list with default empty list
        assert "features: list[str] = []" in code

    def test_list_uuid_type(self):
        """Test that list<uuid> generates list[UUID] with proper import."""
        schema = SchnitzelSchema(
            models={
                "Relationships": Model(
                    name="Relationships",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "friend_ids": FieldDefinition(type="list<uuid>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify list[UUID] type and UUID import
        assert "friend_ids: list[UUID]" in code
        assert "from uuid import UUID" in code

    def test_list_datetime_type(self):
        """Test that list<datetime> generates list[datetime] with proper import."""
        schema = SchnitzelSchema(
            models={
                "Timeline": Model(
                    name="Timeline",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "timestamps": FieldDefinition(type="list<datetime>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify list[datetime] type and datetime import
        assert "timestamps: list[datetime]" in code
        assert "from datetime import datetime" in code

    def test_multiple_list_fields(self):
        """Test that multiple list fields in same model work correctly."""
        schema = SchnitzelSchema(
            models={
                "DataSet": Model(
                    name="DataSet",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                        "values": FieldDefinition(type="list<float>"),
                        "ids": FieldDefinition(type="list<uuid>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify all list fields are present
        assert "tags: list[str]" in code
        assert "values: list[float]" in code
        assert "ids: list[UUID]" in code
        # Verify UUID import
        assert "from uuid import UUID" in code

    def test_list_field_required(self):
        """Test that required list fields don't have default values unless specified."""
        schema = SchnitzelSchema(
            models={
                "RequiredList": Model(
                    name="RequiredList",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "required_tags": FieldDefinition(type="list<string>", required=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify required list field without default
        assert "required_tags: list[str]" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
