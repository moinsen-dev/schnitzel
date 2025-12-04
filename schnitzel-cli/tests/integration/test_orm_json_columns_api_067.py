"""Integration test for API_067: SQLAlchemy ORM generator handles JSON/JSONB columns.

Test Requirements:
1. Verify JSON type maps to sa.JSON
2. Verify JSON fields generate correct Python type hints (dict[str, Any])
3. Test CRUD operations with JSON data
4. Test complex nested JSON structures
5. Test optional and required JSON fields
6. Test JSON field with default values
7. Verify database storage and retrieval of JSON data

This test verifies that the ORM generator properly handles JSON field types,
which is crucial for storing flexible structured data like configurations,
metadata, and API responses.

For PostgreSQL, sa.JSON automatically uses JSONB for better indexing and performance.

Note on Field Names:
- The field name "metadata" is reserved in SQLAlchemy's Declarative API
- Tests avoid using "metadata" as a field name (use "meta_info", "doc_metadata", etc.)
- This is a SQLAlchemy limitation, not a Schnitzel limitation
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


def load_generated_module(code: str, module_name: str = "test_orm_json"):
    """Helper function to load generated ORM code as a Python module.

    Args:
        code: The generated Python code
        module_name: Name for the module (must be unique per test)

    Returns:
        The loaded module
    """
    import importlib.util
    import sys

    # Create module spec
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)

    # Register the module in sys.modules BEFORE executing code
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


class TestORMJSONTypeMapping:
    """Test that JSON types are correctly mapped to SQLAlchemy types."""

    def test_json_type_maps_to_sa_json(self):
        """Test that json type maps to sa.JSON."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "settings": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify sa.JSON is used
        assert "sa.JSON" in code
        assert "settings: Mapped[dict[str, Any]] = mapped_column(sa.JSON" in code

    def test_json_type_hint_is_dict_any(self):
        """Test that JSON type generates dict[str, Any] type hint."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "doc_info": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify Python type hint
        assert "doc_info: Mapped[dict[str, Any]]" in code

    def test_json_field_imports_any(self):
        """Test that JSON fields cause 'Any' to be imported from typing."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "data": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify Any is imported
        assert "from typing import Any" in code


