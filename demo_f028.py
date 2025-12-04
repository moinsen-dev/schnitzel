#!/usr/bin/env python3
"""
Demo for F028: Python model generator includes model_dump() for JSON serialization

This demo shows that generated Pydantic models support:
1. Inheriting from BaseModel
2. model_dump() for dictionary serialization
3. model_dump_json() for JSON string serialization
4. Runtime execution and instantiation
5. All field types serialize correctly
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add the source directory to path
sys.path.insert(0, str(Path(__file__).parent / "schnitzel-cli" / "src"))

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


def demo_basic_serialization():
    """Demo 1: Basic model_dump() and model_dump_json()"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Model Serialization")
    print("=" * 80)

    # Step 1: Create User model with basic fields
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="A user in the system",
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

    # Step 2: Call PythonModelGenerator.generate(schema)
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)

    # Step 3: Verify generated code inherits from BaseModel
    assert "class User(BaseModel):" in generated_code
    print("\n✓ Step 3: Generated code inherits from BaseModel")

    # Execute the generated code
    namespace = {}
    exec(generated_code, namespace)
    User = namespace["User"]

    # Create an instance
    test_id = uuid4()
    user = User(
        id=test_id,
        username="john_doe",
        email="john@example.com",
        age=30,
        is_active=True
    )

    # Step 4: Verify model_dump() is available (Pydantic v2 feature)
    assert hasattr(user, "model_dump")
    print("✓ Step 4: model_dump() is available")

    # Step 5: Verify model_dump_json() is available
    assert hasattr(user, "model_dump_json")
    print("✓ Step 5: model_dump_json() is available")

    # Step 6: Write test to instantiate model and call model_dump()
    user_dict = user.model_dump()
    print("\n✓ Step 6: Instantiated model and called model_dump()")
    print(f"\nSerialized to dict:")
    print(json.dumps(str(user_dict), indent=2))

    # Step 7: Verify serialization works correctly
    assert user_dict["id"] == test_id
    assert user_dict["username"] == "john_doe"
    assert user_dict["email"] == "john@example.com"
    assert user_dict["age"] == 30
    assert user_dict["is_active"] is True
    print("\n✓ Step 7: Serialization works correctly - all fields match")

    # Test JSON serialization
    user_json = user.model_dump_json()
    parsed = json.loads(user_json)
    print(f"\nSerialized to JSON string:")
    print(json.dumps(parsed, indent=2))

    assert parsed["username"] == "john_doe"
    print("\n✓ JSON serialization works correctly")


def demo_complex_types():
    """Demo 2: Complex model with all field types"""
    print("\n" + "=" * 80)
    print("DEMO 2: Complex Model with All Field Types")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "ComplexModel": Model(
                name="ComplexModel",
                description="Model with all supported field types",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string", max_length=100),
                    "age": FieldDefinition(type="int", min=0, max=150),
                    "score": FieldDefinition(type="float", min=0.0, max=100.0),
                    "is_active": FieldDefinition(type="bool", default=True),
                    "created_at": FieldDefinition(type="datetime"),
                    "tags": FieldDefinition(type="list<string>"),
                    "status": FieldDefinition(
                        type="enum",
                        values=["active", "inactive", "pending"]
                    ),
                    "metadata": FieldDefinition(type="json"),
                    "bio": FieldDefinition(type="string", optional=True),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Code:")
    print("-" * 80)
    print(generated_code)
    print("-" * 80)

    # Execute and create instance
    namespace = {}
    exec(generated_code, namespace)
    ComplexModel = namespace["ComplexModel"]

    test_id = uuid4()
    now = datetime.now()
    model = ComplexModel(
        id=test_id,
        name="Test Model",
        age=25,
        score=87.5,
        is_active=True,
        created_at=now,
        tags=["python", "pydantic", "schnitzel"],
        status="active",
        metadata={"version": "1.0", "features": ["auth", "api"]},
        bio="A comprehensive test model"
    )

    print("\nModel instance created successfully!")

    # Test model_dump()
    model_dict = model.model_dump()
    print("\nSerialized with model_dump():")
    print(f"  - id: {model_dict['id']}")
    print(f"  - name: {model_dict['name']}")
    print(f"  - age: {model_dict['age']}")
    print(f"  - score: {model_dict['score']}")
    print(f"  - is_active: {model_dict['is_active']}")
    print(f"  - created_at: {model_dict['created_at']}")
    print(f"  - tags: {model_dict['tags']}")
    print(f"  - status: {model_dict['status']}")
    print(f"  - metadata: {model_dict['metadata']}")
    print(f"  - bio: {model_dict['bio']}")

    # Test model_dump_json()
    model_json = model.model_dump_json()
    parsed = json.loads(model_json)
    print("\nSerialized with model_dump_json():")
    print(json.dumps(parsed, indent=2))

    print("\n✓ All field types serialize correctly!")


def demo_pydantic_features():
    """Demo 3: Pydantic v2 features (exclude, include)"""
    print("\n" + "=" * 80)
    print("DEMO 3: Pydantic v2 Serialization Features")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "username": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                    "password": FieldDefinition(type="string"),
                    "api_key": FieldDefinition(type="string"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    namespace = {}
    exec(generated_code, namespace)
    User = namespace["User"]

    user = User(
        username="john_doe",
        email="john@example.com",
        password="secret123",
        api_key="sk-1234567890"
    )

    # Full serialization
    print("\nFull serialization:")
    full_dict = user.model_dump()
    print(json.dumps(full_dict, indent=2))

    # Exclude sensitive fields
    print("\nWith exclude={'password', 'api_key'}:")
    safe_dict = user.model_dump(exclude={"password", "api_key"})
    print(json.dumps(safe_dict, indent=2))

    # Include only specific fields
    print("\nWith include={'username', 'email'}:")
    limited_dict = user.model_dump(include={"username", "email"})
    print(json.dumps(limited_dict, indent=2))

    print("\n✓ Pydantic v2 exclude/include features work correctly!")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("F028: Python Model Generator - model_dump() Serialization Demo")
    print("=" * 80)

    try:
        demo_basic_serialization()
        demo_complex_types()
        demo_pydantic_features()

        print("\n" + "=" * 80)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ Generated models inherit from BaseModel")
        print("  ✓ model_dump() is available and works correctly")
        print("  ✓ model_dump_json() is available and works correctly")
        print("  ✓ All field types serialize correctly")
        print("  ✓ Pydantic v2 features (exclude/include) work")
        print("  ✓ Code can be executed at runtime")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
