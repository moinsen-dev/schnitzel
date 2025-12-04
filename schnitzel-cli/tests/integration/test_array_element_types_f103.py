"""Integration tests for F103: Schema validator validates array element types.

Test Requirements:
- test_array_element_type_valid - verify valid list element types pass validation
- test_array_invalid_element_type - verify list<unknown_type> is rejected
- test_array_nested_types - verify nested array types are handled appropriately
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator


class TestArrayElementTypeValidation:
    """Test schema validator with array/list element type validation."""

    def test_array_element_type_valid(self):
        """Test that valid list element types pass validation."""
        schema = SchnitzelSchema(
            models={
                "ValidArrays": Model(
                    name="ValidArrays",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                        "scores": FieldDefinition(type="list<float>"),
                        "counts": FieldDefinition(type="list<int>"),
                        "flags": FieldDefinition(type="list<bool>"),
                        "timestamps": FieldDefinition(type="list<datetime>"),
                        "ids": FieldDefinition(type="list<uuid>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # All valid list types should pass
        assert result.valid is True
        assert len(result.errors) == 0

    def test_array_invalid_element_type(self):
        """Test that list<unknown_type> is rejected with helpful error."""
        schema = SchnitzelSchema(
            models={
                "InvalidArray": Model(
                    name="InvalidArray",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bad_field": FieldDefinition(type="list<unknown>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail validation
        assert result.valid is False
        assert len(result.errors) > 0

        # Error should mention the invalid type
        error_text = "\n".join(result.errors)
        assert "unknown" in error_text.lower()
        assert "bad_field" in error_text
        assert "InvalidArray" in error_text

    def test_array_invalid_element_type_shows_suggestions(self):
        """Test that invalid list element types provide helpful suggestions."""
        schema = SchnitzelSchema(
            models={
                "SuggestionTest": Model(
                    name="SuggestionTest",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "numbers": FieldDefinition(type="list<number>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail validation
        assert result.valid is False

        # Error should suggest valid types
        error_text = "\n".join(result.errors)
        assert "int" in error_text or "float" in error_text

    def test_array_element_type_case_sensitive(self):
        """Test that list element type validation is case-sensitive."""
        schema = SchnitzelSchema(
            models={
                "CaseTest": Model(
                    name="CaseTest",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<String>"),  # Should be 'string'
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail - String is not valid, should be string
        assert result.valid is False
        error_text = "\n".join(result.errors)
        assert "String" in error_text or "string" in error_text

    def test_array_empty_element_type(self):
        """Test that list<> (empty element type) is rejected."""
        schema = SchnitzelSchema(
            models={
                "EmptyElement": Model(
                    name="EmptyElement",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bad_list": FieldDefinition(type="list<>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail validation
        assert result.valid is False

    def test_array_malformed_syntax(self):
        """Test that malformed list syntax is rejected."""
        schema = SchnitzelSchema(
            models={
                "MalformedList": Model(
                    name="MalformedList",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bad1": FieldDefinition(type="list<string"),  # Missing >
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail validation
        assert result.valid is False

    def test_array_vector_type_valid(self):
        """Test that vector type (which is list<float>) passes validation."""
        schema = SchnitzelSchema(
            models={
                "VectorTest": Model(
                    name="VectorTest",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "embedding": FieldDefinition(type="vector", dimensions=1536),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Vector type should be valid
        assert result.valid is True
        assert len(result.errors) == 0

    def test_array_json_element_type_valid(self):
        """Test that list<json> is valid (array of JSON objects)."""
        schema = SchnitzelSchema(
            models={
                "NestedJson": Model(
                    name="NestedJson",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "json_array": FieldDefinition(type="list<json>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # list<json> should be valid - represents array of JSON objects
        assert result.valid is True
        assert len(result.errors) == 0

    def test_array_enum_element_type_valid(self):
        """Test that list<enum> is valid (array of enum values)."""
        schema = SchnitzelSchema(
            models={
                "EnumArray": Model(
                    name="EnumArray",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "statuses": FieldDefinition(type="list<enum>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # list<enum> should be valid - represents array of enum values
        assert result.valid is True
        assert len(result.errors) == 0

    def test_array_multiple_invalid_elements(self):
        """Test validation with multiple invalid list element types."""
        schema = SchnitzelSchema(
            models={
                "MultipleInvalid": Model(
                    name="MultipleInvalid",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bad1": FieldDefinition(type="list<unknown1>"),
                        "bad2": FieldDefinition(type="list<unknown2>"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail with multiple errors
        assert result.valid is False
        assert len(result.errors) >= 2

        # Both errors should be present
        error_text = "\n".join(result.errors)
        assert "unknown1" in error_text
        assert "unknown2" in error_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
