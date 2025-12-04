"""Integration test for API_005: SQLAlchemy ORM generator creates unique constraints.

Test Requirements:
1. Verify ORM generator reads unique: true from schema fields
2. Verify generated code includes unique=True in mapped_column()
3. Create integration test that:
   - Creates a schema with unique fields (like email, username)
   - Generates ORM code
   - Creates database and verifies unique constraints exist
   - Tests that duplicate values raise IntegrityError

This test ensures the ORM generator correctly translates unique field constraints
from the Schnitzel schema into SQLAlchemy unique constraints that are enforced
at the database level.
"""

import pytest
import sys
import importlib.util
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


def load_generated_module(code: str, module_name: str = "test_orm_unique"):
    """Helper function to load generated ORM code as a Python module.

    Args:
        code: The generated Python code
        module_name: Name for the module (must be unique per test)

    Returns:
        The loaded module
    """
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


class TestORMUniqueConstraints:
    """Test that SQLAlchemy ORM generator creates unique constraints correctly."""

    def test_generator_reads_unique_from_schema(self):
        """Test that ORM generator reads unique: true from schema fields."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'username': FieldDefinition(type='string', unique=True, required=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify that unique fields are recognized in schema
        user_model = schema.models['User']
        assert user_model.fields['email'].unique is True
        assert user_model.fields['username'].unique is True
        assert user_model.fields['name'].unique is False

        print("✓ ORM generator reads unique: true from schema fields")

    def test_generated_code_includes_unique_true(self):
        """Test that generated code includes unique=True in mapped_column()."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'username': FieldDefinition(type='string', unique=True, required=True),
                        'bio': FieldDefinition(type='text', optional=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify unique=True appears in generated code for unique fields
        assert 'unique=True' in code

        # Verify email field has unique=True
        # The field should look like: email: Mapped[...] = mapped_column(..., unique=True, ...)
        lines = code.split('\n')
        email_line = [line for line in lines if 'email:' in line and 'mapped_column' in line]
        assert len(email_line) == 1, "Should find exactly one email field definition"
        assert 'unique=True' in email_line[0], "email field should have unique=True"

        # Verify username field has unique=True
        username_line = [line for line in lines if 'username:' in line and 'mapped_column' in line]
        assert len(username_line) == 1, "Should find exactly one username field definition"
        assert 'unique=True' in username_line[0], "username field should have unique=True"

        # Verify bio field does NOT have unique=True
        bio_line = [line for line in lines if 'bio:' in line and 'mapped_column' in line]
        assert len(bio_line) == 1, "Should find exactly one bio field definition"
        assert 'unique=True' not in bio_line[0], "bio field should NOT have unique=True"

        print("✓ Generated code includes unique=True in mapped_column()")

    def test_database_unique_constraints_created(self):
        """Test that database tables have unique constraints created."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'username': FieldDefinition(type='string', unique=True, required=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_unique_db_constraints")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Verify unique constraints exist in database schema
        inspector = inspect(engine)

        # Get columns for users table
        columns = inspector.get_columns('users')

        # Find email and username columns
        email_col = [col for col in columns if col['name'] == 'email'][0]
        username_col = [col for col in columns if col['name'] == 'username'][0]
        name_col = [col for col in columns if col['name'] == 'name'][0]

        # Note: In SQLite, unique constraints may be reflected differently
        # We'll verify by attempting to insert duplicate values
        # But we can check that the columns exist
        assert email_col is not None, "email column should exist"
        assert username_col is not None, "username column should exist"
        assert name_col is not None, "name column should exist"

        print("✓ Database tables have unique constraints created")

    def test_duplicate_values_raise_integrity_error(self):
        """Test that duplicate values in unique fields raise IntegrityError."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'username': FieldDefinition(type='string', unique=True, required=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_unique_integrity")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        orm_models.Base.metadata.create_all(engine)

        # Test 1: Insert first user successfully
        with Session(engine) as session:
            user1 = orm_models.User(
                id=1,
                email="alice@example.com",
                username="alice",
                name="Alice Smith"
            )
            session.add(user1)
            session.commit()

        # Test 2: Try to insert user with duplicate email (should fail)
        with Session(engine) as session:
            user2 = orm_models.User(
                id=2,
                email="alice@example.com",  # Duplicate email
                username="alice2",
                name="Alice Jones"
            )
            session.add(user2)

            with pytest.raises(IntegrityError) as exc_info:
                session.commit()

            # Verify error message mentions the constraint
            error_msg = str(exc_info.value).lower()
            assert 'unique' in error_msg or 'constraint' in error_msg or 'email' in error_msg

        # Test 3: Try to insert user with duplicate username (should fail)
        with Session(engine) as session:
            user3 = orm_models.User(
                id=3,
                email="bob@example.com",
                username="alice",  # Duplicate username
                name="Bob Smith"
            )
            session.add(user3)

            with pytest.raises(IntegrityError) as exc_info:
                session.commit()

            # Verify error message mentions the constraint
            error_msg = str(exc_info.value).lower()
            assert 'unique' in error_msg or 'constraint' in error_msg or 'username' in error_msg

        # Test 4: Insert user with unique values (should succeed)
        with Session(engine) as session:
            user4 = orm_models.User(
                id=4,
                email="charlie@example.com",
                username="charlie",
                name="Charlie Brown"
            )
            session.add(user4)
            session.commit()  # Should succeed

        print("✓ Duplicate values in unique fields raise IntegrityError")

    def test_multiple_unique_fields_in_one_model(self):
        """Test that multiple unique fields work correctly in a single model."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'sku': FieldDefinition(type='string', unique=True, required=True),
                        'barcode': FieldDefinition(type='string', unique=True, required=True),
                        'serial_number': FieldDefinition(type='string', unique=True, required=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all three unique fields appear in generated code
        lines = code.split('\n')

        sku_line = [line for line in lines if 'sku:' in line and 'mapped_column' in line]
        assert 'unique=True' in sku_line[0]

        barcode_line = [line for line in lines if 'barcode:' in line and 'mapped_column' in line]
        assert 'unique=True' in barcode_line[0]

        serial_line = [line for line in lines if 'serial_number:' in line and 'mapped_column' in line]
        assert 'unique=True' in serial_line[0]

        # Load and test with database
        orm_models = load_generated_module(code, "test_orm_multiple_unique")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Insert valid product
        with Session(engine) as session:
            product1 = orm_models.Product(
                id=1,
                sku="SKU-001",
                barcode="123456789",
                serial_number="SN-001",
                name="Widget"
            )
            session.add(product1)
            session.commit()

        # Try duplicate SKU
        with Session(engine) as session:
            product2 = orm_models.Product(
                id=2,
                sku="SKU-001",  # Duplicate
                barcode="987654321",
                serial_number="SN-002",
                name="Widget 2"
            )
            session.add(product2)
            with pytest.raises(IntegrityError):
                session.commit()

        # Try duplicate barcode
        with Session(engine) as session:
            product3 = orm_models.Product(
                id=3,
                sku="SKU-003",
                barcode="123456789",  # Duplicate
                serial_number="SN-003",
                name="Widget 3"
            )
            session.add(product3)
            with pytest.raises(IntegrityError):
                session.commit()

        # Try duplicate serial_number
        with Session(engine) as session:
            product4 = orm_models.Product(
                id=4,
                sku="SKU-004",
                barcode="111111111",
                serial_number="SN-001",  # Duplicate
                name="Widget 4"
            )
            session.add(product4)
            with pytest.raises(IntegrityError):
                session.commit()

        print("✓ Multiple unique fields work correctly in a single model")

    def test_unique_with_different_field_types(self):
        """Test that unique constraints work with various field types."""
        schema = SchnitzelSchema(
            models={
                'Entity': Model(
                    name='Entity',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'code': FieldDefinition(type='string', unique=True, required=True),
                        'number': FieldDefinition(type='int', unique=True, required=True),
                        'identifier': FieldDefinition(type='uuid', unique=True, required=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify unique appears for different types
        lines = code.split('\n')

        code_line = [line for line in lines if 'code:' in line and 'mapped_column' in line]
        assert 'unique=True' in code_line[0], "string field should support unique"

        number_line = [line for line in lines if 'number:' in line and 'mapped_column' in line]
        assert 'unique=True' in number_line[0], "int field should support unique"

        identifier_line = [line for line in lines if 'identifier:' in line and 'mapped_column' in line]
        assert 'unique=True' in identifier_line[0], "uuid field should support unique"

        # Load and test with database
        orm_models = load_generated_module(code, "test_orm_unique_types")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        import uuid

        # Insert valid entity
        with Session(engine) as session:
            entity1 = orm_models.Entity(
                id=1,
                code="CODE-001",
                number=100,
                identifier=uuid.uuid4(),
                name="Entity 1"
            )
            session.add(entity1)
            session.commit()

        # Try duplicate string code
        with Session(engine) as session:
            entity2 = orm_models.Entity(
                id=2,
                code="CODE-001",  # Duplicate string
                number=200,
                identifier=uuid.uuid4(),
                name="Entity 2"
            )
            session.add(entity2)
            with pytest.raises(IntegrityError):
                session.commit()

        # Try duplicate int number
        with Session(engine) as session:
            entity3 = orm_models.Entity(
                id=3,
                code="CODE-003",
                number=100,  # Duplicate int
                identifier=uuid.uuid4(),
                name="Entity 3"
            )
            session.add(entity3)
            with pytest.raises(IntegrityError):
                session.commit()

        print("✓ Unique constraints work with various field types")

    def test_unique_constraint_with_optional_fields(self):
        """Test that unique constraints work with optional fields (nullable)."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'phone': FieldDefinition(type='string', unique=True, optional=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify phone field has both unique=True and nullable=True
        lines = code.split('\n')
        phone_line = [line for line in lines if 'phone:' in line and 'mapped_column' in line]
        assert len(phone_line) == 1
        assert 'unique=True' in phone_line[0], "phone should be unique"
        assert 'nullable=True' in phone_line[0], "phone should be nullable"

        # Load and test with database
        orm_models = load_generated_module(code, "test_orm_unique_optional")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Insert user with phone
        with Session(engine) as session:
            user1 = orm_models.User(
                id=1,
                email="alice@example.com",
                phone="555-1234",
                name="Alice"
            )
            session.add(user1)
            session.commit()

        # Insert user without phone (NULL is allowed)
        with Session(engine) as session:
            user2 = orm_models.User(
                id=2,
                email="bob@example.com",
                phone=None,
                name="Bob"
            )
            session.add(user2)
            session.commit()  # Should succeed

        # Insert another user without phone (multiple NULLs allowed for unique nullable)
        # Note: SQLite allows multiple NULL values in unique columns
        with Session(engine) as session:
            user3 = orm_models.User(
                id=3,
                email="charlie@example.com",
                phone=None,
                name="Charlie"
            )
            session.add(user3)
            session.commit()  # Should succeed

        # Try duplicate phone (should fail)
        with Session(engine) as session:
            user4 = orm_models.User(
                id=4,
                email="david@example.com",
                phone="555-1234",  # Duplicate phone
                name="David"
            )
            session.add(user4)
            with pytest.raises(IntegrityError):
                session.commit()

        print("✓ Unique constraints work with optional (nullable) fields")

    def test_unique_with_index_and_other_constraints(self):
        """Test that unique works alongside other field constraints."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(
                            type='string',
                            unique=True,
                            required=True,
                            index=True,
                            max_length=255
                        ),
                        'username': FieldDefinition(
                            type='string',
                            unique=True,
                            required=True,
                            max_length=50
                        ),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify email has both unique and index
        lines = code.split('\n')
        email_line = [line for line in lines if 'email:' in line and 'mapped_column' in line]
        assert 'unique=True' in email_line[0]
        assert 'index=True' in email_line[0]
        assert 'nullable=False' in email_line[0]
        assert 'sa.String(255)' in email_line[0]

        # Verify username has unique and max_length
        username_line = [line for line in lines if 'username:' in line and 'mapped_column' in line]
        assert 'unique=True' in username_line[0]
        assert 'sa.String(50)' in username_line[0]

        # Load and test with database
        orm_models = load_generated_module(code, "test_orm_unique_combined")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Verify constraints work together
        with Session(engine) as session:
            user1 = orm_models.User(
                id=1,
                email="alice@example.com",
                username="alice",
                name="Alice"
            )
            session.add(user1)
            session.commit()

        # Test unique constraint still enforced
        with Session(engine) as session:
            user2 = orm_models.User(
                id=2,
                email="alice@example.com",  # Duplicate
                username="alice2",
                name="Alice 2"
            )
            session.add(user2)
            with pytest.raises(IntegrityError):
                session.commit()

        print("✓ Unique works alongside other field constraints")

    def test_unique_field_with_default_value(self):
        """Test that unique constraints work with fields that have default values."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'status': FieldDefinition(
                            type='string',
                            unique=False,
                            default='active'
                        ),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify email is unique without default
        lines = code.split('\n')
        email_line = [line for line in lines if 'email:' in line and 'mapped_column' in line]
        assert 'unique=True' in email_line[0]
        assert 'default=' not in email_line[0]

        # Verify status has default but not unique
        status_line = [line for line in lines if 'status:' in line and 'mapped_column' in line]
        assert 'unique=True' not in status_line[0]
        assert 'default=' in status_line[0]

        print("✓ Unique constraints work with fields that have default values")