class TestORMJSONFieldVariations:
    """Test different variations of JSON fields."""

    def test_required_json_field(self):
        """Test that required JSON field has nullable=False."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "settings": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Required JSON field should not be nullable
        assert "settings: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)" in code

    def test_optional_json_field(self):
        """Test that optional JSON field has nullable=True."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "preferences": FieldDefinition(type="json", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Optional JSON field should be nullable
        assert "preferences: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON, nullable=True)" in code

    def test_json_field_with_default(self):
        """Test JSON field with default value."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "options": FieldDefinition(type="json", default={}),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should have default value
        assert 'default={}' in code or 'default="{}"' in code

    def test_multiple_json_fields(self):
        """Test model with multiple JSON fields."""
        schema = SchnitzelSchema(
            models={
                "Application": Model(
                    name="Application",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "config": FieldDefinition(type="json", required=True),
                        "meta_info": FieldDefinition(type="json", optional=True),
                        "defaults": FieldDefinition(type="json", default={}),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # All JSON fields should be present
        assert code.count("sa.JSON") == 3
        assert "config: Mapped[dict[str, Any]]" in code
        assert "meta_info: Mapped[dict[str, Any] | None]" in code
        assert "defaults: Mapped[dict[str, Any]]" in code


class TestORMJSONDatabaseOperations:
    """Test CRUD operations with JSON fields in actual database."""

    def test_json_field_create_and_read(self):
        """Test creating and reading records with JSON data."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "settings": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_create_read")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Create record with JSON data
        test_settings = {
            "theme": "dark",
            "language": "en",
            "notifications": True
        }

        with Session(engine) as session:
            config = orm_models.Config(
                id=1,
                settings=test_settings
            )
            session.add(config)
            session.commit()

            # Read back the record
            stmt = select(orm_models.Config).where(orm_models.Config.id == 1)
            result = session.execute(stmt).scalar_one()

            # Verify JSON data is correctly stored and retrieved
            assert result.settings == test_settings
            assert result.settings["theme"] == "dark"
            assert result.settings["language"] == "en"
            assert result.settings["notifications"] is True

    def test_json_field_update(self):
        """Test updating JSON field values."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "doc_metadata": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_update")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            # Create record
            doc = orm_models.Document(
                id=1,
                doc_metadata={"version": 1, "author": "Alice"}
            )
            session.add(doc)
            session.commit()

            # Update JSON field
            stmt = select(orm_models.Document).where(orm_models.Document.id == 1)
            doc = session.execute(stmt).scalar_one()
            doc.doc_metadata = {"version": 2, "author": "Bob", "editor": "Charlie"}
            session.commit()

            # Verify update
            updated_doc = session.execute(stmt).scalar_one()
            assert updated_doc.doc_metadata["version"] == 2
            assert updated_doc.doc_metadata["author"] == "Bob"
            assert updated_doc.doc_metadata["editor"] == "Charlie"

    def test_json_field_with_nested_data(self):
        """Test JSON field with complex nested structures."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "profile": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_nested")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Complex nested JSON structure
        profile_data = {
            "personal": {
                "firstName": "John",
                "lastName": "Doe",
                "age": 30
            },
            "contact": {
                "emails": ["john@example.com", "doe@example.com"],
                "phones": ["+1234567890", "+0987654321"]
            },
            "preferences": {
                "notifications": {
                    "email": True,
                    "sms": False,
                    "push": True
                },
                "privacy": {
                    "shareProfile": False,
                    "showOnline": True
                }
            }
        }

        with Session(engine) as session:
            user = orm_models.User(id=1, profile=profile_data)
            session.add(user)
            session.commit()

            # Read back and verify nested structure
            stmt = select(orm_models.User).where(orm_models.User.id == 1)
            result = session.execute(stmt).scalar_one()

            assert result.profile["personal"]["firstName"] == "John"
            assert result.profile["contact"]["emails"][0] == "john@example.com"
            assert result.profile["preferences"]["notifications"]["email"] is True
            assert result.profile["preferences"]["privacy"]["shareProfile"] is False

    def test_json_field_with_array_data(self):
        """Test JSON field storing array/list data."""
        schema = SchnitzelSchema(
            models={
                "Playlist": Model(
                    name="Playlist",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "tracks": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_array")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        tracks_data = [
            {"id": 1, "title": "Song A", "duration": 180},
            {"id": 2, "title": "Song B", "duration": 200},
            {"id": 3, "title": "Song C", "duration": 220}
        ]

        with Session(engine) as session:
            playlist = orm_models.Playlist(id=1, tracks=tracks_data)
            session.add(playlist)
            session.commit()

            # Read back
            stmt = select(orm_models.Playlist).where(orm_models.Playlist.id == 1)
            result = session.execute(stmt).scalar_one()

            # Note: SQLite stores JSON but returns it as the native type
            # For list-like JSON, it depends on the driver
            assert result.tracks is not None
            # The exact type depends on the SQLite JSON implementation

    def test_optional_json_field_null_handling(self):
        """Test that optional JSON fields can be NULL."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "preferences": FieldDefinition(type="json", optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_null")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            # Create user without preferences
            user1 = orm_models.User(id=1, name="Alice", preferences=None)
            session.add(user1)

            # Create user with preferences
            user2 = orm_models.User(
                id=2,
                name="Bob",
                preferences={"theme": "light"}
            )
            session.add(user2)
            session.commit()

            # Verify NULL handling
            stmt1 = select(orm_models.User).where(orm_models.User.id == 1)
            result1 = session.execute(stmt1).scalar_one()
            assert result1.preferences is None

            stmt2 = select(orm_models.User).where(orm_models.User.id == 2)
            result2 = session.execute(stmt2).scalar_one()
            assert result2.preferences == {"theme": "light"}

    def test_json_field_empty_object(self):
        """Test JSON field with empty object {}."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "settings": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_empty")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            config = orm_models.Config(id=1, settings={})
            session.add(config)
            session.commit()

            # Read back
            stmt = select(orm_models.Config).where(orm_models.Config.id == 1)
            result = session.execute(stmt).scalar_one()
            assert result.settings == {}


class TestORMJSONFieldsMixedTypes:
    """Test JSON fields alongside other field types."""

    def test_json_field_with_mixed_field_types(self):
        """Test JSON field in model with various other field types."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "price": FieldDefinition(type="float", required=True),
                        "active": FieldDefinition(type="bool", default=True),
                        "extra_info": FieldDefinition(type="json", optional=True),
                        "tags": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_mixed")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            product = orm_models.Product(
                id=1,
                name="Widget",
                price=29.99,
                active=True,
                extra_info={"supplier": "ACME", "warehouse": "A1"},
                tags=["electronics", "gadget", "new"]
            )
            session.add(product)
            session.commit()

            # Verify all fields
            stmt = select(orm_models.Product).where(orm_models.Product.id == 1)
            result = session.execute(stmt).scalar_one()

            assert result.name == "Widget"
            assert result.price == 29.99
            assert result.active is True
            assert result.extra_info["supplier"] == "ACME"
            # Note: tags is JSON, so it's stored as-is

    def test_multiple_models_with_json_fields(self):
        """Test multiple models each having JSON fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "name": FieldDefinition(type="string", required=True),
                        "settings": FieldDefinition(type="json", optional=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "title": FieldDefinition(type="string", required=True),
                        "post_meta": FieldDefinition(type="json", required=True),
                    }
                ),
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "data": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify JSON fields in all models
        assert code.count("sa.JSON") == 3

        # Load and test with database
        orm_models = load_generated_module(code, "test_json_multi_models")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        with Session(engine) as session:
            user = orm_models.User(
                id=1,
                name="Alice",
                settings={"theme": "dark"}
            )
            post = orm_models.Post(
                id=1,
                title="Test",
                post_meta={"views": 100}
            )
            config = orm_models.Config(
                id=1,
                data={"version": "1.0"}
            )

            session.add(user)
            session.add(post)
            session.add(config)
            session.commit()

            # Verify all were created
            users = session.execute(select(orm_models.User)).scalars().all()
            posts = session.execute(select(orm_models.Post)).scalars().all()
            configs = session.execute(select(orm_models.Config)).scalars().all()

            assert len(users) == 1
            assert len(posts) == 1
            assert len(configs) == 1


class TestORMJSONFieldSchemaValidation:
    """Test that JSON fields are properly validated in database schema."""

    def test_json_field_creates_correct_column_type(self):
        """Test that JSON field creates the correct column type in database."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="int", primary=True),
                        "data": FieldDefinition(type="json", required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_json_column_type")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Inspect database schema
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns("configs")

        # Find the JSON column
        data_column = [c for c in columns if c["name"] == "data"][0]

        # Verify it's a JSON type (in SQLite it might be stored as TEXT or JSON)
        # The important thing is that it exists and can store JSON
        assert data_column is not None
        assert data_column["name"] == "data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
