"""Integration test for API_004: SQLAlchemy ORM generator creates indexes on fields.

Test Requirements (from feature_list_module_01_api_layer.json):
1. Create schema with fields marked index: true
2. Verify generated ORM code includes index=True in mapped_column()
3. Create database and verify indexes exist using SQLAlchemy inspector
4. Test both single-field and multiple-field index scenarios
5. Verify indexes improve query performance (basic validation)

This test uses an in-memory SQLite database for testing.
"""

import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


def load_generated_module(code: str, module_name: str = "test_orm"):
    """Helper function to load generated ORM code as a Python module.

    Args:
        code: The generated Python code
        module_name: Name for the module (must be unique per test)

    Returns:
        The loaded module
    """
    import importlib.util

    # Create module spec
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)

    # Register the module in sys.modules BEFORE executing code
    # This is necessary for SQLAlchemy to resolve type annotations
    sys.modules[module_name] = module

    try:
        # Execute the code in the module's namespace
        exec(code, module.__dict__)
        return module
    except Exception:
        # Clean up on failure
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise


class TestORMIndexGeneration:
    """Test SQLAlchemy ORM generator index creation (API_004)."""

    def test_index_field_generates_index_true(self):
        """Test that fields marked with index: true generate index=True in mapped_column()."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', required=True, index=True),
                        'username': FieldDefinition(type='string', required=True, index=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify index=True is in the generated code for indexed fields
        assert 'email: Mapped[str] = mapped_column(sa.String, index=True, nullable=False)' in code
        assert 'username: Mapped[str] = mapped_column(sa.String, index=True, nullable=False)' in code

        # Verify name field does NOT have index=True
        lines = code.split('\n')
        name_line = [line for line in lines if 'name: Mapped[str]' in line and 'username' not in line][0]
        assert 'index=True' not in name_line

    def test_index_with_unique_constraint(self):
        """Test that fields with both unique and index generate both constraints."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'sku': FieldDefinition(type='string', unique=True, index=True, required=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify both unique and index are present
        assert 'sku: Mapped[str] = mapped_column(sa.String, unique=True, index=True, nullable=False)' in code

    def test_indexes_created_in_database(self):
        """Test that indexes are actually created in the database schema."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', required=True, index=True),
                        'username': FieldDefinition(type='string', required=True, index=True),
                        'age': FieldDefinition(type='int', optional=True, index=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_indexes_db")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Verify indexes exist using SQLAlchemy inspector
        from sqlalchemy import inspect
        inspector = inspect(engine)

        indexes = inspector.get_indexes('users')

        # Extract index column names
        indexed_columns = set()
        for idx in indexes:
            for col in idx['column_names']:
                indexed_columns.add(col)

        # Verify our indexed fields have indexes
        # Note: Primary keys automatically get indexes, so we check email, username, age
        assert 'email' in indexed_columns, f"email should be indexed. Found indexes: {indexes}"
        assert 'username' in indexed_columns, f"username should be indexed. Found indexes: {indexes}"
        assert 'age' in indexed_columns, f"age should be indexed. Found indexes: {indexes}"

        # Verify non-indexed field does NOT have an index
        # (name should not appear in indexed_columns unless it's part of a composite index)
        name_indexed = 'name' in indexed_columns
        assert not name_indexed, f"name should NOT be indexed. Found indexes: {indexes}"

    def test_optional_field_with_index(self):
        """Test that optional fields can have indexes."""
        schema = SchnitzelSchema(
            models={
                'Article': Model(
                    name='Article',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True),
                        'published_at': FieldDefinition(type='datetime', optional=True, index=True),
                        'tags': FieldDefinition(type='string', optional=True, index=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify optional fields with index have both nullable=True and index=True
        assert 'published_at: Mapped[datetime | None] = mapped_column(sa.DateTime, index=True, nullable=True)' in code
        assert 'tags: Mapped[str | None] = mapped_column(sa.String, index=True, nullable=True)' in code

    def test_multiple_models_with_indexes(self):
        """Test index generation across multiple models.

        Note: Using UUID primary keys because the ORM generator creates UUID foreign keys.
        """
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', required=True, index=True),
                        'username': FieldDefinition(type='string', required=True, index=True)
                    },
                    relations={
                        'posts': Relation(type='hasMany', model='Post')
                    }
                ),
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True, index=True),
                        'slug': FieldDefinition(type='string', required=True, unique=True, index=True),
                        'published': FieldDefinition(type='bool', default=False, index=True)
                    },
                    relations={
                        'user': Relation(type='belongsTo', model='User')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_multi_indexes")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Verify indexes exist on both tables
        from sqlalchemy import inspect
        inspector = inspect(engine)

        # Check User table indexes
        user_indexes = inspector.get_indexes('users')
        user_indexed_cols = set()
        for idx in user_indexes:
            for col in idx['column_names']:
                user_indexed_cols.add(col)

        assert 'email' in user_indexed_cols
        assert 'username' in user_indexed_cols

        # Check Post table indexes
        post_indexes = inspector.get_indexes('posts')
        post_indexed_cols = set()
        for idx in post_indexes:
            for col in idx['column_names']:
                post_indexed_cols.add(col)

        assert 'title' in post_indexed_cols
        assert 'slug' in post_indexed_cols
        assert 'published' in post_indexed_cols

    def test_foreign_key_with_index(self):
        """Test that foreign key columns can also have explicit indexes."""
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
                        'title': FieldDefinition(type='string', required=True, index=True),
                        'content': FieldDefinition(type='text', optional=True)
                    },
                    relations={
                        'user': Relation(type='belongsTo', model='User')
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_fk_index")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Verify foreign key and title index exist
        from sqlalchemy import inspect
        inspector = inspect(engine)

        post_indexes = inspector.get_indexes('posts')
        post_indexed_cols = set()
        for idx in post_indexes:
            for col in idx['column_names']:
                post_indexed_cols.add(col)

        # Title should be indexed
        assert 'title' in post_indexed_cols

        # Note: Foreign keys may or may not be automatically indexed by SQLite
        # The important part is that our explicit index on 'title' works

    def test_index_on_different_field_types(self):
        """Test that indexes work with different field types."""
        schema = SchnitzelSchema(
            models={
                'Analytics': Model(
                    name='Analytics',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'event_name': FieldDefinition(type='string', required=True, index=True),
                        'timestamp': FieldDefinition(type='datetime', required=True, index=True),
                        'user_id': FieldDefinition(type='int', required=True, index=True),
                        'count': FieldDefinition(type='int', default=0, index=True),
                        'active': FieldDefinition(type='bool', default=True, index=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify indexes on different types
        assert 'event_name: Mapped[str] = mapped_column(sa.String, index=True, nullable=False)' in code
        assert 'timestamp: Mapped[datetime] = mapped_column(sa.DateTime, index=True, nullable=False)' in code
        assert 'user_id: Mapped[int] = mapped_column(sa.Integer, index=True, nullable=False)' in code
        # Note: When default is present, nullable is not explicitly added (SQLAlchemy infers it)
        assert 'count: Mapped[int] = mapped_column(sa.Integer, index=True, default=0)' in code
        assert 'active: Mapped[bool] = mapped_column(sa.Boolean, index=True, default=True)' in code

        # Load and verify in database
        orm_models = load_generated_module(code, "test_orm_type_indexes")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        from sqlalchemy import inspect
        inspector = inspect(engine)

        # Note: Analytics pluralizes to "analyticses"
        indexes = inspector.get_indexes('analyticses')
        indexed_columns = set()
        for idx in indexes:
            for col in idx['column_names']:
                indexed_columns.add(col)

        # Verify all indexed fields have indexes
        assert 'event_name' in indexed_columns
        assert 'timestamp' in indexed_columns
        assert 'user_id' in indexed_columns
        assert 'count' in indexed_columns
        assert 'active' in indexed_columns

    def test_no_index_by_default(self):
        """Test that fields without index: true do not get indexes."""
        schema = SchnitzelSchema(
            models={
                'SimpleModel': Model(
                    name='SimpleModel',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'field1': FieldDefinition(type='string', required=True),
                        'field2': FieldDefinition(type='int', optional=True),
                        'field3': FieldDefinition(type='bool', default=False)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Count occurrences of index=True (should only be 0, as no fields have index=True)
        index_count = code.count('index=True')
        assert index_count == 0, f"Expected no indexes, but found {index_count} index=True statements"

    def test_index_with_string_max_length(self):
        """Test that indexed string fields with max_length work correctly."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'sku': FieldDefinition(type='string', max_length=50, required=True, unique=True, index=True),
                        'name': FieldDefinition(type='string', max_length=255, required=True, index=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify max_length and index both present
        assert 'sku: Mapped[str] = mapped_column(sa.String(50), unique=True, index=True, nullable=False)' in code
        assert 'name: Mapped[str] = mapped_column(sa.String(255), index=True, nullable=False)' in code

        # Verify in database
        orm_models = load_generated_module(code, "test_orm_string_index")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        from sqlalchemy import inspect
        inspector = inspect(engine)

        indexes = inspector.get_indexes('products')
        indexed_columns = set()
        for idx in indexes:
            for col in idx['column_names']:
                indexed_columns.add(col)

        assert 'sku' in indexed_columns
        assert 'name' in indexed_columns

    def test_crud_with_indexed_fields(self):
        """Test that CRUD operations work correctly with indexed fields."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', required=True, unique=True, index=True),
                        'username': FieldDefinition(type='string', required=True, index=True),
                        'age': FieldDefinition(type='int', optional=True, index=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_crud_index")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Test CRUD operations
        with Session(engine) as session:
            # CREATE
            user1 = orm_models.User(id=1, email="alice@example.com", username="alice", age=30)
            user2 = orm_models.User(id=2, email="bob@example.com", username="bob", age=25)
            user3 = orm_models.User(id=3, email="charlie@example.com", username="charlie", age=30)
            session.add_all([user1, user2, user3])
            session.commit()

            # READ - Query using indexed fields
            stmt = select(orm_models.User).where(orm_models.User.email == "alice@example.com")
            result = session.execute(stmt).scalar_one()
            assert result.username == "alice"

            # Query by indexed username
            stmt = select(orm_models.User).where(orm_models.User.username == "bob")
            result = session.execute(stmt).scalar_one()
            assert result.email == "bob@example.com"

            # Query by indexed age
            stmt = select(orm_models.User).where(orm_models.User.age == 30)
            results = session.execute(stmt).scalars().all()
            assert len(results) == 2

            # UPDATE
            stmt = select(orm_models.User).where(orm_models.User.username == "alice")
            user = session.execute(stmt).scalar_one()
            user.age = 31
            session.commit()

            # Verify update
            stmt = select(orm_models.User).where(orm_models.User.email == "alice@example.com")
            updated_user = session.execute(stmt).scalar_one()
            assert updated_user.age == 31

            # DELETE
            session.delete(updated_user)
            session.commit()

            # Verify deletion
            stmt = select(orm_models.User).where(orm_models.User.email == "alice@example.com")
            deleted_result = session.execute(stmt).one_or_none()
            assert deleted_result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
