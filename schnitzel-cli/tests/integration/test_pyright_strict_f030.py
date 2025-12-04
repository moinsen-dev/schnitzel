"""Integration test for F030: Python model generator produces code that passes pyright strict type checking.

Test Steps:
1. Create schema with complex model: User with relationships, validations, optional fields
2. Call PythonModelGenerator.generate(schema)
3. Save generated code to temp file
4. Run pyright on the file with strict type checking enabled
5. Verify exit code is 0 (no errors)
6. Verify no type errors in output
7. Verify all type hints are correct
"""

import subprocess
import tempfile
import os
from pathlib import Path

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


def test_pyright_strict_basic_types():
    """Test that generated code with basic types passes pyright strict checking."""

    # Step 1: Create schema with various basic field types
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="User model with basic types",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", min=0, max=150),
                    "balance": FieldDefinition(type="float", default=0.0),
                    "is_active": FieldDefinition(type="bool", default=True),
                    "created_at": FieldDefinition(type="datetime"),
                    "metadata": FieldDefinition(type="json", optional=True),
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

    # Step 3: Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(generated_code)
        temp_path = f.name

    try:
        # Step 4: Run pyright with strict mode via config
        temp_dir = Path(temp_path).parent
        config_path = temp_dir / "pyrightconfig.json"
        config_path.write_text('{"typeCheckingMode": "strict"}')

        result = subprocess.run(
            ['pyright', temp_path],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        print("\nPyright output:")
        print(result.stdout)
        if result.stderr:
            print("Stderr:", result.stderr)

        # Step 5: Verify exit code is 0 (no errors)
        assert result.returncode == 0, f"Pyright failed with exit code {result.returncode}\nOutput: {result.stdout}\nErrors: {result.stderr}"

        # Step 6: Verify no type errors
        assert "error" not in result.stdout.lower() or "0 errors" in result.stdout, \
            f"Type errors found in output: {result.stdout}"

        # Step 7: Verify proper type hints exist
        assert "id: UUID" in generated_code
        assert "name: str" in generated_code
        assert "email: str | None" in generated_code
        assert "age: int" in generated_code
        assert "balance: float" in generated_code
        assert "is_active: bool" in generated_code
        assert "created_at: datetime" in generated_code
        assert "metadata: dict[str, Any] | None" in generated_code

    finally:
        # Cleanup
        os.unlink(temp_path)
        if config_path.exists():
            config_path.unlink()


def test_pyright_strict_with_relationships():
    """Test that generated code with relationships passes pyright strict checking."""

    # Create schema with relationships (forward references)
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "username": FieldDefinition(type="string"),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post", foreign_key="author_id"),
                    "profile": Relation(type="hasOne", model="Profile", foreign_key="user_id"),
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                },
                relations={
                    "author": Relation(type="belongsTo", model="User", foreign_key="author_id"),
                }
            ),
            "Profile": Model(
                name="Profile",
                fields={
                    "user_id": FieldDefinition(type="uuid", primary=True),
                    "bio": FieldDefinition(type="string", optional=True),
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

    # Write and test with pyright
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(generated_code)
        temp_path = f.name

    try:
        temp_dir = Path(temp_path).parent
        config_path = temp_dir / "pyrightconfig.json"
        config_path.write_text('{"typeCheckingMode": "strict"}')

        result = subprocess.run(
            ['pyright', temp_path],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        print("\nPyright output:")
        print(result.stdout)
        if result.stderr:
            print("Stderr:", result.stderr)

        # Should pass strict checking
        assert result.returncode == 0, f"Pyright failed with exit code {result.returncode}\nOutput: {result.stdout}"
        assert "error" not in result.stdout.lower() or "0 errors" in result.stdout

        # Verify forward references are handled correctly
        # With __future__ annotations, we shouldn't need quotes
        assert "from __future__ import annotations" in generated_code, \
            "Should include __future__ annotations import for forward references"

    finally:
        os.unlink(temp_path)
        if config_path.exists():
            config_path.unlink()


def test_pyright_strict_comprehensive():
    """Comprehensive test with all field types, validations, and relationships."""

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                description="Comprehensive user model",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "username": FieldDefinition(type="string", unique=True, max_length=50),
                    "email": FieldDefinition(type="string", optional=True, format="email"),
                    "age": FieldDefinition(type="int", min=0, max=150, optional=True),
                    "balance": FieldDefinition(type="float", default=0.0, min=0.0),
                    "is_active": FieldDefinition(type="bool", default=True),
                    "created_at": FieldDefinition(type="datetime", auto="create"),
                    "updated_at": FieldDefinition(type="datetime", auto="update", optional=True),
                    "metadata": FieldDefinition(type="json", optional=True),
                    "tags": FieldDefinition(type="list<string>", optional=True),
                    "friend_ids": FieldDefinition(type="list<uuid>", optional=True),
                    "role": FieldDefinition(
                        type="enum",
                        values=["admin", "user", "guest"],
                        default="user"
                    ),
                    "embedding": FieldDefinition(type="vector", dimensions=384, optional=True),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post", foreign_key="author_id"),
                }
            ),
            "Post": Model(
                name="Post",
                description="Blog post",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "title": FieldDefinition(type="string", max_length=200),
                    "content": FieldDefinition(type="string"),
                    "author_id": FieldDefinition(type="uuid"),
                    "published_at": FieldDefinition(type="datetime", optional=True),
                    "view_count": FieldDefinition(type="int", default=0, min=0),
                    "rating": FieldDefinition(type="float", optional=True, min=0.0, max=5.0),
                },
                relations={
                    "author": Relation(type="belongsTo", model="User", foreign_key="author_id"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nComprehensive generated code:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Write and test with pyright
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(generated_code)
        temp_path = f.name

    try:
        temp_dir = Path(temp_path).parent
        config_path = temp_dir / "pyrightconfig.json"
        config_path.write_text('{"typeCheckingMode": "strict"}')

        result = subprocess.run(
            ['pyright', temp_path],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        print("\nPyright output:")
        print(result.stdout)
        if result.stderr:
            print("Stderr:", result.stderr)

        # Step 5: Verify exit code is 0
        assert result.returncode == 0, f"Pyright strict checking failed\nOutput: {result.stdout}\nStderr: {result.stderr}"

        # Step 6: Verify no errors
        assert "0 errors" in result.stdout, f"Expected 0 errors but got: {result.stdout}"

        # Step 7: Verify all type hints are present and correct
        type_checks = [
            "id: UUID",
            "username: str",
            "email: str | None",
            "age: int | None",
            "balance: float",
            "is_active: bool",
            "created_at: datetime",
            "updated_at: datetime | None",
            "metadata: dict[str, Any] | None",
            "tags: list[str] | None",
            "friend_ids: list[UUID] | None",
            'role: Literal["admin", "user", "guest"]',
            "embedding: list[float] | None",
        ]

        for type_check in type_checks:
            assert type_check in generated_code, f"Expected type hint '{type_check}' not found in generated code"

        # Verify all necessary imports
        required_imports = [
            "from __future__ import annotations",
            "from pydantic import BaseModel",
            "from uuid import UUID",
            "from datetime import datetime",
            "from typing import Any",
            "from typing import Literal",
        ]

        for required_import in required_imports:
            assert required_import in generated_code, f"Expected import '{required_import}' not found"

    finally:
        os.unlink(temp_path)
        if config_path.exists():
            config_path.unlink()


def test_pyright_strict_optional_fields():
    """Test that optional fields with various configurations pass strict checking."""

    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "required_field": FieldDefinition(type="string"),
                    "optional_no_default": FieldDefinition(type="string", optional=True),
                    "optional_with_default": FieldDefinition(type="string", optional=True, default="test"),
                    "optional_with_constraints": FieldDefinition(
                        type="int",
                        optional=True,
                        min=0,
                        max=100,
                        default=50
                    ),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with optional fields:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Test with pyright
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(generated_code)
        temp_path = f.name

    try:
        temp_dir = Path(temp_path).parent
        config_path = temp_dir / "pyrightconfig.json"
        config_path.write_text('{"typeCheckingMode": "strict"}')

        result = subprocess.run(
            ['pyright', temp_path],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        print("\nPyright output:")
        print(result.stdout)

        assert result.returncode == 0, f"Pyright failed: {result.stdout}"
        assert "0 errors" in result.stdout

    finally:
        os.unlink(temp_path)
        if config_path.exists():
            config_path.unlink()


if __name__ == "__main__":
    # Run tests manually for development
    print("\n" + "=" * 80)
    print("F030: Testing Python model generator pyright strict compliance")
    print("=" * 80 + "\n")

    test_pyright_strict_basic_types()
    print("\n✓ Basic types test passed")

    test_pyright_strict_with_relationships()
    print("\n✓ Relationships test passed")

    test_pyright_strict_comprehensive()
    print("\n✓ Comprehensive test passed")

    test_pyright_strict_optional_fields()
    print("\n✓ Optional fields test passed")

    print("\n" + "=" * 80)
    print("✓ All F030 tests passed!")
    print("=" * 80)
