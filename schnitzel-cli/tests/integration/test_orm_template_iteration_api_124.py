"""Integration test for API_124: ORM template correctly iterates over models.

Test Requirements:
1. Create schema with multiple models (User, Post, Comment)
2. Generate ORM models using template
3. Verify each model in schema produces a class
4. Verify field iteration is correct
5. Verify relationship iteration is correct

This test verifies the ORM generator correctly processes all models in a schema,
properly iterating over models, fields, and relationships.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


class TestORMTemplateIteration:
    """Test ORM generator correctly iterates over all models and their components."""

    def test_multiple_models_all_generated(self):
        """Test that all models in schema produce ORM classes."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', required=True, unique=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True),
                        'content': FieldDefinition(type='text', optional=True)
                    }
                ),
                'Comment': Model(
                    name='Comment',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'text': FieldDefinition(type='string', required=True),
                        'created_at': FieldDefinition(type='datetime', auto='create')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all three models are generated
        assert 'class User(Base):' in code
        assert 'class Post(Base):' in code
        assert 'class Comment(Base):' in code

        # Verify table names
        assert '__tablename__ = "users"' in code
        assert '__tablename__ = "posts"' in code
        assert '__tablename__ = "comments"' in code

    def test_field_iteration_preserves_all_fields(self):
        """Test that all fields in each model are generated."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', required=True),
                        'name': FieldDefinition(type='string', required=True),
                        'age': FieldDefinition(type='int', optional=True),
                        'active': FieldDefinition(type='bool', default=True),
                        'created_at': FieldDefinition(type='datetime', auto='create')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all fields are present
        assert 'id: Mapped[uuid.UUID]' in code
        assert 'email: Mapped[str]' in code
        assert 'name: Mapped[str]' in code
        assert 'age: Mapped[int | None]' in code
        assert 'active: Mapped[bool]' in code
        assert 'created_at: Mapped[datetime]' in code

        # Count the number of mapped_column declarations (should be 6)
        field_count = code.count('mapped_column(')
        assert field_count == 6, f"Expected 6 fields, found {field_count}"

    def test_relationship_iteration_all_relationships_generated(self):
        """Test that all relationships on all models are generated."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True)
                    },
                    relations={
                        'posts': Relation(type='hasMany', model='Post'),
                        'comments': Relation(type='hasMany', model='Comment')
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True)
                    },
                    relations={
                        'author': Relation(type='belongsTo', model='User'),
                        'comments': Relation(type='hasMany', model='Comment')
                    }
                ),
                'Comment': Model(
                    name='Comment',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True)
                    },
                    relations={
                        'author': Relation(type='belongsTo', model='User'),
                        'post': Relation(type='belongsTo', model='Post')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify User relationships
        assert 'posts: Mapped[list["Post"]] = relationship(' in code
        assert 'comments: Mapped[list["Comment"]] = relationship(' in code

        # Verify Post relationships
        assert 'author: Mapped["User | None"] = relationship(' in code
        # Note: Post has both author (belongsTo) and comments (hasMany)

        # Verify Comment relationships
        # Comment has author (belongsTo User) and post (belongsTo Post)

        # Count total relationship declarations
        relationship_count = code.count('= relationship(')
        assert relationship_count == 6, f"Expected 6 relationships, found {relationship_count}"

    def test_model_order_independence(self):
        """Test that model generation works regardless of definition order."""
        # Define models in different order
        schema = SchnitzelSchema(
            models={
                'Comment': Model(
                    name='Comment',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={'post': Relation(type='belongsTo', model='Post')}
                ),
                'User': Model(
                    name='User',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={'posts': Relation(type='hasMany', model='Post')}
                ),
                'Post': Model(
                    name='Post',
                    fields={'id': FieldDefinition(type='uuid', primary=True)},
                    relations={
                        'author': Relation(type='belongsTo', model='User'),
                        'comments': Relation(type='hasMany', model='Comment')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # All models should still be generated
        assert 'class User(Base):' in code
        assert 'class Post(Base):' in code
        assert 'class Comment(Base):' in code

        # All relationships should still work
        assert 'post_id: Mapped[uuid.UUID | None]' in code
        assert 'author_id: Mapped[uuid.UUID | None]' in code

    def test_complex_schema_with_many_models(self):
        """Test ORM generation with a larger schema (5+ models)."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', unique=True)
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string')
                    }
                ),
                'Comment': Model(
                    name='Comment',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'text': FieldDefinition(type='string')
                    }
                ),
                'Tag': Model(
                    name='Tag',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', unique=True)
                    }
                ),
                'Category': Model(
                    name='Category',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string')
                    }
                ),
                'Media': Model(
                    name='Media',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'url': FieldDefinition(type='string')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all 6 models are generated
        assert 'class User(Base):' in code
        assert 'class Post(Base):' in code
        assert 'class Comment(Base):' in code
        assert 'class Tag(Base):' in code
        assert 'class Category(Base):' in code
        assert 'class Media(Base):' in code

        # Count class definitions
        class_count = code.count('class ') - 1  # Subtract Base class
        assert class_count == 6, f"Expected 6 model classes, found {class_count}"

    def test_empty_models_dict(self):
        """Test that generator handles empty models dict gracefully."""
        schema = SchnitzelSchema(models={})

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should still have imports and Base class
        assert 'import sqlalchemy as sa' in code
        assert 'class Base(DeclarativeBase):' in code

        # But no model classes
        assert 'class User(Base):' not in code
        assert '__tablename__' not in code

    def test_model_with_no_relationships(self):
        """Test models without relationships are properly generated."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string')
                    },
                    relations=None  # Explicitly no relationships
                ),
                'Settings': Model(
                    name='Settings',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'config': FieldDefinition(type='json')
                    },
                    relations=None
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Both models should be generated
        assert 'class User(Base):' in code
        assert 'class Settings(Base):' in code

        # No relationships should be present
        assert 'relationship(' not in code

    def test_field_attributes_preserved_across_models(self):
        """Test that field attributes are correctly preserved for each model."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', unique=True, index=True)
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', index=True)
                    }
                ),
                'Comment': Model(
                    name='Comment',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'text': FieldDefinition(type='string')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify User.email has unique and index
        user_section = code[code.find('class User(Base):'):code.find('class Post(Base):')]
        assert 'unique=True' in user_section
        assert 'index=True' in user_section

        # Verify Post.title has index
        post_section = code[code.find('class Post(Base):'):code.find('class Comment(Base):')]
        assert 'index=True' in post_section

        # Verify Comment.text has neither
        comment_section = code[code.find('class Comment(Base):'): ]
        # Count unique=True in comment section should be 0
        assert 'unique=True' not in comment_section.replace('class Comment(Base):', '').split('\n\n')[0]

    def test_mixed_field_types_across_models(self):
        """Test that different field types work correctly across multiple models."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'created_at': FieldDefinition(type='datetime')
                    }
                ),
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'price': FieldDefinition(type='float'),
                        'quantity': FieldDefinition(type='int')
                    }
                ),
                'Settings': Model(
                    name='Settings',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'config': FieldDefinition(type='json'),
                        'enabled': FieldDefinition(type='bool')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify datetime in User
        assert 'sa.DateTime' in code
        assert 'created_at: Mapped[datetime]' in code

        # Verify numeric types in Product
        assert 'price: Mapped[float]' in code
        assert 'quantity: Mapped[int]' in code
        assert 'sa.Float' in code
        assert 'sa.Integer' in code

        # Verify json and bool in Settings
        assert 'config: Mapped[dict[str, Any]' in code
        assert 'enabled: Mapped[bool]' in code
        assert 'sa.JSON' in code
        assert 'sa.Boolean' in code

    def test_imports_collected_from_all_models(self):
        """Test that imports are correctly collected from all models."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={'created_at': FieldDefinition(type='datetime')}
                ),
                'Product': Model(
                    name='Product',
                    fields={'id': FieldDefinition(type='uuid', primary=True)}
                ),
                'Settings': Model(
                    name='Settings',
                    fields={'config': FieldDefinition(type='json')}
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # All necessary imports should be present
        assert 'from datetime import datetime' in code
        assert 'import uuid' in code
        assert 'from typing import Any' in code
        assert 'import sqlalchemy as sa' in code
        assert 'from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column' in code

    def test_func_import_when_auto_fields_present(self):
        """Test that func is imported when auto fields are used."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'created_at': FieldDefinition(type='datetime', auto='create'),
                        'updated_at': FieldDefinition(type='datetime', auto='update')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # func should be imported when auto fields are present
        assert 'from sqlalchemy import func' in code
        assert 'server_default=func.now()' in code
        assert 'onupdate=func.now()' in code

    def test_no_func_import_without_auto_fields(self):
        """Test that func is not imported when no auto fields are present."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'created_at': FieldDefinition(type='datetime', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # func should NOT be imported when no auto fields are present
        assert 'from sqlalchemy import func' not in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
