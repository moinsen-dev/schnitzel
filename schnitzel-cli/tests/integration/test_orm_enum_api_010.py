"""Integration tests for API_010 - SQLAlchemy ORM generator handles enum types.

Test Requirements:
1. Verify ORM generator recognizes enum type in schema
2. Verify generated code creates Python Enum class
3. Verify generated column uses SQLAlchemy Enum type
4. Create integration test that:
   - Creates a schema with enum fields (e.g., status: enum[pending, active, completed])
   - Generates ORM code
   - Verifies Enum class is generated
   - Verifies column type is SQLAlchemy Enum
   - Tests CRUD with enum values

This follows Schnitzel zero-tolerance policy: no errors, no warnings, no TODOs.
"""

import tempfile
import os
import sys
from pathlib import Path
import pytest

from schnitzel.schema.parser import SchemaParser
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def schema_with_single_enum(temp_dir: Path) -> Path:
    """Create a schema with a single enum field."""
    schema_content = """schnitzel: "1.0"

models:
  Task:
    description: "Task with status enum"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      status:
        type: enum
        values: ["pending", "active", "completed"]
        default: pending
      created_at:
        type: datetime
        auto: create
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.fixture
def schema_with_multiple_enums(temp_dir: Path) -> Path:
    """Create a schema with multiple enum fields across models."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with role enum"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
      role:
        type: enum
        values: ["admin", "moderator", "user", "guest"]
        default: user
      created_at:
        type: datetime
        auto: create

  Order:
    description: "Order with status enum"
    fields:
      id:
        type: uuid
        primary: true
      order_number:
        type: string
        unique: true
      status:
        type: enum
        values: ["pending", "processing", "shipped", "delivered", "cancelled"]
        default: pending
      priority:
        type: enum
        values: ["low", "medium", "high", "urgent"]
        default: medium
      total:
        type: float
      user_id:
        type: uuid
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_orm_generator_recognizes_enum_type(schema_with_single_enum: Path) -> None:
    """Test that ORM generator recognizes enum type in schema."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_single_enum))

    # Verify schema has enum field
    assert "Task" in schema.models
    task_model = schema.models["Task"]
    assert "status" in task_model.fields
    status_field = task_model.fields["status"]
    assert status_field.type.lower() == "enum"
    assert status_field.values == ["pending", "active", "completed"]
    assert status_field.default == "pending"


def test_generated_code_creates_python_enum_class(schema_with_single_enum: Path) -> None:
    """Test that generated code creates Python Enum class."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_single_enum))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify enum import
    assert "import enum" in orm_code

    # Verify enum class is generated
    assert "class TaskStatus(str, enum.Enum):" in orm_code

    # Verify enum values are present
    assert 'PENDING = "pending"' in orm_code
    assert 'ACTIVE = "active"' in orm_code
    assert 'COMPLETED = "completed"' in orm_code


def test_generated_column_uses_sqlalchemy_enum_type(schema_with_single_enum: Path) -> None:
    """Test that generated column uses SQLAlchemy Enum type."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_single_enum))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify SQLAlchemy Enum is used in column definition
    assert "sa.Enum(TaskStatus)" in orm_code

    # Verify the column has proper type hint
    assert "status: Mapped[TaskStatus]" in orm_code

    # Verify default value uses enum member
    assert "default=TaskStatus.PENDING" in orm_code


def test_generated_code_is_syntactically_valid(schema_with_single_enum: Path) -> None:
    """Test that generated code with enums is syntactically valid."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_single_enum))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify Python syntax by compiling
    try:
        compile(orm_code, "<generated>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated ORM code with enums has syntax errors: {e}\n\nCode:\n{orm_code}")


