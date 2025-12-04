"""Integration test for api_146: End-to-end CRUD operations work.

Test Requirements:
1. Create integration test that generates ORM models for a User entity
2. Test CREATE: Insert a new user into database
3. Test READ: Query user by ID and verify data
4. Test UPDATE: Modify user data and verify changes persist
5. Test DELETE: Remove user and verify deletion
6. Test LIST: Query all users

This test validates that generated SQLAlchemy ORM models work correctly with
a real database, testing the complete CRUD lifecycle.
"""

import importlib.util
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


@pytest.fixture
def user_schema():
    """Create a User model schema for testing."""
    return SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="User in the system",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "username": FieldDefinition(
                        type="string", required=True, unique=True, max_length=50
                    ),
                    "email": FieldDefinition(
                        type="string", required=True, unique=True
                    ),
                    "full_name": FieldDefinition(type="string", required=True),
                    "age": FieldDefinition(type="int", optional=True),
                    "is_active": FieldDefinition(type="bool", default=True),
                    "bio": FieldDefinition(type="text", optional=True),
                    "user_data": FieldDefinition(type="json", optional=True),
                    "created_at": FieldDefinition(type="datetime", auto="create"),
                    "updated_at": FieldDefinition(type="datetime", auto="update"),
                },
            )
        }
    )


