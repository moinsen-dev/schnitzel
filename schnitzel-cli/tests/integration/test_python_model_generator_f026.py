"""Integration tests for F026: Python model generator generates belongsTo relationship with type hint.

Test Steps:
1. Create Post model with belongsTo: author referencing User
2. Call PythonModelGenerator.generate(schema)
3. Verify Post model has author_id field with UUID type
4. Verify Post model has author field with Optional['User'] type (forward ref)
5. Verify forward reference is used if User is defined after Post
6. Verify relationship is properly typed
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


class TestPythonModelGeneratorBelongsTo:
    """Test Python model generator for belongsTo relationships."""

    def test_belongsto_generates_relationship_field(self):
        """Test that belongsTo generates a relationship field with forward reference."""
        # Step 1: Create Post model with belongsTo: author referencing User
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User",
                            foreign_key="author_id"
                        )
                    }
                ),
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        # Step 2: Call PythonModelGenerator.generate(schema)
        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Step 3: Verify Post model has author_id field with UUID type
        assert "author_id: UUID" in generated_code, \
            "Post model should have author_id field with UUID type"

        # Step 4: Verify Post model has author field with forward reference type
        # Using __future__ annotations, we don't need quotes: User | None = None
        assert 'author: User | None = None' in generated_code, \
            "Post model should have author field with forward reference User | None = None"

        # Verify UUID import is present
        assert "from uuid import UUID" in generated_code, \
            "UUID import should be present"

    def test_belongsto_uses_forward_reference(self):
        """Test that belongsTo uses string forward reference for type hints."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User"
                        )
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        # Step 5: Verify forward reference is used even if User is not defined
        # With __future__ annotations, types work as forward refs without quotes
        assert 'author: User' in generated_code, \
            "Should use forward reference for User"

        # Verify __future__ import is present for forward reference support
        assert 'from __future__ import annotations' in generated_code, \
            "Should include __future__ annotations import for forward references"

    def test_belongsto_with_multiple_relationships(self):
        """Test model with multiple belongsTo relationships."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "author_id": FieldDefinition(type="uuid"),
                        "category_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User",
                            foreign_key="author_id"
                        ),
                        "category": Relation(
                            type="belongsTo",
                            model="Category",
                            foreign_key="category_id"
                        )
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code with multiple relationships:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Verify both foreign keys
        assert "author_id: UUID" in generated_code
        assert "category_id: UUID" in generated_code

        # Step 6: Verify both relationships are properly typed
        assert 'author: User | None = None' in generated_code
        assert 'category: Category | None = None' in generated_code

    def test_belongsto_relationship_type_format(self):
        """Test that belongsTo relationship uses correct Pydantic v2 type syntax."""
        schema = SchnitzelSchema(
            models={
                "Comment": Model(
                    name="Comment",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "post_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "post": Relation(
                            type="belongsTo",
                            model="Post"
                        )
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        # Should use Pydantic v2 union syntax (| None) not Optional
        assert 'post: Post | None = None' in generated_code, \
            "Should use Pydantic v2 union syntax (| None)"

        # Should NOT use Optional syntax
        assert 'Optional[' not in generated_code or 'from typing import Optional' not in generated_code, \
            "Should not use Optional (Pydantic v2 uses | None)"

        # Should have __future__ import for forward references
        assert 'from __future__ import annotations' in generated_code, \
            "Should include __future__ annotations for forward references"

    def test_belongsto_with_fields_and_relations(self):
        """Test that fields and relations are both generated correctly."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    description="A blog post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", max_length=200),
                        "content": FieldDefinition(type="string"),
                        "author_id": FieldDefinition(type="uuid"),
                        "published": FieldDefinition(type="bool", default=False),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User",
                            foreign_key="author_id"
                        )
                    }
                ),
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code with fields and relations:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Verify class definition
        assert "class Post(BaseModel):" in generated_code
        assert '"""A blog post"""' in generated_code

        # Verify all fields are present
        assert "id: UUID" in generated_code
        assert "title: str = Field(max_length=200)" in generated_code
        assert "content: str" in generated_code
        assert "author_id: UUID" in generated_code
        assert "published: bool = False" in generated_code

        # Verify relationship field
        assert 'author: User | None = None' in generated_code

        # Verify imports
        assert "from __future__ import annotations" in generated_code
        assert "from uuid import UUID" in generated_code
        assert "from pydantic import BaseModel, Field" in generated_code

    def test_generated_code_is_valid_python(self):
        """Test that generated code with belongsTo is valid Python syntax."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User"
                        )
                    }
                ),
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        # Verify the code is valid Python by compiling it
        try:
            compile(generated_code, "<string>", "exec")
            print("\n✓ Generated code is valid Python!")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}\n\nGenerated code:\n{generated_code}")

    def test_belongsto_without_user_model(self):
        """Test that belongsTo works even when referenced model is not in schema."""
        # This tests forward references - the referenced model doesn't need to exist
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User"
                        )
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code without User model:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Should still generate the forward reference
        assert 'author: User | None = None' in generated_code, \
            "Should generate forward reference even if User model doesn't exist in schema"

        # Code should still be valid Python
        try:
            compile(generated_code, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