def test_generated_code_can_be_imported(temp_dir: Path, schema_with_single_enum: Path) -> None:
    """Test that generated code can be imported without errors."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_single_enum))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Write to file
    orm_file = temp_dir / "test_orm_enum.py"
    orm_file.write_text(orm_code)

    # Add directory to sys.path
    sys.path.insert(0, str(temp_dir))

    try:
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_orm_enum", orm_file)
        assert spec is not None, "Could not create module spec"
        assert spec.loader is not None, "Module spec has no loader"

        orm_module = importlib.util.module_from_spec(spec)
        # Add to sys.modules before execution (required by SQLAlchemy)
        sys.modules["test_orm_enum"] = orm_module
        spec.loader.exec_module(orm_module)

        # Verify enum class exists
        assert hasattr(orm_module, "TaskStatus"), "TaskStatus enum should be defined"
        TaskStatus = getattr(orm_module, "TaskStatus")

        # Verify enum values
        assert hasattr(TaskStatus, "PENDING")
        assert hasattr(TaskStatus, "ACTIVE")
        assert hasattr(TaskStatus, "COMPLETED")
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ACTIVE.value == "active"
        assert TaskStatus.COMPLETED.value == "completed"

        # Verify Task model exists
        assert hasattr(orm_module, "Task"), "Task model should be defined"
        Task = getattr(orm_module, "Task")
        assert Task is not None

    except ImportError as e:
        pytest.fail(f"Generated code cannot be imported: {e}\n\nCode:\n{orm_code}")
    except Exception as e:
        pytest.fail(f"Error when importing/using generated code: {e}\n\nCode:\n{orm_code}")
    finally:
        # Clean up sys.path and sys.modules
        if str(temp_dir) in sys.path:
            sys.path.remove(str(temp_dir))
        if "test_orm_enum" in sys.modules:
            del sys.modules["test_orm_enum"]


def test_multiple_enums_in_same_model(schema_with_multiple_enums: Path) -> None:
    """Test handling of multiple enum fields in the same model."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_multiple_enums))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify both enum classes are generated
    assert "class OrderStatus(str, enum.Enum):" in orm_code
    assert "class OrderPriority(str, enum.Enum):" in orm_code

    # Verify enum values
    assert 'PENDING = "pending"' in orm_code
    assert 'PROCESSING = "processing"' in orm_code
    assert 'LOW = "low"' in orm_code
    assert 'MEDIUM = "medium"' in orm_code
    assert 'HIGH = "high"' in orm_code

    # Verify both columns use SQLAlchemy Enum
    assert "sa.Enum(OrderStatus)" in orm_code
    assert "sa.Enum(OrderPriority)" in orm_code


def test_multiple_enums_across_models(schema_with_multiple_enums: Path) -> None:
    """Test handling of enums across multiple models."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_multiple_enums))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify enums from both models are generated
    assert "class UserRole(str, enum.Enum):" in orm_code
    assert "class OrderStatus(str, enum.Enum):" in orm_code
    assert "class OrderPriority(str, enum.Enum):" in orm_code

    # Verify UserRole enum values
    assert 'ADMIN = "admin"' in orm_code
    assert 'MODERATOR = "moderator"' in orm_code
    assert 'USER = "user"' in orm_code
    assert 'GUEST = "guest"' in orm_code


def test_enum_with_hyphenated_values(temp_dir: Path) -> None:
    """Test enum handling with hyphenated and special values."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "Product with category enum"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      category:
        type: enum
        values: ["home-goods", "electronics", "sports-outdoors", "health-beauty"]
        default: home-goods
"""
    schema_file = temp_dir / "schema_hyphenated.yaml"
    schema_file.write_text(schema_content)

    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_file))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify enum class handles hyphenated values (converts to underscores)
    assert "class ProductCategory(str, enum.Enum):" in orm_code
    assert 'HOME_GOODS = "home-goods"' in orm_code
    assert 'ELECTRONICS = "electronics"' in orm_code
    assert 'SPORTS_OUTDOORS = "sports-outdoors"' in orm_code
    assert 'HEALTH_BEAUTY = "health-beauty"' in orm_code

    # Verify default value
    assert "default=ProductCategory.HOME_GOODS" in orm_code


def test_enum_ordering_in_generated_code(schema_with_multiple_enums: Path) -> None:
    """Test that enums are generated before models in the code."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_multiple_enums))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Find positions of enum and model definitions
    user_role_pos = orm_code.find("class UserRole(str, enum.Enum):")
    order_status_pos = orm_code.find("class OrderStatus(str, enum.Enum):")
    user_model_pos = orm_code.find("class User(Base):")
    order_model_pos = orm_code.find("class Order(Base):")

    # Verify enums come before models
    assert user_role_pos < user_model_pos, "UserRole enum should be defined before User model"
    assert order_status_pos < order_model_pos, "OrderStatus enum should be defined before Order model"


