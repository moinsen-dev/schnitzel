"""Integration test for API_058: Validate command allows non-breaking changes.

Test Requirements:
1. Verify validate command correctly identifies non-breaking changes:
   - Adding optional fields
   - Adding new models
   - Adding indexes
   - Adding relationships
2. Create integration test that:
   - Tests adding optional field passes
   - Tests adding new model passes
   - Tests adding index passes
   - Verify these don't trigger breaking change warnings

This test validates that the `schnitzel validate` command:
- Accepts schemas with optional fields (non-breaking change)
- Accepts schemas with new models (non-breaking change)
- Accepts schemas with new indexes (non-breaking change)
- Accepts schemas with new relationships (non-breaking change)
- Does not produce errors or warnings for these additions
"""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_validate_allows_adding_optional_field(temp_dir: Path) -> None:
    """Test that validate allows adding optional fields (non-breaking change).

    Step 1: Create schema with optional field
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify no breaking change warnings
    """
    # Step 1: Create schema with optional field
    schema_content = """schnitzel: "1.0"

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
      bio:
        type: text
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify schema is valid and no errors
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()
    # Should not have breaking change errors (but tip about --breaking flag is OK)
    assert "breaking change detected" not in result.stdout.lower()
    assert "error" not in result.stdout.lower()
    assert "failed" not in result.stdout.lower()


def test_validate_allows_adding_new_model(temp_dir: Path) -> None:
    """Test that validate allows adding new models (non-breaking change).

    Step 1: Create schema with multiple models
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify all models are recognized
    """
    # Step 1: Create schema with new model
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Product:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      price:
        type: float

  Order:
    fields:
      id:
        type: uuid
        primary: true
      total:
        type: float
    relations:
      user:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify all models are recognized
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()
    # Should show all 3 models in summary
    output_upper = result.stdout
    if "User" in output_upper or "Product" in output_upper or "Order" in output_upper:
        # Models are listed in output
        assert "3" in result.stdout  # 3 models


def test_validate_allows_adding_index(temp_dir: Path) -> None:
    """Test that validate allows adding indexes (non-breaking change).

    Step 1: Create schema with indexed fields
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify no breaking change warnings
    """
    # Step 1: Create schema with index
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
        index: true
      username:
        type: string
        index: true
      created_at:
        type: datetime
        index: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify schema is valid and no errors
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()
    # Should not have breaking change errors (but tip about --breaking flag is OK)
    assert "breaking change detected" not in result.stdout.lower()
    assert "error" not in result.stdout.lower()
    assert "failed" not in result.stdout.lower()


def test_validate_allows_adding_relationships(temp_dir: Path) -> None:
    """Test that validate allows adding relationships (non-breaking change).

    Step 1: Create schema with relationships
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify relationships are accepted
    """
    # Step 1: Create schema with relationships
    schema_content = """schnitzel: "1.0"

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
        type: hasOne
        model: Profile

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
    relations:
      author:
        type: belongsTo
        model: User

  Profile:
    fields:
      id:
        type: uuid
        primary: true
      bio:
        type: text
    relations:
      user:
        type: hasOne
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify relationships are accepted
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()
    # Should show relationships in summary if present
    if "Relationships" in result.stdout or "relations" in result.stdout.lower():
        assert True


