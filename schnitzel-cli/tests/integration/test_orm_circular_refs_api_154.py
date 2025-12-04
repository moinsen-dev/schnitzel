"""Integration tests for ORM handling circular references (api_154).

Tests for:
- api_154: Unit test: ORM generator handles circular references
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMCircularRefs:
    """Tests for api_154: Unit test: ORM generator handles circular references."""

    def test_bidirectional_relationship(self):
        """Test ORM handles bidirectional relationships."""
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

        # Should generate both relationships
        assert "User" in code
        assert "Post" in code
        assert "relationship" in code

    def test_self_referential_relationship(self):
        """Test ORM handles self-referential relationships."""
        schema = SchnitzelSchema(
            models={
                "Employee": Model(
                    name="Employee",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "manager": Relation(type="belongsTo", model="Employee"),
                        "subordinates": Relation(type="hasMany", model="Employee")
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate self-referential relationships
        assert "Employee" in code
        assert "relationship" in code

    def test_multiple_circular_paths(self):
        """Test ORM handles multiple circular relationship paths."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                        "comments": Relation(type="hasMany", model="Comment")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                        "comments": Relation(type="hasMany", model="Comment")
                    }
                ),
                "Comment": Model(
                    name="Comment",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "author": Relation(type="belongsTo", model="User"),
                        "post": Relation(type="belongsTo", model="Post")
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate all models and relationships
        assert "User" in code
        assert "Post" in code
        assert "Comment" in code

    def test_three_way_circular(self):
        """Test ORM handles three-way circular references."""
        schema = SchnitzelSchema(
            models={
                "A": Model(
                    name="A",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "b": Relation(type="belongsTo", model="B")
                    }
                ),
                "B": Model(
                    name="B",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "c": Relation(type="belongsTo", model="C")
                    }
                ),
                "C": Model(
                    name="C",
                    fields={"id": FieldDefinition(type="uuid", primary=True)},
                    relations={
                        "a": Relation(type="belongsTo", model="A")
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate all models
        assert "class A" in code
        assert "class B" in code
        assert "class C" in code

    def test_no_infinite_loop(self):
        """Test ORM doesn't infinite loop on circular refs."""
        import signal

        def handler(signum, frame):
            raise TimeoutError("Generation timed out")

        # Set timeout of 5 seconds
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(5)

        try:
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
                        fields={"id": FieldDefinition(type="uuid", primary=True)},
                        relations={
                            "user": Relation(type="belongsTo", model="User")
                        }
                    )
                }
            )

            generator = SQLAlchemyORMGenerator()
            code = generator.generate(schema)

            # Should complete without timeout
            assert code is not None
        finally:
            signal.alarm(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
