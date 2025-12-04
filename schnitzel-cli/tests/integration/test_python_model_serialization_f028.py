"""Integration test for F028: Python model generator includes model_dump() for JSON serialization.

This test verifies that generated Pydantic models have working model_dump() and model_dump_json()
methods by actually executing the generated code and testing serialization at runtime.

Test Steps:
1. Create User model with basic fields
2. Call PythonModelGenerator.generate(schema)
3. Verify generated code inherits from BaseModel
4. Verify model_dump() is available (Pydantic v2 feature)
5. Verify model_dump_json() is available
6. Write test to instantiate model and call model_dump()
7. Verify serialization works correctly
"""

import json
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


class TestPythonModelSerialization:
    """Test that generated Python models support Pydantic v2 serialization methods."""

    def test_basic_model_has_model_dump(self):
        """Test that generated models have model_dump() method available."""
        # Step 1: Create User model with basic fields
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int"),
                        "is_active": FieldDefinition(type="bool", default=True),
                    }
                )
            }
        )

        # Step 2: Generate Python code
        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Step 3: Verify generated code inherits from BaseModel
        assert "class User(BaseModel):" in generated_code, "Model should inherit from BaseModel"
        assert "from pydantic import BaseModel" in generated_code, "Should import BaseModel"

        # Execute the generated code and test runtime behavior
        namespace = {}
        exec(generated_code, namespace)

        # Get the User class from the namespace
        User = namespace["User"]

        # Create a test instance
        test_id = uuid4()
        user = User(
            id=test_id,
            username="john_doe",
            email="john@example.com",
            age=30,
            is_active=True
        )

        # Step 4: Verify model_dump() is available
        assert hasattr(user, "model_dump"), "Generated model should have model_dump() method"

        # Step 5: Verify model_dump_json() is available
        assert hasattr(user, "model_dump_json"), "Generated model should have model_dump_json() method"

        # Step 6: Call model_dump() and verify it works
        user_dict = user.model_dump()

        # Step 7: Verify serialization works correctly
        assert isinstance(user_dict, dict), "model_dump() should return a dictionary"
        assert user_dict["id"] == test_id, "UUID should be serialized"
        assert user_dict["username"] == "john_doe", "String fields should be serialized"
        assert user_dict["email"] == "john@example.com"
        assert user_dict["age"] == 30, "Integer fields should be serialized"
        assert user_dict["is_active"] is True, "Boolean fields should be serialized"

        print("\nSerialized with model_dump():")
        print(user_dict)

    def test_model_dump_json_produces_valid_json(self):
        """Test that model_dump_json() produces valid JSON string."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                        "in_stock": FieldDefinition(type="bool"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        # Execute the generated code
        namespace = {}
        exec(generated_code, namespace)

        Product = namespace["Product"]

        # Create a test instance
        test_id = uuid4()
        product = Product(
            id=test_id,
            name="Test Product",
            price=99.99,
            in_stock=True
        )

        # Get JSON string
        json_str = product.model_dump_json()

        print("\nSerialized with model_dump_json():")
        print(json_str)

        # Verify it's a valid JSON string
        assert isinstance(json_str, str), "model_dump_json() should return a string"

        # Parse it to verify it's valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict), "JSON should parse to a dictionary"

        # Verify the data
        assert parsed["id"] == str(test_id), "UUID should be serialized as string in JSON"
        assert parsed["name"] == "Test Product"
        assert parsed["price"] == 99.99
        assert parsed["in_stock"] is True

    def test_optional_fields_serialization(self):
        """Test serialization of models with optional fields."""
        schema = SchnitzelSchema(
            models={
                "Profile": Model(
                    name="Profile",
                    fields={
                        "username": FieldDefinition(type="string"),
                        "bio": FieldDefinition(type="string", optional=True),
                        "website": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Profile = namespace["Profile"]

        # Test with some optional fields set
        profile1 = Profile(username="user1", bio="My bio", website=None)
        data1 = profile1.model_dump()

        assert data1["username"] == "user1"
        assert data1["bio"] == "My bio"
        assert data1["website"] is None

        # Test with all optional fields omitted
        profile2 = Profile(username="user2")
        data2 = profile2.model_dump()

        assert data2["username"] == "user2"
        assert data2["bio"] is None
        assert data2["website"] is None

    def test_datetime_serialization(self):
        """Test serialization of datetime fields."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "name": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime"),
                        "updated_at": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Event = namespace["Event"]

        # Create event with datetime
        now = datetime.now()
        event = Event(name="Test Event", created_at=now, updated_at=None)

        # Serialize to dict
        event_dict = event.model_dump()
        assert event_dict["name"] == "Test Event"
        assert event_dict["created_at"] == now
        assert event_dict["updated_at"] is None

        # Serialize to JSON
        event_json = event.model_dump_json()
        parsed = json.loads(event_json)

        # Datetime should be serialized as ISO format string in JSON
        assert isinstance(parsed["created_at"], str)
        assert parsed["name"] == "Test Event"

    def test_list_field_serialization(self):
        """Test serialization of list fields."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "title": FieldDefinition(type="string"),
                        "tags": FieldDefinition(type="list<string>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Post = namespace["Post"]

        post = Post(title="My Post", tags=["python", "pydantic", "serialization"])

        # Serialize to dict
        post_dict = post.model_dump()
        assert post_dict["title"] == "My Post"
        assert post_dict["tags"] == ["python", "pydantic", "serialization"]

        # Serialize to JSON
        post_json = post.model_dump_json()
        parsed = json.loads(post_json)
        assert parsed["tags"] == ["python", "pydantic", "serialization"]

    def test_enum_field_serialization(self):
        """Test serialization of enum (Literal) fields."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "title": FieldDefinition(type="string"),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "in_progress", "completed"]
                        ),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Task = namespace["Task"]

        task = Task(title="Implement feature", status="in_progress")

        # Serialize to dict
        task_dict = task.model_dump()
        assert task_dict["title"] == "Implement feature"
        assert task_dict["status"] == "in_progress"

        # Serialize to JSON
        task_json = task.model_dump_json()
        parsed = json.loads(task_json)
        assert parsed["status"] == "in_progress"

    def test_json_field_serialization(self):
        """Test serialization of json (dict[str, Any]) fields."""
        schema = SchnitzelSchema(
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "name": FieldDefinition(type="string"),
                        "metadata": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Config = namespace["Config"]

        config = Config(
            name="app_config",
            metadata={"version": "1.0", "features": ["auth", "api"], "count": 42}
        )

        # Serialize to dict
        config_dict = config.model_dump()
        assert config_dict["name"] == "app_config"
        assert config_dict["metadata"]["version"] == "1.0"
        assert config_dict["metadata"]["features"] == ["auth", "api"]
        assert config_dict["metadata"]["count"] == 42

        # Serialize to JSON
        config_json = config.model_dump_json()
        parsed = json.loads(config_json)
        assert parsed["metadata"]["version"] == "1.0"

    def test_complex_model_serialization(self):
        """Test serialization of a complex model with multiple field types."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string", max_length=50),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int", min=0, max=150),
                        "score": FieldDefinition(type="float", min=0.0, max=100.0),
                        "is_active": FieldDefinition(type="bool", default=True),
                        "created_at": FieldDefinition(type="datetime"),
                        "tags": FieldDefinition(type="list<string>"),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"]
                        ),
                        "settings": FieldDefinition(type="json"),
                        "bio": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nComplex model generated code:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]

        # Create a complex user instance
        test_id = uuid4()
        now = datetime.now()
        user = User(
            id=test_id,
            username="complex_user",
            email="user@example.com",
            age=25,
            score=87.5,
            is_active=True,
            created_at=now,
            tags=["python", "developer"],
            role="user",
            settings={"theme": "dark", "notifications": True},
            bio="A test user"
        )

        # Test model_dump()
        user_dict = user.model_dump()

        assert user_dict["id"] == test_id
        assert user_dict["username"] == "complex_user"
        assert user_dict["email"] == "user@example.com"
        assert user_dict["age"] == 25
        assert user_dict["score"] == 87.5
        assert user_dict["is_active"] is True
        assert user_dict["created_at"] == now
        assert user_dict["tags"] == ["python", "developer"]
        assert user_dict["role"] == "user"
        assert user_dict["settings"]["theme"] == "dark"
        assert user_dict["bio"] == "A test user"

        print("\nComplex model serialized to dict:")
        print(user_dict)

        # Test model_dump_json()
        user_json = user.model_dump_json()
        parsed = json.loads(user_json)

        assert isinstance(parsed, dict)
        assert parsed["id"] == str(test_id)  # UUID serialized as string in JSON
        assert parsed["username"] == "complex_user"
        assert parsed["age"] == 25
        assert parsed["role"] == "user"

        print("\nComplex model serialized to JSON:")
        print(user_json)

    def test_model_dump_with_exclude(self):
        """Test that model_dump() supports exclude parameter (Pydantic v2 feature)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "username": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "password": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]

        user = User(username="test", email="test@example.com", password="secret")

        # Exclude password from serialization
        user_dict = user.model_dump(exclude={"password"})

        assert "username" in user_dict
        assert "email" in user_dict
        assert "password" not in user_dict

    def test_model_dump_with_include(self):
        """Test that model_dump() supports include parameter (Pydantic v2 feature)."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "username": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "password": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]

        user = User(username="test", email="test@example.com", password="secret")

        # Include only specific fields
        user_dict = user.model_dump(include={"username", "email"})

        assert "username" in user_dict
        assert "email" in user_dict
        assert "password" not in user_dict


if __name__ == "__main__":
    # Run tests manually for development
    test_suite = TestPythonModelSerialization()

    print("\n" + "=" * 80)
    print("Testing F028: Python model serialization with model_dump()")
    print("=" * 80)

    test_suite.test_basic_model_has_model_dump()
    print("\n PASSED: test_basic_model_has_model_dump")

    test_suite.test_model_dump_json_produces_valid_json()
    print("\n PASSED: test_model_dump_json_produces_valid_json")

    test_suite.test_optional_fields_serialization()
    print("\n PASSED: test_optional_fields_serialization")

    test_suite.test_datetime_serialization()
    print("\n PASSED: test_datetime_serialization")

    test_suite.test_list_field_serialization()
    print("\n PASSED: test_list_field_serialization")

    test_suite.test_enum_field_serialization()
    print("\n PASSED: test_enum_field_serialization")

    test_suite.test_json_field_serialization()
    print("\n PASSED: test_json_field_serialization")

    test_suite.test_complex_model_serialization()
    print("\n PASSED: test_complex_model_serialization")

    test_suite.test_model_dump_with_exclude()
    print("\n PASSED: test_model_dump_with_exclude")

    test_suite.test_model_dump_with_include()
    print("\n PASSED: test_model_dump_with_include")

    print("\n" + "=" * 80)
    print(" ALL F028 TESTS PASSED!")
    print("=" * 80)
