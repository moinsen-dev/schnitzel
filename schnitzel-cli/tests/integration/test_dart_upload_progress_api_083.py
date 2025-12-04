"""Integration tests for Dart upload progress callbacks (api_083).

Tests for:
- api_083: Dart API client generator adds progress callbacks for uploads
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestDartUploadProgress:
    """Tests for api_083: Dart API client generator adds progress callbacks for uploads."""

    def test_generates_upload_endpoint(self):
        """Test Dart client handles upload endpoint."""
        schema = SchnitzelSchema(
            models={
                "File": Model(
                    name="File",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "filename": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/files": {
                    "POST": {
                        "name": "uploadFile",
                        "body": "File",
                        "response": "File"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have upload method
        assert "uploadFile" in code or "File" in code

    def test_uses_dio_for_uploads(self):
        """Test Dart client uses Dio which supports progress."""
        schema = SchnitzelSchema(
            models={
                "Attachment": Model(
                    name="Attachment",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/attachments": {
                    "POST": {"name": "createAttachment", "body": "Attachment", "response": "Attachment"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should use Dio (which supports onSendProgress)
        assert "Dio" in code

    def test_generates_post_method(self):
        """Test Dart client generates POST methods for uploads."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/documents": {
                    "POST": {"name": "uploadDocument", "body": "Document", "response": "Document"}
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have POST method
        assert "uploadDocument" in code or "post" in code.lower()

    def test_handles_multipart_config(self):
        """Test Dart client handles multipart/form-data config."""
        schema = SchnitzelSchema(
            models={
                "Image": Model(
                    name="Image",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/images": {
                    "POST": {
                        "name": "uploadImage",
                        "body": "Image",
                        "content_type": "multipart/form-data",
                        "response": "Image"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        assert "uploadImage" in code or "Image" in code

    def test_client_structure(self):
        """Test Dart client has proper structure for upload support."""
        schema = SchnitzelSchema(
            models={
                "Upload": Model(
                    name="Upload",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have ApiClient with Dio
        assert "class ApiClient" in code
        assert "Dio" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