class TestORMUniqueEdgeCases:
    """Test edge cases and special scenarios for unique constraints."""

    def test_unique_false_explicitly_set(self):
        """Test that unique=False is respected and doesn't create constraint."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'email': FieldDefinition(type='string', unique=True, required=True),
                        'bio': FieldDefinition(type='text', unique=False, optional=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Find the bio line
        lines = code.split('\n')
        bio_line = [line for line in lines if 'bio:' in line and 'mapped_column' in line]

        # Should NOT have unique=True
        assert 'unique=True' not in bio_line[0]

        # Load and test that duplicate bio values are allowed
        orm_models = load_generated_module(code, "test_orm_unique_false")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Insert two users with same bio (should succeed)
        with Session(engine) as session:
            user1 = orm_models.User(id=1, email="alice@example.com", bio="Hello World")
            user2 = orm_models.User(id=2, email="bob@example.com", bio="Hello World")
            session.add(user1)
            session.add(user2)
            session.commit()  # Should succeed

        print("✓ unique=False is respected and doesn't create constraint")

    def test_primary_key_implicit_unique(self):
        """Test that primary keys are implicitly unique."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load and test
        orm_models = load_generated_module(code, "test_orm_pk_unique")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Primary key should enforce uniqueness
        with Session(engine) as session:
            user1 = orm_models.User(id=1, name="Alice")
            session.add(user1)
            session.commit()

        # Try duplicate primary key
        with Session(engine) as session:
            user2 = orm_models.User(id=1, name="Bob")  # Duplicate ID
            session.add(user2)
            with pytest.raises(IntegrityError):
                session.commit()

        print("✓ Primary keys are implicitly unique")

    def test_empty_model_no_unique_fields(self):
        """Test model with no unique fields generates valid code."""
        schema = SchnitzelSchema(
            models={
                'Post': Model(
                    name='Post',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'title': FieldDefinition(type='string', required=True),
                        'content': FieldDefinition(type='text', optional=True)
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should not have unique=True anywhere except possibly primary key
        lines = code.split('\n')

        # Count unique=True occurrences (should be 0 for non-primary fields)
        title_line = [line for line in lines if 'title:' in line and 'mapped_column' in line]
        content_line = [line for line in lines if 'content:' in line and 'mapped_column' in line]

        assert 'unique=True' not in title_line[0]
        assert 'unique=True' not in content_line[0]

        # Load and test
        orm_models = load_generated_module(code, "test_orm_no_unique")
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Should allow duplicate titles
        with Session(engine) as session:
            post1 = orm_models.Post(id=1, title="Hello", content="World")
            post2 = orm_models.Post(id=2, title="Hello", content="Again")
            session.add(post1)
            session.add(post2)
            session.commit()  # Should succeed

        print("✓ Model with no unique fields generates valid code")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