def test_enum_with_relationships(schema_with_multiple_enums: Path) -> None:
    """Test that enums work correctly with model relationships."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_multiple_enums))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify both enum columns and foreign key columns are present
    assert "sa.Enum(OrderStatus)" in orm_code
    assert "sa.ForeignKey" in orm_code

    # Verify syntax is valid
    try:
        compile(orm_code, "<generated>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated code with enums and relationships has syntax errors: {e}")


def test_enum_class_naming_convention(temp_dir: Path) -> None:
    """Test that enum class names follow PascalCase naming convention."""
    schema_content = """schnitzel: "1.0"

models:
  BlogPost:
    description: "Blog post with various enums"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      publish_status:
        type: enum
        values: ["draft", "published", "archived"]
        default: draft
      content_type:
        type: enum
        values: ["article", "video", "podcast"]
        default: article
"""
    schema_file = temp_dir / "schema_naming.yaml"
    schema_file.write_text(schema_content)

    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_file))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify enum class names are in PascalCase with model prefix
    assert "class BlogPostPublishStatus(str, enum.Enum):" in orm_code
    assert "class BlogPostContentType(str, enum.Enum):" in orm_code


def test_enum_without_default_value(temp_dir: Path) -> None:
    """Test enum field without default value."""
    schema_content = """schnitzel: "1.0"

models:
  Ticket:
    description: "Support ticket"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      severity:
        type: enum
        values: ["low", "medium", "high", "critical"]
        required: true
"""
    schema_file = temp_dir / "schema_no_default.yaml"
    schema_file.write_text(schema_content)

    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_file))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify enum class is generated
    assert "class TicketSeverity(str, enum.Enum):" in orm_code

    # Verify no default is set
    assert "default=TicketSeverity" not in orm_code

    # Verify column is not nullable (required)
    assert "nullable=False" in orm_code


def test_enum_with_optional_field(temp_dir: Path) -> None:
    """Test enum field that is optional (nullable)."""
    schema_content = """schnitzel: "1.0"

models:
  Survey:
    description: "Survey response"
    fields:
      id:
        type: uuid
        primary: true
      question:
        type: string
      satisfaction:
        type: enum
        values: ["very-satisfied", "satisfied", "neutral", "dissatisfied", "very-dissatisfied"]
        optional: true
"""
    schema_file = temp_dir / "schema_optional.yaml"
    schema_file.write_text(schema_content)

    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_file))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify enum class is generated
    assert "class SurveySatisfaction(str, enum.Enum):" in orm_code

    # Verify type hint includes None
    assert "satisfaction: Mapped[SurveySatisfaction | None]" in orm_code

    # Verify column is nullable
    assert "nullable=True" in orm_code


def test_full_code_generation_structure(schema_with_multiple_enums: Path) -> None:
    """Test the overall structure of generated code with enums."""
    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_multiple_enums))
    generator = SQLAlchemyORMGenerator()
    orm_code = generator.generate(schema)

    # Verify structure: imports, base, enums, models
    lines = orm_code.split("\n")

    # Check for proper import section
    assert any("from __future__ import annotations" in line for line in lines)
    assert any("import enum" in line for line in lines)
    assert any("import sqlalchemy as sa" in line for line in lines)

    # Check for Base declaration
    assert any("class Base(DeclarativeBase):" in line for line in lines)

    # Check for enum definitions
    assert any("class UserRole(str, enum.Enum):" in line for line in lines)
    assert any("class OrderStatus(str, enum.Enum):" in line for line in lines)

    # Check for model definitions
    assert any("class User(Base):" in line for line in lines)
    assert any("class Order(Base):" in line for line in lines)

    # Verify no syntax errors
    try:
        compile(orm_code, "<generated>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated code structure is invalid: {e}")