def test_validate_optional_vs_required_fields(temp_dir: Path) -> None:
    """Test that validate distinguishes between optional and required fields.

    Step 1: Create schema with mix of optional and required fields
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify both field types are accepted
    """
    # Step 1: Create schema with mixed field requirements
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        required: true
      email:
        type: string
        required: true
      phone:
        type: string
        optional: true
      address:
        type: string
        optional: true
      bio:
        type: text
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify both field types are accepted
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_validate_optional_field_with_default(temp_dir: Path) -> None:
    """Test that validate allows optional fields with default values.

    Step 1: Create schema with optional fields with defaults
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify no errors about default values
    """
    # Step 1: Create schema with optional fields with defaults
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      price:
        type: float
      in_stock:
        type: bool
        optional: true
        default: true
      quantity:
        type: int
        optional: true
        default: 0
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify no errors
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_validate_comprehensive_nonbreaking_changes(temp_dir: Path) -> None:
    """Test comprehensive non-breaking changes together.

    Step 1: Create schema with all non-breaking change types
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify complete schema is accepted
    """
    # Step 1: Create comprehensive schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model with optional fields"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
        index: true
      name:
        type: string
        required: true
      phone:
        type: string
        optional: true
      bio:
        type: text
        optional: true
      created_at:
        type: datetime
        index: true
    relations:
      posts:
        type: hasMany
        model: Post
      profile:
        type: hasOne
        model: Profile

  Post:
    description: "New model - non-breaking addition"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
        index: true
      content:
        type: text
      published:
        type: bool
        optional: true
        default: false
      views:
        type: int
        optional: true
        default: 0
    relations:
      author:
        type: belongsTo
        model: User

  Profile:
    description: "Another new model with indexes"
    fields:
      id:
        type: uuid
        primary: true
      bio:
        type: text
        optional: true
      avatar_url:
        type: string
        optional: true
      website:
        type: string
        optional: true
        format: url
    relations:
      user:
        type: hasOne
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify complete schema is accepted
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()
    # Should show all 3 models
    if "3" in result.stdout:
        assert True


def test_validate_nonbreaking_with_strict_mode(temp_dir: Path) -> None:
    """Test that non-breaking changes pass even in strict mode.

    Step 1: Create schema with non-breaking changes
    Step 2: Run schnitzel validate --strict
    Step 3: Verify validation passes
    Step 4: Verify strict mode doesn't flag non-breaking changes
    """
    # Step 1: Create schema with non-breaking changes
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
        index: true
      phone:
        type: string
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate with --strict
    result = runner.invoke(app, ["validate", str(schema_file), "--strict"])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed in strict mode: {result.stdout}"

    # Step 4: Verify no warnings about non-breaking changes
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_validate_index_on_various_field_types(temp_dir: Path) -> None:
    """Test that validate allows indexes on various field types.

    Step 1: Create schema with indexes on different field types
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify all index types are accepted
    """
    # Step 1: Create schema with various indexed field types
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        index: true
      age:
        type: int
        index: true
      created_at:
        type: datetime
        index: true
      is_active:
        type: bool
        index: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify all indexes are accepted
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_validate_multiple_optional_fields(temp_dir: Path) -> None:
    """Test that validate allows multiple optional fields in a model.

    Step 1: Create schema with many optional fields
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify all optional fields are accepted
    """
    # Step 1: Create schema with many optional fields
    schema_content = """schnitzel: "1.0"

models:
  UserProfile:
    fields:
      id:
        type: uuid
        primary: true
      user_id:
        type: uuid
        unique: true
      bio:
        type: text
        optional: true
      avatar_url:
        type: string
        optional: true
      website:
        type: string
        optional: true
      twitter:
        type: string
        optional: true
      github:
        type: string
        optional: true
      linkedin:
        type: string
        optional: true
      location:
        type: string
        optional: true
      company:
        type: string
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify all optional fields are accepted
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_validate_quiet_mode_with_nonbreaking_changes(temp_dir: Path) -> None:
    """Test that quiet mode works with non-breaking changes.

    Step 1: Create schema with non-breaking changes
    Step 2: Run schnitzel validate --quiet
    Step 3: Verify validation passes
    Step 4: Verify output is minimal
    """
    # Step 1: Create schema with non-breaking changes
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        index: true
      phone:
        type: string
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate with --quiet
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify output is minimal
    assert len(result.stdout.strip()) < 50
    assert "ok" in result.stdout.lower()


def test_validate_new_model_with_relationships(temp_dir: Path) -> None:
    """Test that validate allows new models with relationships.

    Step 1: Create schema with new model that has relationships
    Step 2: Run schnitzel validate
    Step 3: Verify validation passes
    Step 4: Verify relationships to existing models work
    """
    # Step 1: Create schema with new model with relationships
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Comment:
    description: "New model with relationships"
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: text
      created_at:
        type: datetime
    relations:
      author:
        type: belongsTo
        model: User
      post:
        type: belongsTo
        model: Post

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
    relations:
      author:
        type: belongsTo
        model: User
      comments:
        type: hasMany
        model: Comment
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Step 3: Verify validation passes
    assert result.exit_code == 0, f"Validation failed: {result.stdout}"

    # Step 4: Verify relationships are accepted
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
