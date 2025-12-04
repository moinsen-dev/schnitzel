"""Integration tests for validate command missing response type detection (api_101).

Tests for:
- api_101: Validate command checks for missing response types
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import MissingResponseTypeDetector


class TestMissingResponseTypeDetection:
    """Tests for api_101: Validate command checks for missing response types."""

    def test_detector_exists(self):
        """Test that MissingResponseTypeDetector class exists."""
        detector = MissingResponseTypeDetector()
        assert hasattr(detector, "detect_missing_response_types")
        assert hasattr(detector, "detect_undefined_response_types")

    def test_detect_endpoint_without_response(self):
        """Test detection of endpoint without response type."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "list_users"
                        # No response defined
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        missing = detector.detect_missing_response_types(schema)

        assert len(missing) == 1
        assert "GET /users" in missing

    def test_endpoint_with_response_not_flagged(self):
        """Test that endpoint with response is not flagged."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "response": {"200": {"type": "list[User]"}}
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        missing = detector.detect_missing_response_types(schema)

        assert len(missing) == 0

    def test_delete_endpoint_not_flagged(self):
        """Test that DELETE endpoints without response are not flagged."""
        schema = SchnitzelSchema(
            models={},
            endpoints={
                "/users/{id}": {
                    "DELETE": {
                        "name": "delete_user"
                        # No response is fine for DELETE
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        missing = detector.detect_missing_response_types(schema)

        assert len(missing) == 0

    def test_multiple_missing_responses(self):
        """Test detection of multiple endpoints missing responses."""
        schema = SchnitzelSchema(
            models={},
            endpoints={
                "/users": {
                    "GET": {"name": "list_users"},  # Missing
                    "POST": {"name": "create_user"},  # Missing
                },
                "/products": {
                    "GET": {"name": "list_products"},  # Missing
                }
            }
        )

        detector = MissingResponseTypeDetector()
        missing = detector.detect_missing_response_types(schema)

        assert len(missing) == 3
        assert "GET /users" in missing
        assert "POST /users" in missing
        assert "GET /products" in missing

    def test_detect_undefined_response_type(self):
        """Test detection of response type that references undefined model."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/posts": {
                    "GET": {
                        "response": {"200": {"type": "Post"}}  # Post is not defined
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        errors = detector.detect_undefined_response_types(schema)

        assert len(errors) == 1
        assert "Post" in errors[0]
        assert "not defined" in errors[0].lower()

    def test_defined_response_type_not_flagged(self):
        """Test that defined response types are not flagged."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "response": {"200": {"type": "User"}}
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        errors = detector.detect_undefined_response_types(schema)

        assert len(errors) == 0

    def test_primitive_response_type_not_flagged(self):
        """Test that primitive response types are not flagged as undefined."""
        schema = SchnitzelSchema(
            models={},
            endpoints={
                "/health": {
                    "GET": {
                        "response": {"200": {"type": "string"}}
                    }
                },
                "/count": {
                    "GET": {
                        "response": {"200": {"type": "int"}}
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        errors = detector.detect_undefined_response_types(schema)

        assert len(errors) == 0

    def test_list_of_undefined_type(self):
        """Test detection of list[UndefinedModel]."""
        schema = SchnitzelSchema(
            models={},
            endpoints={
                "/items": {
                    "GET": {
                        "response": {"200": {"type": "list[Item]"}}  # Item not defined
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        errors = detector.detect_undefined_response_types(schema)

        assert len(errors) == 1
        assert "Item" in errors[0]

    def test_no_endpoints_returns_empty(self):
        """Test that schema without endpoints returns empty lists."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            }
        )

        detector = MissingResponseTypeDetector()
        missing = detector.detect_missing_response_types(schema)
        undefined = detector.detect_undefined_response_types(schema)

        assert len(missing) == 0
        assert len(undefined) == 0

    def test_string_response_format(self):
        """Test handling of string response format."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "response": {"200": "User"}  # String format
                    }
                }
            }
        )

        detector = MissingResponseTypeDetector()
        missing = detector.detect_missing_response_types(schema)

        assert len(missing) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
