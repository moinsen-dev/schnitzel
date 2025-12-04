"""Integration test for F027: Python model generator generates hasMany relationships.

Test Steps:
1. Create User model with hasMany: posts referencing Post
2. Call PythonModelGenerator.generate(schema)
3. Verify User model has posts field with list['Post'] type
4. Verify list is used (not List from typing - use built-in)
5. Verify forward reference is used correctly
6. Verify hasMany relationships are optional by default (= [])
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


def test_hasmany_relationship_basic():
    """Test basic hasMany relationship generation."""

    # Step 1: Create User model with hasMany posts
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "user_id": FieldDefinition(type="uuid"),
                }
            )
        }
    )

    # Step 2: Generate Python code
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python code:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Step 3: Verify User model has posts field with list[Post] type
    assert 'posts: list[Post]' in generated_code, \
        "User model should have posts field with list[Post] type"

    # Step 4: Verify built-in list is used (not typing.List)
    assert "List[" not in generated_code, \
        "Should use built-in list[], not typing.List[]"
    assert "from typing import List" not in generated_code, \
        "Should not import List from typing"

    # Step 5: Verify forward reference is used correctly with __future__ annotations
    assert 'list[Post]' in generated_code, \
        "Should use forward reference without quotes (using __future__ annotations)"
    assert 'from __future__ import annotations' in generated_code, \
        "Should import annotations from __future__"

    # Step 6: Verify hasMany relationships are optional by default (= [])
    assert 'posts: list[Post] = []' in generated_code, \
        "hasMany relationships should default to empty list"


def test_hasmany_relationship_multiple():
    """Test model with multiple hasMany relationships."""

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    ),
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with multiple hasMany relationships:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify both relationships are generated
    assert 'posts: list[Post] = []' in generated_code, \
        "User should have posts relationship"
    assert 'comments: list[Comment] = []' in generated_code, \
        "User should have comments relationship"


def test_hasmany_with_belongsto():
    """Test that both belongsTo and hasMany relationships are generated."""

    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    ),
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with belongsTo and hasMany:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # hasMany should generate a field
    assert 'comments: list[Comment] = []' in generated_code, \
        "hasMany should generate relationship field"

    # belongsTo also generates a field (bonus feature!)
    assert 'author: User | None = None' in generated_code, \
        "belongsTo generates optional relationship field"


def test_hasmany_comprehensive_example():
    """Test comprehensive example with User -> Posts -> Comments."""

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "content": FieldDefinition(type="string"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    ),
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string"),
                    "post_id": FieldDefinition(type="uuid"),
                    "user_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "post": Relation(
                        type="belongsTo",
                        model="Post",
                        foreign_key="post_id"
                    ),
                    "author": Relation(
                        type="belongsTo",
                        model="User",
                        foreign_key="user_id"
                    )
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nComprehensive generated code:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify User has posts relationship
    assert "class User(BaseModel):" in generated_code
    assert 'posts: list[Post] = []' in generated_code

    # Verify Post has comments relationship
    assert "class Post(BaseModel):" in generated_code
    assert 'comments: list[Comment] = []' in generated_code

    # Verify Comment has belongsTo relationships
    assert "class Comment(BaseModel):" in generated_code
    assert 'post: Post | None = None' in generated_code
    assert 'author: User | None = None' in generated_code


def test_generated_code_is_valid_python():
    """Test that generated code with relationships is valid Python."""

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                },
                relations={
                    "comments": Relation(
                        type="hasMany",
                        model="Comment"
                    )
                }
            ),
            "Comment": Model(
                name="Comment",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "text": FieldDefinition(type="string"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nValidating generated Python code:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify the code is valid Python by compiling it
    try:
        compile(generated_code, "<string>", "exec")
        print("\n✓ Generated code is valid Python!")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")


def test_hasmany_field_ordering():
    """Test that relationship fields appear after regular fields."""

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(
                        type="hasMany",
                        model="Post"
                    )
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
    generated_code = generator.generate(schema)

    # Extract User class
    user_start = generated_code.index("class User(BaseModel):")
    post_start = generated_code.index("class Post(BaseModel):")
    user_class = generated_code[user_start:post_start]

    # Find positions
    id_pos = user_class.index("id: UUID")
    name_pos = user_class.index("name: str")
    email_pos = user_class.index("email: str")
    posts_pos = user_class.index('posts: list[Post]')

    # Verify ordering: regular fields come before relationship fields
    assert id_pos < posts_pos, "id field should come before posts relationship"
    assert name_pos < posts_pos, "name field should come before posts relationship"
    assert email_pos < posts_pos, "email field should come before posts relationship"


if __name__ == "__main__":
    # Run tests manually for development
    test_hasmany_relationship_basic()
    test_hasmany_relationship_multiple()
    test_hasmany_with_belongsto()
    test_hasmany_comprehensive_example()
    test_generated_code_is_valid_python()
    test_hasmany_field_ordering()

    print("\n" + "=" * 80)
    print("✓ All F027 tests passed!")
    print("=" * 80)