@pytest.fixture
def generated_orm_models(user_schema):
    """Generate ORM models from schema and load them as a module."""
    generator = SQLAlchemyORMGenerator()
    code = generator.generate(user_schema)

    # Verify code was generated
    assert code
    assert "class User(Base):" in code
    assert "username: Mapped[str]" in code
    assert "email: Mapped[str]" in code

    # Write generated code to a temporary file and import it as a module
    # This is necessary because SQLAlchemy's annotation resolution requires
    # proper module-level imports when using 'from __future__ import annotations'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_file = Path(f.name)

    try:
        # Import the generated module
        spec = importlib.util.spec_from_file_location("generated_orm", temp_file)
        if spec is None or spec.loader is None:
            raise ImportError("Failed to create module spec")

        module = importlib.util.module_from_spec(spec)
        sys.modules["generated_orm"] = module
        spec.loader.exec_module(module)

        # Return the module's namespace as a dict for easy access
        return {
            "Base": module.Base,
            "User": module.User,
        }
    finally:
        # Clean up temporary file
        temp_file.unlink(missing_ok=True)
        # Clean up imported module
        if "generated_orm" in sys.modules:
            del sys.modules["generated_orm"]


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database engine."""
    # Use SQLite in-memory database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    return engine


@pytest.fixture
def db_session(db_engine, generated_orm_models):
    """Create database tables and return a session."""
    # Get Base class from generated code
    Base = generated_orm_models["Base"]

    # Create all tables
    Base.metadata.create_all(db_engine)

    # Create session
    with Session(db_engine) as session:
        yield session


class TestCRUDOperations:
    """Test complete CRUD operations with generated ORM models."""

    def test_create_user(self, db_session, generated_orm_models):
        """Test CREATE: Insert a new user into database."""
        User = generated_orm_models["User"]

        # Create a new user
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            age=30,
            is_active=True,
            bio="Software developer",
            user_data={"preferences": {"theme": "dark"}},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Add to session and commit
        db_session.add(new_user)
        db_session.commit()

        # Verify user was created
        assert new_user.id == user_id
        assert new_user.username == "johndoe"
        assert new_user.email == "john@example.com"
        assert new_user.full_name == "John Doe"
        assert new_user.age == 30
        assert new_user.is_active is True
        assert new_user.bio == "Software developer"
        assert new_user.user_data == {"preferences": {"theme": "dark"}}
        assert isinstance(new_user.created_at, datetime)
        assert isinstance(new_user.updated_at, datetime)

    def test_read_user_by_id(self, db_session, generated_orm_models):
        """Test READ: Query user by ID and verify data."""
        User = generated_orm_models["User"]

        # Create a user
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="janedoe",
            email="jane@example.com",
            full_name="Jane Doe",
            age=25,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # Query user by ID
        stmt = select(User).where(User.id == user_id)
        result = db_session.execute(stmt)
        retrieved_user = result.scalar_one()

        # Verify retrieved data matches
        assert retrieved_user.id == user_id
        assert retrieved_user.username == "janedoe"
        assert retrieved_user.email == "jane@example.com"
        assert retrieved_user.full_name == "Jane Doe"
        assert retrieved_user.age == 25
        assert retrieved_user.is_active is True

    def test_read_user_by_username(self, db_session, generated_orm_models):
        """Test READ: Query user by unique field (username)."""
        User = generated_orm_models["User"]

        # Create a user
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="bobsmith",
            email="bob@example.com",
            full_name="Bob Smith",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # Query user by username
        stmt = select(User).where(User.username == "bobsmith")
        result = db_session.execute(stmt)
        retrieved_user = result.scalar_one()

        # Verify retrieved data
        assert retrieved_user.username == "bobsmith"
        assert retrieved_user.email == "bob@example.com"
        assert retrieved_user.full_name == "Bob Smith"

    def test_update_user(self, db_session, generated_orm_models):
        """Test UPDATE: Modify user data and verify changes persist."""
        User = generated_orm_models["User"]

        # Create a user
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="alicewonder",
            email="alice@example.com",
            full_name="Alice Wonder",
            age=28,
            is_active=True,
            bio="Designer",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # Update user data
        new_user.full_name = "Alice Wonderland"
        new_user.age = 29
        new_user.bio = "Senior Designer"
        new_user.updated_at = datetime.now()
        db_session.commit()

        # Query user again to verify changes persisted
        stmt = select(User).where(User.id == user_id)
        result = db_session.execute(stmt)
        updated_user = result.scalar_one()

        # Verify updated data
        assert updated_user.full_name == "Alice Wonderland"
        assert updated_user.age == 29
        assert updated_user.bio == "Senior Designer"
        assert updated_user.username == "alicewonder"  # Unchanged
        assert updated_user.email == "alice@example.com"  # Unchanged

    def test_update_optional_fields(self, db_session, generated_orm_models):
        """Test UPDATE: Set and clear optional fields."""
        User = generated_orm_models["User"]

        # Create a user without optional fields
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="charlie",
            email="charlie@example.com",
            full_name="Charlie Brown",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # Verify optional fields are None
        assert new_user.age is None
        assert new_user.bio is None
        assert new_user.user_data is None

        # Set optional fields
        new_user.age = 35
        new_user.bio = "Product Manager"
        new_user.user_data = {"role": "admin"}
        db_session.commit()

        # Verify optional fields are set
        stmt = select(User).where(User.id == user_id)
        result = db_session.execute(stmt)
        updated_user = result.scalar_one()
        assert updated_user.age == 35
        assert updated_user.bio == "Product Manager"
        assert updated_user.user_data == {"role": "admin"}

        # Clear optional fields
        updated_user.age = None
        updated_user.bio = None
        updated_user.user_data = None
        db_session.commit()

        # Verify optional fields are None again
        result = db_session.execute(stmt)
        cleared_user = result.scalar_one()
        assert cleared_user.age is None
        assert cleared_user.bio is None
        assert cleared_user.user_data is None

    def test_delete_user(self, db_session, generated_orm_models):
        """Test DELETE: Remove user and verify deletion."""
        User = generated_orm_models["User"]

        # Create a user
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="davidlee",
            email="david@example.com",
            full_name="David Lee",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # Verify user exists
        stmt = select(User).where(User.id == user_id)
        result = db_session.execute(stmt)
        assert result.scalar_one_or_none() is not None

        # Delete user
        db_session.delete(new_user)
        db_session.commit()

        # Verify user is deleted
        result = db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    def test_list_all_users(self, db_session, generated_orm_models):
        """Test LIST: Query all users."""
        User = generated_orm_models["User"]

        # Create multiple users
        users_data = [
            {
                "id": uuid.uuid4(),
                "username": "user1",
                "email": "user1@example.com",
                "full_name": "User One",
            },
            {
                "id": uuid.uuid4(),
                "username": "user2",
                "email": "user2@example.com",
                "full_name": "User Two",
            },
            {
                "id": uuid.uuid4(),
                "username": "user3",
                "email": "user3@example.com",
                "full_name": "User Three",
            },
        ]

        for user_data in users_data:
            user = User(
                **user_data,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db_session.add(user)
        db_session.commit()

        # Query all users
        stmt = select(User)
        result = db_session.execute(stmt)
        all_users = result.scalars().all()

        # Verify we got all users
        assert len(all_users) == 3
        usernames = {user.username for user in all_users}
        assert usernames == {"user1", "user2", "user3"}

    def test_list_users_with_filter(self, db_session, generated_orm_models):
        """Test LIST: Query users with filter condition."""
        User = generated_orm_models["User"]

        # Create users with different is_active states
        active_user = User(
            id=uuid.uuid4(),
            username="activeuser",
            email="active@example.com",
            full_name="Active User",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        inactive_user = User(
            id=uuid.uuid4(),
            username="inactiveuser",
            email="inactive@example.com",
            full_name="Inactive User",
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(active_user)
        db_session.add(inactive_user)
        db_session.commit()

        # Query only active users
        stmt = select(User).where(User.is_active == True)
        result = db_session.execute(stmt)
        active_users = result.scalars().all()

        # Verify only active user is returned
        assert len(active_users) == 1
        assert active_users[0].username == "activeuser"

        # Query only inactive users
        stmt = select(User).where(User.is_active == False)
        result = db_session.execute(stmt)
        inactive_users = result.scalars().all()

        # Verify only inactive user is returned
        assert len(inactive_users) == 1
        assert inactive_users[0].username == "inactiveuser"

    def test_crud_with_json_field(self, db_session, generated_orm_models):
        """Test CRUD operations with JSON field."""
        User = generated_orm_models["User"]

        # Create user with JSON user_data
        user_id = uuid.uuid4()
        user_data = {
            "preferences": {"theme": "dark", "language": "en"},
            "tags": ["developer", "python", "fullstack"],
            "score": 95.5,
        }
        new_user = User(
            id=user_id,
            username="jsonuser",
            email="json@example.com",
            full_name="JSON User",
            user_data=user_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # Read and verify JSON data
        stmt = select(User).where(User.id == user_id)
        result = db_session.execute(stmt)
        retrieved_user = result.scalar_one()
        assert retrieved_user.user_data == user_data
        assert retrieved_user.user_data["preferences"]["theme"] == "dark"
        assert "python" in retrieved_user.user_data["tags"]

        # Update JSON data
        new_user_data = {
            "preferences": {"theme": "light", "language": "es"},
            "tags": ["developer", "typescript"],
        }
        retrieved_user.user_data = new_user_data
        db_session.commit()

        # Verify updated JSON data
        result = db_session.execute(stmt)
        updated_user = result.scalar_one()
        assert updated_user.user_data == new_user_data
        assert updated_user.user_data["preferences"]["theme"] == "light"

    def test_unique_constraint_enforcement(self, db_session, generated_orm_models):
        """Test that unique constraints are enforced."""
        User = generated_orm_models["User"]

        # Create first user
        user1 = User(
            id=uuid.uuid4(),
            username="uniqueuser",
            email="unique@example.com",
            full_name="Unique User",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(user1)
        db_session.commit()

        # Attempt to create second user with same username
        user2 = User(
            id=uuid.uuid4(),
            username="uniqueuser",  # Duplicate username
            email="different@example.com",
            full_name="Different User",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(user2)

        # Should raise IntegrityError due to unique constraint
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db_session.commit()

        # Rollback the failed transaction
        db_session.rollback()

    def test_full_crud_lifecycle(self, db_session, generated_orm_models):
        """Test complete CRUD lifecycle: Create -> Read -> Update -> Delete."""
        User = generated_orm_models["User"]

        # CREATE
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            username="lifecycle",
            email="lifecycle@example.com",
            full_name="Lifecycle Test",
            age=40,
            is_active=True,
            bio="Testing full lifecycle",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db_session.add(new_user)
        db_session.commit()

        # READ
        stmt = select(User).where(User.id == user_id)
        result = db_session.execute(stmt)
        read_user = result.scalar_one()
        assert read_user.username == "lifecycle"
        assert read_user.age == 40

        # UPDATE
        read_user.age = 41
        read_user.bio = "Updated lifecycle test"
        db_session.commit()

        # Verify UPDATE
        result = db_session.execute(stmt)
        updated_user = result.scalar_one()
        assert updated_user.age == 41
        assert updated_user.bio == "Updated lifecycle test"

        # DELETE
        db_session.delete(updated_user)
        db_session.commit()

        # Verify DELETE
        result = db_session.execute(stmt)
        assert result.scalar_one_or_none() is None
