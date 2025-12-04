"""Integration tests for validate command unused model detection (api_100).

Tests for:
- api_100: Validate command checks for unused models
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.schema.validator import UnusedModelDetector


class TestUnusedModelDetection:
    """Tests for api_100: Validate command checks for unused models."""

    def test_detector_exists(self):
        """Test that UnusedModelDetector class exists."""
        detector = UnusedModelDetector()
        assert hasattr(detector, "detect_unused_models")

    def test_detect_unused_model(self):
        """Test detection of a model not used in endpoints or relationships."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "UnusedModel": Model(
                    name="UnusedModel",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            },
            endpoints={
                "/users": {
                    "GET": {
                        "response": {
                            "200": {"type": "list[User]"}
                        }
                    }
                }
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert "UnusedModel" in unused
        assert "User" not in unused

    def test_model_used_in_endpoint_response(self):
        """Test that model used in endpoint response is not flagged."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            },
            endpoints={
                "/products": {
                    "GET": {
                        "response": {
                            "200": {"type": "Product"}
                        }
                    }
                }
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert "Product" not in unused

    def test_model_used_in_list_response(self):
        """Test that model used in list response is detected."""
        schema = SchnitzelSchema(
            models={
                "Item": Model(
                    name="Item",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            },
            endpoints={
                "/items": {
                    "GET": {
                        "response": {
                            "200": {"type": "list[Item]"}
                        }
                    }
                }
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert "Item" not in unused

    def test_model_used_in_relationship(self):
        """Test that model used in relationship is not flagged."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                ),
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        # Both should be used - Post has relation, User is referenced
        assert "Post" not in unused
        assert "User" not in unused

    def test_model_used_in_request_body(self):
        """Test that model used in request body is not flagged."""
        schema = SchnitzelSchema(
            models={
                "CreateUserRequest": Model(
                    name="CreateUserRequest",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                ),
            },
            endpoints={
                "/users": {
                    "POST": {
                        "body": "CreateUserRequest",
                        "response": {
                            "201": {"type": "string"}
                        }
                    }
                }
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert "CreateUserRequest" not in unused

    def test_all_models_unused_without_endpoints(self):
        """Test that all models are unused when no endpoints defined."""
        schema = SchnitzelSchema(
            models={
                "ModelA": Model(
                    name="ModelA",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "ModelB": Model(
                    name="ModelB",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert "ModelA" in unused
        assert "ModelB" in unused

    def test_no_unused_models(self):
        """Test returns empty list when all models are used."""
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

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert len(unused) == 0

    def test_multiple_unused_models(self):
        """Test detection of multiple unused models."""
        schema = SchnitzelSchema(
            models={
                "UsedModel": Model(
                    name="UsedModel",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Unused1": Model(
                    name="Unused1",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Unused2": Model(
                    name="Unused2",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
            },
            endpoints={
                "/used": {
                    "GET": {"response": {"200": {"type": "UsedModel"}}}
                }
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert "Unused1" in unused
        assert "Unused2" in unused
        assert "UsedModel" not in unused

    def test_returns_sorted_list(self):
        """Test that unused models are returned sorted."""
        schema = SchnitzelSchema(
            models={
                "Zebra": Model(name="Zebra", fields={"id": FieldDefinition(type="uuid", primary=True)}),
                "Apple": Model(name="Apple", fields={"id": FieldDefinition(type="uuid", primary=True)}),
                "Mango": Model(name="Mango", fields={"id": FieldDefinition(type="uuid", primary=True)}),
            }
        )

        detector = UnusedModelDetector()
        unused = detector.detect_unused_models(schema)

        assert unused == ["Apple", "Mango", "Zebra"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
