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

    def test_detects_n_plus_1_issue_in_endpoint(self):
        """Test that N+1 detection identifies endpoints without eager loading."""
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
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "listUsers",
                        "description": "List all users",
                        "response": {
                            "200": {"type": "list<User>"}
                        }
                    }
                }
            }
        )

        validator = SchemaValidator()
        warnings = validator.detect_n_plus_1_issues(schema)

        # Should detect N+1 issue since User has hasMany posts but endpoint has no include parameter
        assert len(warnings) > 0
        assert "N+1" in warnings[0]
        assert "User" in warnings[0]
        assert "posts" in warnings[0]

    def test_no_n_plus_1_warning_with_eager_loading(self):
        """Test that N+1 detection passes when endpoint has eager loading parameter."""
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
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "listUsers",
                        "description": "List all users",
                        "query": {
                            "include": {"type": "string", "optional": True}
                        },
                        "response": {
                            "200": {"type": "list<User>"}
                        }
                    }
                }
            }
        )

        validator = SchemaValidator()
        warnings = validator.detect_n_plus_1_issues(schema)

        # Should NOT detect N+1 issue since endpoint has include parameter
        assert len(warnings) == 0

    def test_detects_n_plus_1_for_hasone_relations(self):
        """Test that N+1 detection works for hasOne relations too."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={"profile": Relation(type="hasOne", model="Profile")}
                ),
                "Profile": Model(
                    name="Profile",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{id}": {
                    "GET": {
                        "name": "getUser",
                        "description": "Get user by ID",
                        "response": {
                            "200": {"type": "User"}
                        }
                    }
                }
            }
        )

        validator = SchemaValidator()
        warnings = validator.detect_n_plus_1_issues(schema)

        # Should detect N+1 issue for hasOne relation
        assert len(warnings) > 0
        assert "profile" in warnings[0]

    def test_no_warning_for_belongsto_relations(self):
        """Test that belongsTo relations don't trigger N+1 warnings."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={"author": Relation(type="belongsTo", model="User")}
                ),
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/posts": {
                    "GET": {
                        "name": "listPosts",
                        "description": "List all posts",
                        "response": {
                            "200": {"type": "list<Post>"}
                        }
                    }
                }
            }
        )

        validator = SchemaValidator()
        warnings = validator.detect_n_plus_1_issues(schema)

        # Should NOT warn for belongsTo (usually loaded efficiently)
        assert len(warnings) == 0

    def test_detects_n_plus_1_in_paginated_response(self):
        """Test N+1 detection with PaginatedResponse wrapper."""
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
            },
            endpoints={
                "/users": {
                    "GET": {
                        "name": "listUsers",
                        "description": "List all users",
                        "response": {
                            "200": {"type": "PaginatedResponse<User>"}
                        }
                    }
                }
            }
        )

        validator = SchemaValidator()
        warnings = validator.detect_n_plus_1_issues(schema)

        # Should detect N+1 even in wrapped types
        assert len(warnings) > 0
        assert "User" in warnings[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
