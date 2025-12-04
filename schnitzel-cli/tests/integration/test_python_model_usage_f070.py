"""Integration test for F070: Generated Python models can be instantiated and serialized.

This test verifies that generated Pydantic models can be:
- Instantiated with valid data
- Serialized to JSON (model_dump_json)
- Deserialized from JSON (model_validate_json)
- Validated with constraints

Test Steps:
1. Generate Python models with PythonModelGenerator
2. Execute generated code in a namespace
3. Instantiate models with valid data
4. Test serialization (model_dump, model_dump_json)
5. Test deserialization (model_validate_json)
6. Test validation (required fields, constraints)
7. Test optional fields
8. Test models with relationships
"""

import json
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


class TestPythonModelInstantiation:
    """Test that generated Python models can be instantiated."""

    def test_model_can_be_instantiated(self):
        """Test F070: Generated model can be instantiated with valid data."""
        # Create a simple User model
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

        # Generate Python code
        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Execute the generated code
        namespace = {}
        exec(generated_code, namespace)

        # Get the User class from the namespace
        User = namespace["User"]

        # Test instantiation with valid data
        test_id = uuid4()
        user = User(
            id=test_id,
            username="john_doe",
            email="john@example.com",
            age=30,
            is_active=True
        )

        # Verify the instance was created successfully
        assert isinstance(user, namespace["BaseModel"]), "User should be a Pydantic BaseModel"
        assert user.id == test_id, "ID should match"
        assert user.username == "john_doe", "Username should match"
        assert user.email == "john@example.com", "Email should match"
        assert user.age == 30, "Age should match"
        assert user.is_active is True, "is_active should match"

        print("\n✓ Model instantiated successfully with valid data")


class TestPythonModelSerialization:
    """Test that generated Python models support serialization."""

    def test_model_serializes_to_json(self):
        """Test F070: model_dump_json works correctly."""
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

        namespace = {}
        exec(generated_code, namespace)

        Product = namespace["Product"]

        # Create a product instance
        test_id = uuid4()
        product = Product(
            id=test_id,
            name="Test Product",
            price=99.99,
            in_stock=True
        )

        # Test model_dump_json()
        json_str = product.model_dump_json()

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

        print("\n✓ Model serializes to JSON successfully")
        print(f"JSON output: {json_str}")

    def test_model_deserializes_from_json(self):
        """Test F070: model_validate_json works correctly."""
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

        namespace = {}
        exec(generated_code, namespace)

        Product = namespace["Product"]

        # Create JSON data
        test_id = str(uuid4())
        json_data = json.dumps({
            "id": test_id,
            "name": "Test Product",
            "price": 99.99,
            "in_stock": True
        })

        # Test model_validate_json()
        product = Product.model_validate_json(json_data)

        # Verify deserialization worked
        assert isinstance(product, Product), "Should create a Product instance"
        assert str(product.id) == test_id, "ID should be deserialized correctly"
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.in_stock is True

        print("\n✓ Model deserializes from JSON successfully")

    def test_model_dump_returns_dict(self):
        """Test F070: model_dump returns dict."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]

        # Create a user instance
        test_id = uuid4()
        user = User(
            id=test_id,
            username="john_doe",
            email="john@example.com"
        )

        # Test model_dump()
        user_dict = user.model_dump()

        # Verify it returns a dict
        assert isinstance(user_dict, dict), "model_dump() should return a dictionary"
        assert user_dict["id"] == test_id, "UUID should be in dict"
        assert user_dict["username"] == "john_doe"
        assert user_dict["email"] == "john@example.com"

        print("\n✓ model_dump returns dict successfully")
        print(f"Dict output: {user_dict}")


class TestPythonModelValidation:
    """Test that generated Python models validate data correctly."""

    def test_model_validates_required_fields(self):
        """Test F070: Missing required field raises validation error."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]
        ValidationError = namespace.get("ValidationError") or namespace["__builtins__"]["__import__"]("pydantic").ValidationError

        # Try to create user without required field
        with pytest.raises(ValidationError) as exc_info:
            User(
                id=uuid4(),
                username="john_doe"
                # Missing required 'email' field
            )

        # Verify the error mentions the missing field
        error_str = str(exc_info.value)
        assert "email" in error_str.lower(), "Error should mention missing 'email' field"

        print("\n✓ Model validates required fields correctly")

    def test_model_validates_constraints(self):
        """Test F070: Min/max constraints are validated."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float", min=0, max=10000),
                        "stock": FieldDefinition(type="int", min=0, max=1000),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Product = namespace["Product"]
        ValidationError = namespace.get("ValidationError") or namespace["__builtins__"]["__import__"]("pydantic").ValidationError

        # Test valid constraints
        product = Product(
            id=uuid4(),
            name="Valid Product",
            price=99.99,
            stock=100
        )
        assert product.price == 99.99
        assert product.stock == 100

        print("\n✓ Valid constraints pass validation")

        # Test price below minimum
        with pytest.raises(ValidationError) as exc_info:
            Product(
                id=uuid4(),
                name="Invalid Product",
                price=-10,  # Below min
                stock=100
            )
        assert "price" in str(exc_info.value).lower()

        print("\n✓ Below-minimum constraint raises validation error")

        # Test price above maximum
        with pytest.raises(ValidationError) as exc_info:
            Product(
                id=uuid4(),
                name="Invalid Product",
                price=20000,  # Above max
                stock=100
            )
        assert "price" in str(exc_info.value).lower()

        print("\n✓ Above-maximum constraint raises validation error")

        # Test stock below minimum
        with pytest.raises(ValidationError) as exc_info:
            Product(
                id=uuid4(),
                name="Invalid Product",
                price=99.99,
                stock=-5  # Below min
            )
        assert "stock" in str(exc_info.value).lower()

        print("\n✓ Integer constraints are validated correctly")

    def test_model_validates_string_length(self):
        """Test F070: max_length constraint is validated."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string", max_length=20),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]
        ValidationError = namespace.get("ValidationError") or namespace["__builtins__"]["__import__"]("pydantic").ValidationError

        # Test valid length
        user = User(
            id=uuid4(),
            username="john_doe"
        )
        assert user.username == "john_doe"

        print("\n✓ Valid string length passes validation")

        # Test string too long
        with pytest.raises(ValidationError) as exc_info:
            User(
                id=uuid4(),
                username="this_username_is_way_too_long_for_the_constraint"
            )
        assert "username" in str(exc_info.value).lower()

        print("\n✓ max_length constraint raises validation error for long strings")


