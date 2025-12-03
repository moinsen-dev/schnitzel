"""Integration test for F022: Python model generator maps all field types correctly.

Test Steps:
1. Create schema with fields: str_field (string), int_field (int), float_field (float),
   bool_field (bool), uuid_field (uuid), datetime_field (datetime), json_field (json)
2. Call PythonModelGenerator.generate(schema)
3. Verify str_field maps to str
4. Verify int_field maps to int
5. Verify float_field maps to float
6. Verify bool_field maps to bool
7. Verify uuid_field maps to UUID
8. Verify datetime_field maps to datetime
9. Verify json_field maps to dict[str, Any]
10. Verify all necessary imports are present
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


def test_python_model_generator_basic_type_mappings():
    """Test that all basic field types map to correct Python types."""

    # Step 1: Create schema with all basic field types
    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "str_field": FieldDefinition(type="string"),
                    "int_field": FieldDefinition(type="int"),
                    "float_field": FieldDefinition(type="float"),
                    "bool_field": FieldDefinition(type="bool"),
                    "uuid_field": FieldDefinition(type="uuid"),
                    "datetime_field": FieldDefinition(type="datetime"),
                    "json_field": FieldDefinition(type="json"),
                }
            )
        }
    )

    # Step 2: Generate Python code
    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated Python code:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Step 3-9: Verify type mappings
    assert "str_field: str" in generated_code, "str_field should map to str"
    assert "int_field: int" in generated_code, "int_field should map to int"
    assert "float_field: float" in generated_code, "float_field should map to float"
    assert "bool_field: bool" in generated_code, "bool_field should map to bool"
    assert "uuid_field: UUID" in generated_code, "uuid_field should map to UUID"
    assert "datetime_field: datetime" in generated_code, "datetime_field should map to datetime"
    assert "json_field: dict[str, Any]" in generated_code, "json_field should map to dict[str, Any]"

    # Step 10: Verify necessary imports
    assert "from uuid import UUID" in generated_code, "UUID import should be present"
    assert "from datetime import datetime" in generated_code, "datetime import should be present"
    assert "from typing import Any" in generated_code, "Any import should be present for dict[str, Any]"
    assert "from pydantic import BaseModel" in generated_code, "BaseModel import should be present"


def test_python_model_generator_list_types():
    """Test that list<T> types map correctly."""

    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "str_list": FieldDefinition(type="list<string>"),
                    "int_list": FieldDefinition(type="list<int>"),
                    "uuid_list": FieldDefinition(type="list<uuid>"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with list types:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify list type mappings
    assert "str_list: list[str]" in generated_code, "list<string> should map to list[str]"
    assert "int_list: list[int]" in generated_code, "list<int> should map to list[int]"
    assert "uuid_list: list[UUID]" in generated_code, "list<uuid> should map to list[UUID]"

    # Verify UUID import is present
    assert "from uuid import UUID" in generated_code


def test_python_model_generator_enum_types():
    """Test that enum types map to Literal."""

    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "status": FieldDefinition(
                        type="enum",
                        values=["active", "inactive", "pending"]
                    ),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with enum type:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify enum maps to Literal
    assert 'status: Literal["active", "inactive", "pending"]' in generated_code, \
        "enum should map to Literal[...]"

    # Verify Literal import
    assert "from typing import Literal" in generated_code, "Literal import should be present"


def test_python_model_generator_vector_types():
    """Test that vector types map to list[float]."""

    schema = SchnitzelSchema(
        models={
            "TestModel": Model(
                name="TestModel",
                fields={
                    "embedding": FieldDefinition(type="vector", dimensions=384),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with vector type:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify vector maps to list[float]
    assert "embedding: list[float]" in generated_code, "vector should map to list[float]"


def test_python_model_generator_all_types_comprehensive():
    """Comprehensive test with all supported types."""

    schema = SchnitzelSchema(
        models={
            "ComprehensiveModel": Model(
                name="ComprehensiveModel",
                fields={
                    # Basic types
                    "name": FieldDefinition(type="string"),
                    "age": FieldDefinition(type="int"),
                    "height": FieldDefinition(type="float"),
                    "active": FieldDefinition(type="bool"),
                    "user_id": FieldDefinition(type="uuid"),
                    "created_at": FieldDefinition(type="datetime"),
                    "metadata": FieldDefinition(type="json"),

                    # List types
                    "tags": FieldDefinition(type="list<string>"),
                    "scores": FieldDefinition(type="list<int>"),

                    # Enum type
                    "role": FieldDefinition(
                        type="enum",
                        values=["admin", "user", "guest"]
                    ),

                    # Vector type
                    "embedding": FieldDefinition(type="vector"),
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

    # Verify all type mappings
    assert "name: str" in generated_code
    assert "age: int" in generated_code
    assert "height: float" in generated_code
    assert "active: bool" in generated_code
    assert "user_id: UUID" in generated_code
    assert "created_at: datetime" in generated_code
    assert "metadata: dict[str, Any]" in generated_code
    assert "tags: list[str]" in generated_code
    assert "scores: list[int]" in generated_code
    assert 'role: Literal["admin", "user", "guest"]' in generated_code
    assert "embedding: list[float]" in generated_code

    # Verify all necessary imports
    assert "from uuid import UUID" in generated_code
    assert "from datetime import datetime" in generated_code
    assert "from typing import Any" in generated_code
    assert "from typing import Literal" in generated_code
    assert "from pydantic import BaseModel" in generated_code

    # Verify the code is valid Python by compiling it
    try:
        compile(generated_code, "<string>", "exec")
        print("\n Generated code is valid Python!")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")


def test_python_model_generator_imports_order():
    """Test that imports are properly ordered and deduplicated."""

    schema = SchnitzelSchema(
        models={
            "Model1": Model(
                name="Model1",
                fields={
                    "id": FieldDefinition(type="uuid"),
                    "data": FieldDefinition(type="json"),
                }
            ),
            "Model2": Model(
                name="Model2",
                fields={
                    "timestamp": FieldDefinition(type="datetime"),
                    "user_id": FieldDefinition(type="uuid"),
                }
            )
        }
    )

    generator = PythonModelGenerator()
    generated_code = generator.generate(schema)

    print("\nGenerated code with multiple models:")
    print("=" * 80)
    print(generated_code)
    print("=" * 80)

    # Verify imports appear only once (deduplicated)
    import_lines = [line for line in generated_code.split('\n') if line.startswith('from')]
    uuid_imports = [line for line in import_lines if 'UUID' in line]

    assert len(uuid_imports) == 1, "UUID import should appear only once"

    # Verify both models are generated
    assert "class Model1(BaseModel):" in generated_code
    assert "class Model2(BaseModel):" in generated_code


if __name__ == "__main__":
    # Run tests manually for development
    test_python_model_generator_basic_type_mappings()
    test_python_model_generator_list_types()
    test_python_model_generator_enum_types()
    test_python_model_generator_vector_types()
    test_python_model_generator_all_types_comprehensive()
    test_python_model_generator_imports_order()

    print("\n" + "=" * 80)
    print(" All F022 tests passed!")
    print("=" * 80)
