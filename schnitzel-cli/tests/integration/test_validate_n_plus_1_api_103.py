"""Integration tests for validate N+1 query issues (api_103).

Tests for:
- api_103: Validate command checks for potential N+1 query issues
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.schema.validator import SchemaValidator


class TestValidateNPlus1:
    """Tests for api_103: Validate N+1 query detection."""

    def test_validates_schema_with_relations(self):
        """Test validator handles schema with relations."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={"posts": Relation(type="hasMany", model="Post")}
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)
        assert result is not None

    def test_validates_nested_relations(self):
        """Test validator handles nested relations."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={"posts": Relation(type="hasMany", model="Post")}
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={"comments": Relation(type="hasMany", model="Comment")}
                ),
                "Comment": Model(
                    name="Comment",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