class TestPythonModelOptionalFields:
    """Test that generated Python models handle optional fields correctly."""

    def test_optional_fields_default_to_none(self):
        """Test F070: Optional fields default to None."""
        schema = SchnitzelSchema(
            models={
                "Profile": Model(
                    name="Profile",
                    fields={
                        "username": FieldDefinition(type="string"),
                        "bio": FieldDefinition(type="string", optional=True),
                        "website": FieldDefinition(type="string", optional=True),
                        "age": FieldDefinition(type="int", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Profile = namespace["Profile"]

        # Create profile without optional fields
        profile = Profile(username="john_doe")

        # Verify optional fields default to None
        assert profile.username == "john_doe"
        assert profile.bio is None, "Optional bio should default to None"
        assert profile.website is None, "Optional website should default to None"
        assert profile.age is None, "Optional age should default to None"

        print("\n✓ Optional fields default to None")

        # Create profile with some optional fields set
        profile2 = Profile(
            username="jane_doe",
            bio="Software developer",
            website=None,
            age=28
        )

        assert profile2.username == "jane_doe"
        assert profile2.bio == "Software developer"
        assert profile2.website is None
        assert profile2.age == 28

        print("\n✓ Optional fields can be explicitly set")

    def test_optional_fields_with_defaults(self):
        """Test optional fields with explicit default values."""
        schema = SchnitzelSchema(
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "theme": FieldDefinition(type="string", optional=True, default="light"),
                        "notifications": FieldDefinition(type="bool", optional=True, default=True),
                        "max_items": FieldDefinition(type="int", optional=True, default=10),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        namespace = {}
        exec(generated_code, namespace)

        Settings = namespace["Settings"]

        # Create settings without optional fields
        settings = Settings(id=uuid4())

        # Verify optional fields use their defaults
        assert settings.theme == "light", "Optional theme should default to 'light'"
        assert settings.notifications is True, "Optional notifications should default to True"
        assert settings.max_items == 10, "Optional max_items should default to 10"

        print("\n✓ Optional fields use explicit default values")


class TestPythonModelRelationships:
    """Test that generated Python models handle relationships correctly."""

    def test_model_with_relationships(self):
        """Test F070: Related models can be set."""
        # Create schema with User -> Post relationship
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string"),
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
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User",
                            foreign_key="author_id"
                        )
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code with relationships:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        namespace = {}
        exec(generated_code, namespace)

        User = namespace["User"]
        Post = namespace["Post"]

        # Rebuild models to resolve forward references
        # This is required when models have circular relationships
        if hasattr(User, 'model_rebuild'):
            User.model_rebuild(_types_namespace=namespace)
        if hasattr(Post, 'model_rebuild'):
            Post.model_rebuild(_types_namespace=namespace)

        # Create user
        user_id = uuid4()
        user = User(
            id=user_id,
            username="john_doe"
        )

        # Create post with author_id referencing user
        post_id = uuid4()
        post = Post(
            id=post_id,
            title="My First Post",
            content="This is my first blog post!",
            author_id=user_id
        )

        # Verify instances were created
        assert user.id == user_id
        assert user.username == "john_doe"
        assert post.id == post_id
        assert post.title == "My First Post"
        assert post.author_id == user_id

        print("\n✓ Models with relationships can be instantiated")

        # Test serialization of related models
        user_dict = user.model_dump()
        post_dict = post.model_dump()

        assert user_dict["id"] == user_id
        assert post_dict["author_id"] == user_id

        print("\n✓ Models with relationships serialize correctly")


class TestPythonModelComplexScenarios:
    """Test complex scenarios with generated Python models."""

    def test_complex_model_with_all_features(self):
        """Test a complex model with multiple field types and constraints."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", max_length=200),
                        "slug": FieldDefinition(type="string", unique=True),
                        "content": FieldDefinition(type="string"),
                        "excerpt": FieldDefinition(type="string", optional=True),
                        "author_id": FieldDefinition(type="uuid"),
                        "view_count": FieldDefinition(type="int", min=0, default=0),
                        "rating": FieldDefinition(type="float", min=0.0, max=5.0, optional=True),
                        "published": FieldDefinition(type="bool", default=False),
                        "tags": FieldDefinition(type="list<string>"),
                        "metadata": FieldDefinition(type="json", optional=True),
                        "created_at": FieldDefinition(type="datetime"),
                        "updated_at": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated complex model:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        namespace = {}
        exec(generated_code, namespace)

        Article = namespace["Article"]

        # Create complex article instance
        now = datetime.now()
        article_id = uuid4()
        author_id = uuid4()

        article = Article(
            id=article_id,
            title="Understanding Python Pydantic",
            slug="understanding-python-pydantic",
            content="This is a comprehensive guide to Pydantic...",
            excerpt="Learn about Pydantic's validation features",
            author_id=author_id,
            view_count=150,
            rating=4.5,
            published=True,
            tags=["python", "pydantic", "validation"],
            metadata={"editor": "vim", "reading_time": "5 min"},
            created_at=now,
            updated_at=now
        )

        # Verify all fields
        assert article.id == article_id
        assert article.title == "Understanding Python Pydantic"
        assert article.slug == "understanding-python-pydantic"
        assert article.view_count == 150
        assert article.rating == 4.5
        assert article.published is True
        assert article.tags == ["python", "pydantic", "validation"]
        assert article.metadata["editor"] == "vim"

        print("\n✓ Complex model instantiated successfully")

        # Test serialization
        article_json = article.model_dump_json()
        parsed = json.loads(article_json)

        assert parsed["title"] == "Understanding Python Pydantic"
        assert parsed["view_count"] == 150
        assert parsed["rating"] == 4.5
        assert parsed["tags"] == ["python", "pydantic", "validation"]

        print("\n✓ Complex model serializes to JSON")

        # Test deserialization
        article_from_json = Article.model_validate_json(article_json)
        assert article_from_json.title == article.title
        assert article_from_json.view_count == article.view_count
        assert article_from_json.tags == article.tags

        print("\n✓ Complex model deserializes from JSON")

    def test_model_with_enum_field(self):
        """Test model with enum (Literal) field."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
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
        ValidationError = namespace.get("ValidationError") or namespace["__builtins__"]["__import__"]("pydantic").ValidationError

        # Test valid enum value
        task = Task(
            id=uuid4(),
            title="Implement feature",
            status="in_progress"
        )

        assert task.status == "in_progress"

        print("\n✓ Valid enum value accepted")

        # Test invalid enum value
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id=uuid4(),
                title="Invalid task",
                status="invalid_status"
            )

        assert "status" in str(exc_info.value).lower()

        print("\n✓ Invalid enum value raises validation error")


if __name__ == "__main__":
    # Run tests manually for development
    print("\n" + "=" * 80)
    print("Testing F070: Python model usage (instantiation & serialization)")
    print("=" * 80)

    # Instantiation tests
    test_instantiation = TestPythonModelInstantiation()
    test_instantiation.test_model_can_be_instantiated()

    # Serialization tests
    test_serialization = TestPythonModelSerialization()
    test_serialization.test_model_serializes_to_json()
    test_serialization.test_model_deserializes_from_json()
    test_serialization.test_model_dump_returns_dict()

    # Validation tests
    test_validation = TestPythonModelValidation()
    test_validation.test_model_validates_required_fields()
    test_validation.test_model_validates_constraints()
    test_validation.test_model_validates_string_length()

    # Optional fields tests
    test_optional = TestPythonModelOptionalFields()
    test_optional.test_optional_fields_default_to_none()
    test_optional.test_optional_fields_with_defaults()

    # Relationship tests
    test_relationships = TestPythonModelRelationships()
    test_relationships.test_model_with_relationships()

    # Complex scenarios
    test_complex = TestPythonModelComplexScenarios()
    test_complex.test_complex_model_with_all_features()
    test_complex.test_model_with_enum_field()

    print("\n" + "=" * 80)
    print("✓ ALL F070 TESTS PASSED!")
    print("=" * 80)
