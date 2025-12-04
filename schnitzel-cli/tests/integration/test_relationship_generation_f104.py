"""Integration tests for F104: Integration test for generated code with relationships.

Test Requirements:
- test_belongsto_generates_correctly - verify belongsTo generates proper code
- test_hasmany_generates_correctly - verify hasMany generates proper code
- test_relationship_types - verify relationship types are correct
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python import PythonModelGenerator
from schnitzel.generators.dart.models import DartModelGenerator


class TestPythonRelationshipGeneration:
    """Test Python model generator with relationships."""

    def test_belongsto_generates_correctly(self):
        """Test that belongsTo relationship generates correct Python code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify belongsTo generates optional forward reference
        assert "author: User | None = None" in code
        # Verify __future__ annotations import for forward references
        assert "from __future__ import annotations" in code

    def test_hasmany_generates_correctly(self):
        """Test that hasMany relationship generates correct Python code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify hasMany generates list with default empty list
        assert "posts: list[Post] = []" in code
        # Verify __future__ annotations import
        assert "from __future__ import annotations" in code

    def test_relationship_types(self):
        """Test that different relationship types generate correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                        "profile": Relation(type="belongsTo", model="Profile")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                ),
                "Profile": Model(
                    name="Profile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify all relationships are generated
        assert "posts: list[Post] = []" in code
        assert "profile: Profile | None = None" in code
        assert "author: User | None = None" in code

    def test_bidirectional_relationship(self):
        """Test that bidirectional relationships generate correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify both sides of the relationship
        assert "posts: list[Post] = []" in code
        assert "author: User | None = None" in code

    def test_relationships_without_fields(self):
        """Test models with only relationships and no regular fields."""
        schema = SchnitzelSchema(
            models={
                "Link": Model(
                    name="Link",
                    fields={},
                    relations={
                        "source": Relation(type="belongsTo", model="Node"),
                        "target": Relation(type="belongsTo", model="Node")
                    }
                ),
                "Node": Model(
                    name="Node",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify relationships are generated even without fields
        assert "source: Node | None = None" in code
        assert "target: Node | None = None" in code


class TestDartRelationshipGeneration:
    """Test Dart model generator with relationships."""

    def test_belongsto_generates_correctly(self):
        """Test that belongsTo relationship generates correct Dart code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify belongsTo generates nullable field
        assert "User? author" in code

    def test_hasmany_generates_correctly(self):
        """Test that hasMany relationship generates correct Dart code."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify hasMany generates List type
        assert "List<Post>? posts" in code

    def test_relationship_types(self):
        """Test that different relationship types generate correctly in Dart."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    },
                    relations={
                        "posts": Relation(type="hasMany", model="Post"),
                        "profile": Relation(type="belongsTo", model="Profile")
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                    },
                    relations={
                        "author": Relation(type="belongsTo", model="User")
                    }
                ),
                "Profile": Model(
                    name="Profile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all relationships are generated
        assert "List<Post>? posts" in code
        assert "Profile? profile" in code
        assert "User? author" in code

    def test_dart_relationship_json_key(self):
        """Test that Dart relationships with camelCase names get @JsonKey annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    },
                    relations={
                        "postAuthor": Relation(type="belongsTo", model="User")
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @JsonKey annotation for camelCase relationship
        assert "@JsonKey(name: 'post_author')" in code
        assert "User? postAuthor" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
