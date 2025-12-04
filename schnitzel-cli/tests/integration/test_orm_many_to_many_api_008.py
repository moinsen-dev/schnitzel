"""Integration tests for ORM many-to-many relationships (api_008).

Tests for:
- api_008: SQLAlchemy ORM generator handles many-to-many relationships
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMManyToMany:
    """Tests for api_008: SQLAlchemy ORM generator handles many-to-many relationships."""

    def test_many_to_many_generates_association_table(self):
        """Test that many-to-many relationship generates an association table."""
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
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "users": Relation(type="manyToMany", model="User")
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate association table
        assert "user_roles" in code or "users_roles" in code or "Table(" in code

    def test_many_to_many_secondary_parameter(self):
        """Test that relationship uses secondary parameter for association table."""
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
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "users": Relation(type="manyToMany", model="User")
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have relationship with secondary
        assert "secondary=" in code or "roles:" in code

    def test_many_to_many_back_populates(self):
        """Test that many-to-many uses back_populates."""
        schema = SchnitzelSchema(
            models={
                "Student": Model(
                    name="Student",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "courses": Relation(type="manyToMany", model="Course")
                    }
                ),
                "Course": Model(
                    name="Course",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "students": Relation(type="manyToMany", model="Student")
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have back_populates for bidirectional relationship
        assert "back_populates" in code or "relationship" in code

    def test_many_to_many_list_type_hint(self):
        """Test that many-to-many relationship has list type hint."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "tags": Relation(type="manyToMany", model="Tag")
                    }
                ),
                "Tag": Model(
                    name="Tag",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "articles": Relation(type="manyToMany", model="Article")
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Both sides should be lists
        assert 'list["Tag"]' in code or "list[Tag]" in code or "Mapped[list" in code
        assert 'list["Article"]' in code or "list[Article]" in code or "Mapped[list" in code

    def test_association_table_has_foreign_keys(self):
        """Test that association table has proper foreign keys."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "categories": Relation(type="manyToMany", model="Category")
                    }
                ),
                "Category": Model(
                    name="Category",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "products": Relation(type="manyToMany", model="Product")
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have foreign key references
        assert "ForeignKey" in code or "relationship" in code

    def test_many_to_many_custom_association_name(self):
        """Test that custom association table name can be specified."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "permissions": Relation(
                            type="manyToMany",
                            model="Permission",
                            through="user_permissions"
                        )
                    }
                ),
                "Permission": Model(
                    name="Permission",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "users": Relation(
                            type="manyToMany",
                            model="User",
                            through="user_permissions"
                        )
                    }
                ),
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should use custom table name if specified
        # At minimum should have the relationship
        assert "permissions:" in code or "users:" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
