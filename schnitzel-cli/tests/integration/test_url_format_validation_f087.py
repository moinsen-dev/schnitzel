"""Test F087: Schema validator validates URL format constraint.

This feature tests that the schema validator properly handles the 'url' format constraint
for string fields. The URL format is used for schema validation purposes to indicate
that a string field should contain a valid URL.

Requirements:
- Schema validator accepts format: url as a valid constraint
- Fields with url format validate correctly in the schema
- URL format constraint does not block code generation
"""

import pytest
from schnitzel.schema import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python import PythonModelGenerator


class TestUrlFormatValidation:
    """Test URL format constraint validation."""

    def test_url_format_accepted(self):
        """Test that validator accepts 'url' format as a valid constraint."""
        schema = SchnitzelSchema(
            models={
                "Resource": Model(
                    name="Resource",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "website": FieldDefinition(type="string", format="url"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation
        assert result.valid is True, f"Expected validation to pass but got errors: {result.errors}"
        assert result.errors == []

    def test_field_with_url_format(self):
        """Test that field with url format validates correctly."""
        schema = SchnitzelSchema(
            models={
                "Company": Model(
                    name="Company",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "homepage": FieldDefinition(type="string", format="url"),
                        "api_endpoint": FieldDefinition(type="string", format="url", optional=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation
        assert result.valid is True
        assert result.errors == []

    def test_url_format_in_generated_code(self):
        """Test that url format does not block code generation."""
        schema = SchnitzelSchema(
            models={
                "Website": Model(
                    name="Website",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "url": FieldDefinition(type="string", format="url"),
                        "description": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        # First validate the schema
        validator = SchemaValidator()
        result = validator.validate(schema)
        assert result.valid is True

        # Then generate code - should not fail
        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify code was generated successfully
        assert "class Website(BaseModel):" in code
        assert "url: str" in code
        assert "description: str | None = None" in code
        assert "from uuid import UUID" in code

    def test_multiple_url_fields(self):
        """Test model with multiple URL format fields."""
        schema = SchnitzelSchema(
            models={
                "SocialProfile": Model(
                    name="SocialProfile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
                        "website": FieldDefinition(type="string", format="url", optional=True),
                        "blog": FieldDefinition(type="string", format="url", optional=True),
                        "portfolio": FieldDefinition(type="string", format="url", optional=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation
        assert result.valid is True
        assert result.errors == []

    def test_url_format_with_unique_constraint(self):
        """Test that url format works with unique constraint."""
        schema = SchnitzelSchema(
            models={
                "Repository": Model(
                    name="Repository",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "clone_url": FieldDefinition(type="string", format="url", unique=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation and track unique field
        assert result.valid is True
        assert result.errors == []
        assert "Repository" in result.unique_fields
        assert "clone_url" in result.unique_fields["Repository"]

    def test_url_format_with_required_constraint(self):
        """Test that url format works with required constraint."""
        schema = SchnitzelSchema(
            models={
                "Service": Model(
                    name="Service",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "endpoint": FieldDefinition(type="string", format="url", required=True),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation
        assert result.valid is True
        assert result.errors == []

    def test_url_format_only_on_string_type(self):
        """Test that url format is rejected on non-string types."""
        schema = SchnitzelSchema(
            models={
                "InvalidModel": Model(
                    name="InvalidModel",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "port": FieldDefinition(type="int", format="url"),  # Invalid - int with url format
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail validation
        assert result.valid is False
        assert len(result.errors) > 0

        error_message = "\n".join(result.errors)
        assert "url" in error_message.lower()
        assert "string" in error_message.lower()
        assert "port" in error_message
        assert "int" in error_message

    def test_url_format_in_complex_schema(self):
        """Test url format in a complex schema with multiple models."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string", format="email"),
                        "website": FieldDefinition(type="string", format="url", optional=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "content": FieldDefinition(type="string"),
                        "source_url": FieldDefinition(type="string", format="url", optional=True),
                    }
                ),
                "Company": Model(
                    name="Company",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "homepage": FieldDefinition(type="string", format="url"),
                        "api_endpoint": FieldDefinition(type="string", format="url"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation
        assert result.valid is True
        assert result.errors == []

    def test_url_vs_uri_format_distinct(self):
        """Test that url and uri formats are distinct and both accepted."""
        # Schema with url format
        schema_url = SchnitzelSchema(
            models={
                "WebResource": Model(
                    name="WebResource",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "address": FieldDefinition(type="string", format="url"),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result_url = validator.validate(schema_url)
        assert result_url.valid is True

        # Schema with uri format (more generic)
        schema_uri = SchnitzelSchema(
            models={
                "Resource": Model(
                    name="Resource",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "identifier": FieldDefinition(type="string", format="uri"),
                    }
                )
            }
        )

        result_uri = validator.validate(schema_uri)
        assert result_uri.valid is True

        # Both should be valid and distinct
        assert result_url.valid is True
        assert result_uri.valid is True

    def test_url_format_with_default_value(self):
        """Test that url format field can have a default value."""
        schema = SchnitzelSchema(
            models={
                "Configuration": Model(
                    name="Configuration",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "homepage": FieldDefinition(
                            type="string",
                            format="url",
                            default="https://example.com"
                        ),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should pass validation
        assert result.valid is True
        assert result.errors == []

        # Generate code to ensure default is preserved
        generator = PythonModelGenerator()
        code = generator.generate(schema)

        assert "class Configuration(BaseModel):" in code
        assert "homepage: str" in code
        assert '"https://example.com"' in code

    def test_url_format_suggestion_for_common_typos(self):
        """Test that validator suggests 'url' format for common typos."""
        # Test with 'website' (common synonym)
        schema = SchnitzelSchema(
            models={
                "Site": Model(
                    name="Site",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "address": FieldDefinition(type="string", format="website"),  # Invalid
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        # Should fail validation
        assert result.valid is False
        error_message = "\n".join(result.errors)

        # Should suggest 'url' as the correct format
        assert "url" in error_message.lower()
        assert "website" in error_message.lower()

    def test_url_format_in_generated_code_maintains_type(self):
        """Test that url format generates correct Python type (str)."""
        schema = SchnitzelSchema(
            models={
                "Link": Model(
                    name="Link",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "target": FieldDefinition(type="string", format="url"),
                        "label": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # URL field should be str type (format is for validation only)
        assert "target: str" in code
        assert "label: str" in code
        assert "class Link(BaseModel):" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
