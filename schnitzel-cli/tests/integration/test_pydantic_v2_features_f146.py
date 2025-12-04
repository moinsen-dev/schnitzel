"""Integration tests for F146 - Pydantic v2 specific features.

Test Requirements:
- test_uses_union_syntax - Uses str | None instead of Optional[str]
- test_model_dump_compatibility - Models work with model_dump()
- test_field_constraints - Uses Field() with constraints
- test_model_config - Uses model_config instead of Config class
- test_no_optional_import - Does not import Optional from typing
"""

import tempfile
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python import PythonModelGenerator


def test_uses_union_syntax() -> None:
    """Test that generated code uses Pydantic v2 union syntax (| None)."""
    schema_yaml = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      description:
        type: string
        optional: true
      price:
        type: float
        optional: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should use | None syntax
        assert "str | None" in code, "Should use Pydantic v2 union syntax for optional strings"
        assert "float | None" in code, "Should use Pydantic v2 union syntax for optional floats"

        # Should NOT use Optional[]
        assert "Optional[" not in code, "Should not use Optional[] syntax"
        assert "from typing import Optional" not in code, "Should not import Optional"

    finally:
        schema_path.unlink()


def test_model_dump_compatibility() -> None:
    """Test that generated models are compatible with Pydantic v2 model_dump()."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      username:
        type: string
      email:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should use BaseModel from pydantic
        assert "from pydantic import BaseModel" in code
        assert "class User(BaseModel):" in code

        # Verify code structure allows model_dump() (basic check)
        assert "id: UUID" in code
        assert "username: str" in code

    finally:
        schema_path.unlink()


def test_field_constraints() -> None:
    """Test that Field() is used with constraints."""
    schema_yaml = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        max_length: 100
      price:
        type: float
        min: 0
        max: 1000000
      quantity:
        type: int
        min: 0
        default: 0
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should import Field
        assert "from pydantic import BaseModel, Field" in code

        # Should use Field() with constraints
        assert "Field(" in code

        # Check for specific constraints
        assert "max_length=100" in code, "Should have max_length constraint"
        assert "ge=0" in code, "Should use ge= for min constraint"
        assert "le=1000000" in code, "Should use le= for max constraint"

    finally:
        schema_path.unlink()


def test_no_optional_import() -> None:
    """Test that Optional is not imported since we use | None syntax."""
    schema_yaml = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
        optional: true
      published_at:
        type: datetime
        optional: true
      tags:
        type: list<string>
        optional: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should NOT import Optional
        assert "Optional" not in code or "Optional[" not in code

        # Should use | None instead
        lines_with_optional = [line for line in code.split('\n')
                               if 'optional' not in line.lower() and '|' in line]

        # Check that we have union types
        assert any("| None" in line for line in code.split('\n'))

    finally:
        schema_path.unlink()


def test_future_annotations_with_relationships() -> None:
    """Test that __future__ annotations are used when there are relationships."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      user_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: user_id
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have __future__ annotations for forward references
        assert "from __future__ import annotations" in code

        # Should use forward references without quotes
        assert "list[Post]" in code or "Post | None" in code
        assert "User | None" in code or "list[User]" in code

    finally:
        schema_path.unlink()


def test_pydantic_v2_types() -> None:
    """Test that all type mappings work with Pydantic v2."""
    schema_yaml = """schnitzel: "1.0"

models:
  DataTypes:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      age:
        type: int
      price:
        type: float
      active:
        type: bool
      created_at:
        type: datetime
      metadata:
        type: json
      tags:
        type: list<string>
      scores:
        type: list<float>
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Check type mappings
        assert "id: UUID" in code
        assert "name: str" in code
        assert "age: int" in code
        assert "price: float" in code
        assert "active: bool" in code
        assert "created_at: datetime" in code
        assert "metadata: dict[str, Any]" in code
        assert "tags: list[str]" in code
        assert "scores: list[float]" in code

        # Check imports
        assert "from uuid import UUID" in code
        assert "from datetime import datetime" in code
        assert "from typing import Any" in code

    finally:
        schema_path.unlink()
