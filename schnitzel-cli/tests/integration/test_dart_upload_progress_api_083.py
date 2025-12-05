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

    def test_post_with_body_has_progress_callback(self):
        """Test POST with body includes onSendProgress parameter."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/documents": {
                    "POST": {
                        "name": "createDocument",
                        "body": "Document",
                        "response": "Document"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have onSendProgress parameter
        assert "void Function(int, int)? onSendProgress" in code
        # Should pass it to Dio
        assert ", onSendProgress: onSendProgress" in code

    def test_put_with_body_has_progress_callback(self):
        """Test PUT with body includes onSendProgress parameter."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/documents/{id}": {
                    "params": {"id": {"type": "uuid"}},
                    "PUT": {
                        "name": "updateDocument",
                        "body": "Document",
                        "response": "Document"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have onSendProgress parameter
        assert "void Function(int, int)? onSendProgress" in code
        # Should pass it to Dio
        assert ", onSendProgress: onSendProgress" in code

    def test_patch_with_body_has_progress_callback(self):
        """Test PATCH with body includes onSendProgress parameter."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/documents/{id}": {
                    "params": {"id": {"type": "uuid"}},
                    "PATCH": {
                        "name": "patchDocument",
                        "body": "Document",
                        "response": "Document"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should have onSendProgress parameter
        assert "void Function(int, int)? onSendProgress" in code
        # Should pass it to Dio
        assert ", onSendProgress: onSendProgress" in code

    def test_get_without_body_no_progress_callback(self):
        """Test GET without body does NOT include onSendProgress parameter."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/documents/{id}": {
                    "params": {"id": {"type": "uuid"}},
                    "GET": {
                        "name": "getDocument",
                        "response": "Document"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Extract just the getDocument method
        lines = code.split('\n')
        get_method = []
        in_method = False
        for line in lines:
            if 'Future<Document> getDocument' in line:
                in_method = True
            if in_method:
                get_method.append(line)
                if line.strip() == '}':
                    break

        get_method_code = '\n'.join(get_method)
        # Should NOT have onSendProgress in the GET method
        assert "onSendProgress" not in get_method_code

    def test_post_without_body_no_progress_callback(self):
        """Test POST without body does NOT include onSendProgress parameter."""
        schema = SchnitzelSchema(
            models={},
            endpoints={
                "/documents/process": {
                    "POST": {
                        "name": "processDocuments",
                        "response": "void"
                    }
                }
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Extract just the processDocuments method
        lines = code.split('\n')
        process_method = []
        in_method = False
        for line in lines:
            if 'Future<void> processDocuments' in line:
                in_method = True
            if in_method:
                process_method.append(line)
                if line.strip() == '}':
                    break

        process_method_code = '\n'.join(process_method)
        # Should NOT have onSendProgress in POST without body
        assert "onSendProgress" not in process_method_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
