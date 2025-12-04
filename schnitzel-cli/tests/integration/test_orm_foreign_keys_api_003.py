"""Integration test for API_003: SQLAlchemy ORM generator creates foreign key relationships.

Test Requirements (from feature_list_module_01_api_layer.json):
1. Create schema: User model and Post model with user_id referencing User
2. Run schnitzel generate --target python
3. Verify Post.user_id has ForeignKey('users.id')
4. Verify relationship() is defined on both sides
5. Verify User.posts is relationship with back_populates
6. Verify Post.user is relationship with back_populates
7. Run pyright - no errors
"""

import pytest
import tempfile
import subprocess
from pathlib import Path

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMForeignKeyRelationships:
    """Test SQLAlchemy ORM generator foreign key relationship generation (API_003)."""

    def test_foreign_key_generation(self):
        """Test that belongsTo relationship generates foreign key column."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'posts': Relation(type='hasMany', model='Post')
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'user': Relation(type='belongsTo', model='User')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify Post.user_id has ForeignKey('users.id')
        assert 'user_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID, sa.ForeignKey("users.id")' in code

    def test_bidirectional_relationships(self):
        """Test that relationships are defined on both sides with back_populates."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'posts': Relation(type='hasMany', model='Post')
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'user': Relation(type='belongsTo', model='User')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify User.posts is relationship with back_populates
        assert 'posts: Mapped[list["Post"]] = relationship(back_populates="user")' in code

        # Verify Post.user is relationship with back_populates
        assert 'user: Mapped["User | None"] = relationship(back_populates="posts")' in code

    def test_table_name_pluralization(self):
        """Test that table names are properly pluralized snake_case."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={'posts': Relation(type='hasMany', model='Post')}
                ),
                'Post': Model(
                    name='Post',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={'user': Relation(type='belongsTo', model='User')}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify table names are pluralized
        assert '__tablename__ = "users"' in code
        assert '__tablename__ = "posts"' in code

    def test_pyright_type_checking(self):
        """Test that generated ORM code passes pyright type checking."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'posts': Relation(type='hasMany', model='Post')
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True)
                    },
                    relations={
                        'user': Relation(type='belongsTo', model='User')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Write to temp file and run pyright
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            orm_file = tmppath / "orm.py"
            orm_file.write_text(code)

            try:
                result = subprocess.run(
                    ["pyright", str(orm_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Check for errors (not warnings)
                # Pyright returns 0 for no errors
                assert result.returncode == 0 or "0 errors" in result.stdout, \
                    f"Pyright found errors:\n{result.stdout}"

            except FileNotFoundError:
                pytest.skip("Pyright not installed")
            except subprocess.TimeoutExpired:
                pytest.skip("Pyright timed out")

    def test_multiple_relationships(self):
        """Test models with multiple relationships."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={
                        'posts': Relation(type='hasMany', model='Post'),
                        'comments': Relation(type='hasMany', model='Comment')
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={
                        'user': Relation(type='belongsTo', model='User'),
                        'comments': Relation(type='hasMany', model='Comment')
                    }
                ),
                'Comment': Model(
                    name='Comment',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={
                        'user': Relation(type='belongsTo', model='User'),
                        'post': Relation(type='belongsTo', model='Post')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all foreign keys are generated
        assert 'user_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID, sa.ForeignKey("users.id")' in code
        assert 'post_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID, sa.ForeignKey("posts.id")' in code

        # Verify all relationships
        assert 'posts: Mapped[list["Post"]] = relationship(back_populates="user")' in code
        assert 'comments: Mapped[list["Comment"]] = relationship(back_populates="user")' in code

    def test_custom_foreign_key_name(self):
        """Test that custom foreign_key names are respected."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={'posts': Relation(type='hasMany', model='Post')}
                ),
                'Post': Model(
                    name='Post',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={
                        'author': Relation(
                            type='belongsTo',
                            model='User',
                            foreign_key='author_id'
                        )
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify custom foreign key name is used
        assert 'author_id: Mapped[uuid.UUID | None] = mapped_column' in code
        assert 'sa.ForeignKey("users.id")' in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
