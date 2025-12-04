"""Integration tests for relationships loading (api_149).

Tests for:
- api_149: Integration test: Relationships are properly loaded
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestRelationshipsLoaded:
    """Tests for api_149: Integration test: Relationships are properly loaded."""

    def test_belongs_to_relationship(self):
        """Test that belongsTo relationship is generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have relationship
        assert "relationship" in code or "ForeignKey" in code

    def test_has_many_relationship(self):
        """Test that hasMany relationship is generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "posts": Relation(type="hasMany", model="Post")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have relationship
        assert "relationship" in code

    def test_has_one_relationship(self):
        """Test that hasOne relationship is generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "profile": Relation(type="hasOne", model="Profile")
                    }
                ),
                "Profile": Model(
                    name="Profile",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have relationship
        assert "relationship" in code

    def test_many_to_many_relationship(self):
        """Test that manyToMany relationship is generated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "roles": Relation(type="manyToMany", model="Role")
                    }
                ),
                "Role": Model(
                    name="Role",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have relationship or association table
        assert "relationship" in code or "secondary" in code or "Table" in code

    def test_relationship_with_back_populates(self):
        """Test that relationships have back_populates."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "posts": Relation(type="hasMany", model="Post")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have back_populates
        assert "back_populates" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
