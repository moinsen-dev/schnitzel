"""Integration tests for F085: Schema parser preserves field order from YAML file.

This feature ensures that when parsing YAML schemas, the field order defined
in the YAML file is preserved throughout the parsing and code generation pipeline.

Requirements:
- YAML parser preserves field order during parsing
- Generated Python code has fields in same order as schema
- Generated Dart code has fields in same order as schema
- Order is preserved even with many fields
"""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.dart.models import DartModelGenerator


class TestFieldOrderPreservation:
    """Test that field order is preserved from YAML through code generation."""

    def test_yaml_parser_preserves_field_order(self):
        """Test that SchemaParser preserves field order from YAML file.

        This test verifies that when a YAML file defines fields in a specific order,
        the parser maintains that exact order in the resulting SchnitzelSchema object.
        """
        yaml_content = """schnitzel: "1.0"
models:
  User:
    description: "Test model for field order"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      username:
        type: string
      first_name:
        type: string
      last_name:
        type: string
      created_at:
        type: datetime
        auto: create
"""

        # Write YAML to temporary file
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            # Parse the schema
            parser = SchemaParser()
            schema = parser.parse(temp_path)

            # Verify schema was parsed successfully
            assert "User" in schema.models
            user_model = schema.models["User"]

            # Get field names in order
            field_names = list(user_model.fields.keys())

            # Expected order matches YAML order
            expected_order = ["id", "email", "username", "first_name", "last_name", "created_at"]

            # Verify order is preserved
            assert field_names == expected_order, (
                f"Field order not preserved.\n"
                f"Expected: {expected_order}\n"
                f"Got: {field_names}"
            )

            print(f"✓ YAML parser preserved field order: {field_names}")

        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)

    def test_field_order_preserved_python(self):
        """Test that Python generator preserves field order from schema.

        This test verifies that the PythonModelGenerator maintains the field
        order from the schema when generating Pydantic models.
        """
        # Create schema with specific field order
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    description="Product with ordered fields",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="string", optional=True),
                        "price": FieldDefinition(type="float", min=0),
                        "quantity": FieldDefinition(type="int", default=0),
                        "category": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    }
                )
            }
        )

        # Generate Python code
        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Extract field definitions from generated code
        # Look for lines that define fields (contain ": " and are indented)
        lines = code.split('\n')
        field_lines = []
        in_class = False

        for line in lines:
            if 'class Product(BaseModel):' in line:
                in_class = True
                continue
            if in_class and line.strip().startswith('class '):
                # Next class started
                break
            if in_class and ':' in line and line.startswith('    ') and not line.strip().startswith('"""'):
                # Extract field name (before the colon)
                field_name = line.strip().split(':')[0].strip()
                if field_name and not field_name.startswith('#'):
                    field_lines.append(field_name)

        # Expected order
        expected_order = ["id", "name", "description", "price", "quantity", "category", "created_at"]

        # Verify field order matches
        assert field_lines == expected_order, (
            f"Python field order not preserved.\n"
            f"Expected: {expected_order}\n"
            f"Got: {field_lines}\n"
            f"Generated code:\n{code}"
        )

        print(f"✓ Python generator preserved field order: {field_lines}")

    def test_field_order_preserved_dart(self):
        """Test that Dart generator preserves field order from schema.

        This test verifies that the DartModelGenerator maintains the field
        order from the schema when generating Freezed models.
        """
        # Create schema with specific field order
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    description="Product with ordered fields",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "name": FieldDefinition(type="string"),
                        "description": FieldDefinition(type="string", optional=True),
                        "price": FieldDefinition(type="float"),
                        "quantity": FieldDefinition(type="int", default=0),
                        "category": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        # Generate Dart code
        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Extract field definitions from generated code
        # Look for field declarations in factory constructor
        lines = code.split('\n')
        field_lines = []
        in_factory = False

        for line in lines:
            if 'const factory Product({' in line:
                in_factory = True
                continue
            if in_factory and '}) = _Product;' in line:
                break
            if in_factory and line.strip():
                # Extract field name (last word before comma)
                parts = line.strip().split()
                if parts and parts[-1].endswith(','):
                    field_name = parts[-1][:-1]  # Remove trailing comma
                    field_lines.append(field_name)

        # Expected order
        expected_order = ["id", "name", "description", "price", "quantity", "category", "createdAt"]

        # Verify field order matches
        assert field_lines == expected_order, (
            f"Dart field order not preserved.\n"
            f"Expected: {expected_order}\n"
            f"Got: {field_lines}\n"
            f"Generated code:\n{code}"
        )

        print(f"✓ Dart generator preserved field order: {field_lines}")

    def test_many_fields_order(self):
        """Test field order preservation with many fields (stress test).

        This test verifies that field order is preserved even when dealing
        with a large number of fields, ensuring the implementation scales.
        """
        # Create a model with many fields in a specific order
        fields = {}
        expected_order = []

        # Create 20 fields with specific naming pattern
        for i in range(1, 21):
            field_name = f"field_{i:02d}"
            fields[field_name] = FieldDefinition(type="string")
            expected_order.append(field_name)

        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "LargeModel": Model(
                    name="LargeModel",
                    fields=fields
                )
            }
        )

        # Verify order in schema
        schema_field_order = list(schema.models["LargeModel"].fields.keys())
        assert schema_field_order == expected_order, (
            f"Schema field order incorrect.\n"
            f"Expected first 5: {expected_order[:5]}\n"
            f"Got first 5: {schema_field_order[:5]}"
        )

        # Test Python generator
        py_gen = PythonModelGenerator()
        py_code = py_gen.generate(schema)

        # Extract Python field order
        py_fields = []
        lines = py_code.split('\n')
        in_class = False

        for line in lines:
            if 'class LargeModel(BaseModel):' in line:
                in_class = True
                continue
            if in_class and line.strip().startswith('class '):
                break
            if in_class and ':' in line and line.startswith('    '):
                field_name = line.strip().split(':')[0].strip()
                if field_name and not field_name.startswith('#') and not field_name.startswith('"""'):
                    py_fields.append(field_name)

        assert py_fields == expected_order, (
            f"Python many fields order not preserved.\n"
            f"Expected first 5: {expected_order[:5]}\n"
            f"Got first 5: {py_fields[:5]}"
        )

        # Test Dart generator
        dart_gen = DartModelGenerator()
        dart_code = dart_gen.generate(schema)

        # Extract Dart field order
        dart_fields = []
        lines = dart_code.split('\n')
        in_factory = False

        for line in lines:
            if 'const factory LargeModel({' in line:
                in_factory = True
                continue
            if in_factory and '}) = _LargeModel;' in line:
                break
            if in_factory and line.strip():
                parts = line.strip().split()
                if parts and parts[-1].endswith(','):
                    field_name = parts[-1][:-1]
                    dart_fields.append(field_name)

        assert dart_fields == expected_order, (
            f"Dart many fields order not preserved.\n"
            f"Expected first 5: {expected_order[:5]}\n"
            f"Got first 5: {dart_fields[:5]}"
        )

        print(f"✓ Field order preserved for {len(expected_order)} fields")

    def test_yaml_to_code_end_to_end_order(self):
        """Test end-to-end field order preservation from YAML to generated code.

        This test verifies that field order is maintained through the entire
        pipeline: YAML file → Parser → Schema → Generator → Output code.
        """
        yaml_content = """schnitzel: "1.0"
models:
  Order:
    description: "E-commerce order"
    fields:
      id:
        type: uuid
        primary: true
      order_number:
        type: string
      customer_email:
        type: string
      total_amount:
        type: float
      status:
        type: string
      created_at:
        type: datetime
        auto: create
      updated_at:
        type: datetime
        auto: update
"""

        # Write YAML to temporary file
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            # Parse schema from YAML
            parser = SchemaParser()
            schema = parser.parse(temp_path)

            # Expected field order (from YAML)
            expected_order = [
                "id", "order_number", "customer_email", "total_amount",
                "status", "created_at", "updated_at"
            ]

            # Verify schema field order
            schema_fields = list(schema.models["Order"].fields.keys())
            assert schema_fields == expected_order, (
                f"Schema field order doesn't match YAML.\n"
                f"Expected: {expected_order}\n"
                f"Got: {schema_fields}"
            )

            # Generate Python code and verify order
            py_gen = PythonModelGenerator()
            py_code = py_gen.generate(schema)

            # Extract Python field names
            py_fields = []
            lines = py_code.split('\n')
            in_class = False

            for line in lines:
                if 'class Order(BaseModel):' in line:
                    in_class = True
                    continue
                if in_class and line.strip().startswith('class '):
                    break
                if in_class and ':' in line and line.startswith('    ') and not line.strip().startswith('"""'):
                    field_name = line.strip().split(':')[0].strip()
                    if field_name and not field_name.startswith('#'):
                        py_fields.append(field_name)

            assert py_fields == expected_order, (
                f"Python code field order doesn't match YAML.\n"
                f"Expected: {expected_order}\n"
                f"Got: {py_fields}"
            )

            print(f"✓ End-to-end field order preserved: {expected_order}")

        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)

    def test_dict_insertion_order_guarantee(self):
        """Test that Python dicts preserve insertion order (Python 3.7+ guarantee).

        This is a sanity check to verify that the underlying Python dict
        implementation maintains insertion order, which is the foundation
        for field order preservation in the schema.
        """
        # Create a dict with specific insertion order
        test_dict = {}
        insertion_order = ["alpha", "beta", "gamma", "delta", "epsilon"]

        for key in insertion_order:
            test_dict[key] = f"value_{key}"

        # Verify dict keys maintain insertion order
        actual_order = list(test_dict.keys())
        assert actual_order == insertion_order, (
            f"Python dict doesn't preserve insertion order (this should not happen in Python 3.7+).\n"
            f"Expected: {insertion_order}\n"
            f"Got: {actual_order}"
        )

        print("✓ Python dict preserves insertion order (Python 3.7+ guarantee)")

    def test_pydantic_model_field_order(self):
        """Test that Pydantic models preserve field definition order.

        This verifies that when we create a Model with fields in a specific order,
        Pydantic preserves that order in the model's field dictionary.
        """
        # Create a Model with fields in specific order
        model = Model(
            name="TestModel",
            fields={
                "field_a": FieldDefinition(type="string"),
                "field_b": FieldDefinition(type="int"),
                "field_c": FieldDefinition(type="float"),
                "field_d": FieldDefinition(type="bool"),
            }
        )

        # Get field order
        field_order = list(model.fields.keys())
        expected_order = ["field_a", "field_b", "field_c", "field_d"]

        # Verify order is preserved
        assert field_order == expected_order, (
            f"Pydantic Model doesn't preserve field order.\n"
            f"Expected: {expected_order}\n"
            f"Got: {field_order}"
        )

        print("✓ Pydantic Model preserves field definition order")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "="*70)
    print("Running F085: Field Order Preservation Tests")
    print("="*70)

    test_suite = TestFieldOrderPreservation()

    print("\n1. Testing YAML parser field order preservation...")
    test_suite.test_yaml_parser_preserves_field_order()

    print("\n2. Testing Python generator field order preservation...")
    test_suite.test_field_order_preserved_python()

    print("\n3. Testing Dart generator field order preservation...")
    test_suite.test_field_order_preserved_dart()

    print("\n4. Testing many fields order preservation...")
    test_suite.test_many_fields_order()

    print("\n5. Testing end-to-end YAML to code order preservation...")
    test_suite.test_yaml_to_code_end_to_end_order()

    print("\n6. Testing Python dict insertion order guarantee...")
    test_suite.test_dict_insertion_order_guarantee()

    print("\n7. Testing Pydantic model field order...")
    test_suite.test_pydantic_model_field_order()

    print("\n" + "="*70)
    print("All F085 Field Order Preservation Tests Passed!")
    print("="*70)
    print("\nSummary:")
    print("- YAML parser preserves field order from YAML files")
    print("- Python generator maintains field order in generated code")
    print("- Dart generator maintains field order in generated code")
    print("- Field order is preserved even with many fields (20+ tested)")
    print("- End-to-end order preservation verified (YAML → Schema → Code)")
    print("- Python 3.7+ dict insertion order guarantee confirmed")
    print("- Pydantic Model field order preservation confirmed")
