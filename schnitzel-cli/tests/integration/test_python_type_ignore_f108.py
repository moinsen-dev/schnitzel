"""Integration tests for F108 - Python generator adds type: ignore comments only when needed.

Test Requirements:
- test_type_ignore_when_needed - type: ignore is added for hasMany relationships with mutable defaults
- test_no_type_ignore_simple - type: ignore is NOT added for simple fields
"""

import tempfile
from pathlib import Path

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.models import PythonModelGenerator


def test_type_ignore_when_needed() -> None:
    """Test that type: ignore is added for hasMany relationships with mutable defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

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
      user:
        type: belongsTo
        model: User
        foreign_key: user_id
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Check that type: ignore is added for hasMany relationships
        assert "posts: list[Post] = []  # type: ignore[assignment]" in code, \
            "hasMany relationship should have type: ignore comment"

        # Check that belongsTo does NOT have type: ignore (None is not mutable)
        assert "user: User | None = None" in code, \
            "belongsTo relationship should not have type: ignore"


def test_no_type_ignore_simple() -> None:
    """Test that type: ignore is NOT added for simple fields without mutable defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        optional: true
      age:
        type: int
        default: 0
      is_active:
        type: bool
        default: true
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Split into lines for easier checking
        lines = code.split("\n")

        # Check that simple fields do NOT have type: ignore
        for line in lines:
            if "id:" in line or "name:" in line or "email:" in line:
                assert "# type: ignore" not in line, \
                    f"Simple field should not have type: ignore: {line}"

            if "age:" in line and "int" in line:
                assert "# type: ignore" not in line, \
                    f"Field with non-mutable default should not have type: ignore: {line}"

            if "is_active:" in line and "bool" in line:
                assert "# type: ignore" not in line, \
                    f"Bool field should not have type: ignore: {line}"


def test_type_ignore_only_hasmany() -> None:
    """Test that type: ignore is only added for hasMany, not belongsTo or simple fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

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
      profile:
        type: belongsTo
        model: Profile

  Post:
    fields:
      id:
        type: uuid

  Profile:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Count type: ignore occurrences
        type_ignore_count = code.count("# type: ignore")

        # Should have exactly 1 type: ignore (for the hasMany relationship)
        assert type_ignore_count == 1, \
            f"Should have exactly 1 type: ignore comment, found {type_ignore_count}"

        # Verify it's on the hasMany line
        assert "posts: list[Post] = []  # type: ignore[assignment]" in code


def test_type_ignore_multiple_hasmany() -> None:
    """Test that type: ignore is added for each hasMany relationship."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
    relations:
      posts:
        type: hasMany
        model: Post
      comments:
        type: hasMany
        model: Comment
      likes:
        type: hasMany
        model: Like

  Post:
    fields:
      id:
        type: uuid

  Comment:
    fields:
      id:
        type: uuid

  Like:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have 3 type: ignore comments (one for each hasMany)
        type_ignore_count = code.count("# type: ignore")
        assert type_ignore_count == 3, \
            f"Should have 3 type: ignore comments (one per hasMany), found {type_ignore_count}"

        # Verify each hasMany has type: ignore
        assert "posts: list[Post] = []  # type: ignore[assignment]" in code
        assert "comments: list[Comment] = []  # type: ignore[assignment]" in code
        assert "likes: list[Like] = []  # type: ignore[assignment]" in code


def test_type_ignore_format() -> None:
    """Test that type: ignore has the correct format with error code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify type: ignore includes error code [assignment]
        assert "# type: ignore[assignment]" in code, \
            "type: ignore should include error code [assignment]"

        # Verify format: two spaces before comment
        assert "[]  # type: ignore[assignment]" in code, \
            "Should have two spaces before type: ignore comment"


def test_no_type_ignore_without_relationships() -> None:
    """Test that models without relationships have no type: ignore comments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
      created_at:
        type: datetime
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have no type: ignore comments
        assert "# type: ignore" not in code, \
            "Model without relationships should not have type: ignore"


def test_type_ignore_with_belongsto_only() -> None:
    """Test that belongsTo relationships do NOT get type: ignore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_file = Path(tmpdir) / "test.yaml"
        schema_file.write_text("""
schnitzel: "1.0.0"

models:
  Post:
    fields:
      id:
        type: uuid
      user_id:
        type: uuid
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id

  User:
    fields:
      id:
        type: uuid
""")

        parser = SchemaParser()
        schema = parser.parse(schema_file)

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Should have no type: ignore (belongsTo uses None, not mutable default)
        assert "# type: ignore" not in code, \
            "belongsTo relationship should not have type: ignore"

        # Verify belongsTo is generated correctly
        assert "user: User | None = None" in code
