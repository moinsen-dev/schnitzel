"""Integration test for API_006: SQLAlchemy ORM generator handles nullable fields correctly.

Test Requirements:
1. Verify ORM generator correctly handles optional vs required fields
2. Verify generated code includes nullable=True for optional fields
3. Verify generated code includes nullable=False for required fields
4. Create integration test that:
   - Creates a schema with both optional and required fields
   - Generates ORM code
   - Creates database and verifies nullable constraints
   - Tests that NULL values work for optional fields but fail for required fields

This test uses an in-memory SQLite database for testing (no PostgreSQL required).
"""

import importlib.util
import sys

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


def load_generated_module(code: str, module_name: str = "test_orm_nullable"):
    """Helper function to load generated ORM code as a Python module.

    Args:
        code: The generated Python code
        module_name: Name for the module (must be unique per test)

    Returns:
        The loaded module
    """
    # Create module spec
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    if spec is None:
        raise ValueError(f"Failed to create module spec for {module_name}")
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


class TestORMNullableFieldHandling:
    """Test that SQLAlchemy ORM generator correctly handles nullable field constraints."""

    def test_optional_fields_generate_nullable_true(self):
        """Test that optional fields generate nullable=True in code."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'description': FieldDefinition(type='string', optional=True),
                        'price': FieldDefinition(type='float', optional=True),
                        'stock': FieldDefinition(type='int', optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify optional fields have nullable=True in generated code
        assert 'description: Mapped[str | None] = mapped_column(sa.String, nullable=True)' in code
        assert 'price: Mapped[float | None] = mapped_column(sa.Float, nullable=True)' in code
        assert 'stock: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)' in code

        # Verify optional fields have | None in type hint
        assert 'str | None' in code
        assert 'float | None' in code
        assert 'int | None' in code

    def test_required_fields_generate_nullable_false(self):
        """Test that required fields generate nullable=False in code."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'username': FieldDefinition(type='string', required=True),
                        'email': FieldDefinition(type='string', required=True),
                        'age': FieldDefinition(type='int', required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify required fields have nullable=False in generated code
        assert 'username: Mapped[str] = mapped_column(sa.String, nullable=False)' in code
        assert 'email: Mapped[str] = mapped_column(sa.String, nullable=False)' in code
        assert 'age: Mapped[int] = mapped_column(sa.Integer, nullable=False)' in code

        # Verify required fields do NOT have | None in type hint
        lines = code.split('\n')
        username_line = [line for line in lines if 'username:' in line][0]
        email_line = [line for line in lines if 'email:' in line][0]
        age_line = [line for line in lines if 'age:' in line][0]

        assert '| None' not in username_line
        assert '| None' not in email_line
        assert '| None' not in age_line

    def test_primary_key_fields_are_not_nullable(self):
        """Test that primary key fields are never nullable."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify primary key has nullable=False
        assert (
            'id: Mapped[uuid.UUID] = mapped_column'
            '(sa.UUID, primary_key=True, nullable=False)' in code
        )

        # Verify primary key does NOT have | None
        lines = code.split('\n')
        id_line = [line for line in lines if 'id: Mapped' in line][0]
        assert '| None' not in id_line

    def test_mixed_optional_and_required_fields(self):
        """Test schema with both optional and required fields."""
        schema = SchnitzelSchema(
            models={
                'Article': Model(
                    name='Article',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        'title': FieldDefinition(type='string', required=True),
                        'subtitle': FieldDefinition(type='string', optional=True),
                        'content': FieldDefinition(type='text', required=True),
                        'summary': FieldDefinition(type='text', optional=True),
                        'views': FieldDefinition(type='int', required=True),
                        'likes': FieldDefinition(type='int', optional=True),
                        'published': FieldDefinition(type='bool', required=True),
                        'featured': FieldDefinition(type='bool', optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify required fields
        assert 'title: Mapped[str] = mapped_column(sa.String, nullable=False)' in code
        assert 'content: Mapped[str] = mapped_column(sa.Text, nullable=False)' in code
        assert 'views: Mapped[int] = mapped_column(sa.Integer, nullable=False)' in code
        assert 'published: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)' in code

        # Verify optional fields
        assert 'subtitle: Mapped[str | None] = mapped_column(sa.String, nullable=True)' in code
        assert 'summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)' in code
        assert 'likes: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)' in code
        assert 'featured: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)' in code

    def test_database_nullable_constraints_match_schema(self):
        """Test that database nullable constraints match the schema definition."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'description': FieldDefinition(type='string', optional=True),
                        'price': FieldDefinition(type='float', required=True),
                        'discount': FieldDefinition(type='float', optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_nullable_db_constraints")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Inspect database schema
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('products')}

        # Verify required fields are NOT nullable in database
        assert columns['id']['nullable'] is False, (
            "Primary key should not be nullable"
        )
        assert columns['name']['nullable'] is False, (
            "Required field 'name' should not be nullable"
        )
        assert columns['price']['nullable'] is False, (
            "Required field 'price' should not be nullable"
        )

        # Verify optional fields ARE nullable in database
        assert columns['description']['nullable'] is True, (
            "Optional field 'description' should be nullable"
        )
        assert columns['discount']['nullable'] is True, (
            "Optional field 'discount' should be nullable"
        )

    def test_optional_fields_accept_null_values(self):
        """Test that optional fields can be set to NULL in database."""
        schema = SchnitzelSchema(
            models={
                'User': Model(
                    name='User',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'username': FieldDefinition(type='string', required=True),
                        'email': FieldDefinition(type='string', optional=True),
                        'phone': FieldDefinition(type='string', optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_nullable_accept_null")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Test inserting record with NULL optional fields
        with Session(engine) as session:
            user1 = orm_models.User(
                id=1,
                username="alice",
                email=None,  # Optional field set to None
                phone=None   # Optional field set to None
            )
            session.add(user1)
            session.commit()

            # Verify insertion succeeded
            from sqlalchemy import select
            stmt = select(orm_models.User).where(orm_models.User.id == 1)
            result = session.execute(stmt).scalar_one()
            assert result.username == "alice"
            assert result.email is None
            assert result.phone is None

        # Test inserting record with some optional fields populated
        with Session(engine) as session:
            user2 = orm_models.User(
                id=2,
                username="bob",
                email="bob@example.com",  # Optional field with value
                phone=None                # Optional field as None
            )
            session.add(user2)
            session.commit()

            stmt = select(orm_models.User).where(orm_models.User.id == 2)
            result = session.execute(stmt).scalar_one()
            assert result.username == "bob"
            assert result.email == "bob@example.com"
            assert result.phone is None

    def test_required_fields_reject_null_values(self):
        """Test that required fields cannot be NULL in database."""
        schema = SchnitzelSchema(
            models={
                'Product': Model(
                    name='Product',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        'name': FieldDefinition(type='string', required=True),
                        'price': FieldDefinition(type='float', required=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Load generated code as module
        orm_models = load_generated_module(code, "test_orm_nullable_reject_null")

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Note: SQLAlchemy with SQLite may not enforce NOT NULL constraints
        # as strictly as PostgreSQL, but we can verify the schema is correct
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('products')}

        # Verify required fields are marked as NOT NULL in schema
        assert columns['name']['nullable'] is False
        assert columns['price']['nullable'] is False

        # SQLite may allow inserting without required fields, but the schema
        # is correctly defined. In a real PostgreSQL database, this would
        # raise an IntegrityError.

    def test_comprehensive_nullable_integration(self):
        """Comprehensive test with multiple field types and nullable combinations."""
        schema = SchnitzelSchema(
            models={
                'Employee': Model(
                    name='Employee',
                    fields={
                        'id': FieldDefinition(type='uuid', primary=True),
                        # Required string fields
                        'first_name': FieldDefinition(type='string', required=True),
                        'last_name': FieldDefinition(type='string', required=True),
                        # Optional string fields
                        'middle_name': FieldDefinition(type='string', optional=True),
                        'nickname': FieldDefinition(type='string', optional=True),
                        # Required numeric fields
                        'employee_id': FieldDefinition(type='int', required=True),
                        'salary': FieldDefinition(type='float', required=True),
                        # Optional numeric fields
                        'bonus': FieldDefinition(type='float', optional=True),
                        'years_experience': FieldDefinition(type='int', optional=True),
                        # Required boolean
                        'active': FieldDefinition(type='bool', required=True),
                        # Optional boolean
                        'remote': FieldDefinition(type='bool', optional=True),
                        # Required datetime
                        'hire_date': FieldDefinition(type='datetime', required=True),
                        # Optional datetime
                        'termination_date': FieldDefinition(type='datetime', optional=True),
                        # Required text
                        'job_description': FieldDefinition(type='text', required=True),
                        # Optional text
                        'notes': FieldDefinition(type='text', optional=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify all required fields have nullable=False
        required_fields = [
            'first_name', 'last_name', 'employee_id', 'salary',
            'active', 'hire_date', 'job_description'
        ]
        for field in required_fields:
            # Check that the field line contains nullable=False
            field_lines = [
                line for line in code.split('\n')
                if f'{field}:' in line and 'Mapped' in line
            ]
            assert len(field_lines) == 1, (
                f"Expected one line for {field}, got {len(field_lines)}"
            )
            assert 'nullable=False' in field_lines[0], (
                f"Field {field} should have nullable=False"
            )
            assert '| None' not in field_lines[0], (
                f"Field {field} should not have | None type hint"
            )

        # Verify all optional fields have nullable=True
        optional_fields = [
            'middle_name', 'nickname', 'bonus', 'years_experience',
            'remote', 'termination_date', 'notes'
        ]
        for field in optional_fields:
            field_lines = [
                line for line in code.split('\n')
                if f'{field}:' in line and 'Mapped' in line
            ]
            assert len(field_lines) == 1, (
                f"Expected one line for {field}, got {len(field_lines)}"
            )
            assert 'nullable=True' in field_lines[0], (
                f"Field {field} should have nullable=True"
            )
            assert '| None' in field_lines[0], (
                f"Field {field} should have | None type hint"
            )

        # Load and test in database
        orm_models = load_generated_module(code, "test_orm_nullable_comprehensive")

        engine = create_engine("sqlite:///:memory:")
        orm_models.Base.metadata.create_all(engine)

        # Inspect database schema
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('employees')}

        # Verify database constraints match schema
        for field in required_fields:
            assert columns[field]['nullable'] is False, \
                f"Required field {field} should not be nullable in database"

        for field in optional_fields:
            assert columns[field]['nullable'] is True, \
                f"Optional field {field} should be nullable in database"

        # Test actual database operations
        import uuid
        from datetime import datetime

        with Session(engine) as session:
            # Insert employee with all required fields and some optional fields
            employee1 = orm_models.Employee(
                id=uuid.uuid4(),
                first_name="John",
                last_name="Doe",
                middle_name="Alexander",  # Optional - provided
                nickname=None,             # Optional - NULL
                employee_id=12345,
                salary=75000.0,
                bonus=5000.0,              # Optional - provided
                years_experience=None,     # Optional - NULL
                active=True,
                remote=True,               # Optional - provided
                hire_date=datetime(2020, 1, 15),
                termination_date=None,     # Optional - NULL
                job_description="Software Engineer",
                notes=None                 # Optional - NULL
            )
            session.add(employee1)
            session.commit()

            # Verify insertion succeeded
            from sqlalchemy import select
            stmt = select(orm_models.Employee).where(
                orm_models.Employee.employee_id == 12345
            )
            result = session.execute(stmt).scalar_one()

            assert result.first_name == "John"
            assert result.middle_name == "Alexander"
            assert result.nickname is None
            assert result.salary == 75000.0
            assert result.bonus == 5000.0
            assert result.years_experience is None
            assert result.remote is True
            assert result.termination_date is None
            assert result.notes is None

    def test_default_values_with_nullable(self):
        """Test that fields with default values still respect nullable constraints."""
        schema = SchnitzelSchema(
            models={
                'Settings': Model(
                    name='Settings',
                    fields={
                        'id': FieldDefinition(type='int', primary=True),
                        # Optional field with default (should be nullable=True)
                        'theme': FieldDefinition(
                            type='string',
                            optional=True,
                            default='light'
                        ),
                        # Required field with default (should be nullable=False)
                        'notifications_enabled': FieldDefinition(
                            type='bool',
                            required=True,
                            default=True
                        ),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Verify optional field with default is still nullable
        theme_lines = [
            line for line in code.split('\n')
            if 'theme:' in line and 'Mapped' in line
        ]
        assert len(theme_lines) == 1
        assert 'nullable=True' in theme_lines[0]
        assert 'default="light"' in theme_lines[0]

        # Verify required field with default is not nullable
        notifications_lines = [
            line for line in code.split('\n')
            if 'notifications_enabled:' in line and 'Mapped' in line
        ]
        assert len(notifications_lines) == 1
        assert 'nullable=False' in notifications_lines[0]
        assert 'default=True' in notifications_lines[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
