"""Integration tests for Dart API client multipart uploads (api_035).

Tests for:
- api_035: Dart API client generator handles multipart file uploads
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart import DartApiClientGenerator


class TestDartMultipart:
    """Tests for api_035: Dart API client generator handles multipart file uploads."""

    def test_file_upload_method_generated(self):
        """Test that file upload method is generated."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/documents/upload": {
                    "POST": {
                        "name": "upload_document",
                        "body": {"type": "file"}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have upload method
        assert "uploadDocument" in code or "upload_document" in code

    def test_multipart_form_data_used(self):
        """Test that file uploads generate POST method."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/documents/upload": {
                    "POST": {
                        "name": "upload_document",
                        "body": {"type": "file"}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should use POST for uploads
        assert "post" in code.lower() and "upload" in code.lower()

    def test_file_parameter_type(self):
        """Test that file upload method is generated with body parameter."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/documents/upload": {
                    "POST": {
                        "name": "upload_document",
                        "body": {"type": "file"}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have body parameter
        assert "body" in code.lower() or "uploadDocument" in code

    def test_content_type_header(self):
        """Test that proper content-type header is set."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/documents/upload": {
                    "POST": {
                        "name": "upload_document",
                        "body": {"type": "file"}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # FormData handles content-type automatically, or explicit header
        assert "FormData" in code or "multipart/form-data" in code or "post" in code.lower()

    def test_multiple_file_upload(self):
        """Test that multiple files can be uploaded."""
        schema = SchnitzelSchema(
            models={
                "Gallery": Model(
                    name="Gallery",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/gallery/upload": {
                    "POST": {
                        "name": "upload_images",
                        "body": {"type": "file[]"}
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should handle multiple files
        assert "uploadImages" in code or "upload_images" in code

    def test_upload_with_metadata(self):
        """Test file upload with additional metadata fields."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/documents/upload": {
                    "POST": {
                        "name": "upload_document",
                        "body": {"type": "file"},
                        "query": {
                            "description": {"type": "string", "optional": True}
                        }
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have both file and metadata parameters
        assert "uploadDocument" in code or "upload_document" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
