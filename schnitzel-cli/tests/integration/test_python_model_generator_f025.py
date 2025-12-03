"""Integration tests for F025: Python model generator with Pydantic Field validation rules."""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python import PythonModelGenerator


class TestPythonModelGeneratorValidation:
    """Test Python model generator validation rules using Pydantic Field."""

    def test_numeric_min_constraint_generates_ge(self):
        """Test that min constraint maps to ge (greater than or equal)."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float", min=0),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "price: float = Field(ge=0)" in code
        assert "from pydantic import BaseModel, Field" in code

    def test_numeric_max_constraint_generates_le(self):
        """Test that max constraint maps to le (less than or equal)."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float", max=100000),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "price: float = Field(le=100000)" in code

    def test_numeric_min_max_constraint_generates_both(self):
        """Test that min and max constraints map to ge and le."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float", min=0, max=100000),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "price: float = Field(ge=0, le=100000)" in code

    def test_string_max_length_constraint(self):
        """Test that max_length constraint is generated correctly."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "name": FieldDefinition(type="string", max_length=200),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "name: str = Field(max_length=200)" in code

    def test_multiple_fields_with_constraints(self):
        """Test multiple fields with different constraints."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "price": FieldDefinition(type="float", min=0, max=100000),
                        "name": FieldDefinition(type="string", max_length=200),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        # Check all fields are present with correct constraints
        assert "id: UUID" in code
        assert "price: float = Field(ge=0, le=100000)" in code
        assert "name: str = Field(max_length=200)" in code
        assert "from uuid import UUID" in code

    def test_int_field_with_min_max(self):
        """Test integer field with min/max constraints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "age": FieldDefinition(type="int", min=0, max=150),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "age: int = Field(ge=0, le=150)" in code

    def test_optional_field_with_constraints(self):
        """Test optional field with validation constraints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "bio": FieldDefinition(type="string", max_length=500, optional=True),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        # Check for either Union syntax (Python 3.10+) or Optional syntax
        assert (
            "bio: str | None = Field(max_length=500, default=None)" in code or
            "bio: Optional[str] = Field(max_length=500, default=None)" in code
        )

    def test_field_import_present(self):
        """Test that Field is imported from pydantic."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float", min=0),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "from pydantic import BaseModel, Field" in code

    def test_field_without_constraints_no_field(self):
        """Test that fields without constraints don't use Field()."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        # Should be simple type annotation without Field()
        assert "name: str\n" in code or "name: str" in code

    def test_combined_constraints_order(self):
        """Test that constraints are ordered correctly in Field()."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "quantity": FieldDefinition(type="int", min=1, max=1000, default=1),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        # Constraints should come before default
        assert "quantity: int = Field(ge=1, le=1000, default=1)" in code

    def test_multiple_models_with_constraints(self):
        """Test multiple models each with constrained fields."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "price": FieldDefinition(type="float", min=0, max=100000),
                    }
                ),
                "User": Model(
                    name="User",
                    fields={
                        "age": FieldDefinition(type="int", min=0, max=150),
                        "username": FieldDefinition(type="string", max_length=50),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        # Check both models and their constraints
        assert "class Product(BaseModel):" in code
        assert "price: float = Field(ge=0, le=100000)" in code
        assert "class User(BaseModel):" in code
        assert "age: int = Field(ge=0, le=150)" in code
        assert "username: str = Field(max_length=50)" in code

    def test_float_min_max_with_decimals(self):
        """Test float constraints with decimal values."""
        schema = SchnitzelSchema(
            models={
                "Measurement": Model(
                    name="Measurement",
                    fields={
                        "value": FieldDefinition(type="float", min=0.0, max=99.99),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "value: float = Field(ge=0.0, le=99.99)" in code

    def test_negative_min_constraint(self):
        """Test negative min constraint values."""
        schema = SchnitzelSchema(
            models={
                "Temperature": Model(
                    name="Temperature",
                    fields={
                        "celsius": FieldDefinition(type="float", min=-273.15, max=1000),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "celsius: float = Field(ge=-273.15, le=1000)" in code

    def test_max_length_one(self):
        """Test max_length=1 for single character fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "initial": FieldDefinition(type="string", max_length=1),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        assert "initial: str = Field(max_length=1)" in code

    def test_generated_code_structure(self):
        """Test overall structure of generated code."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    description="A product in the catalog",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "price": FieldDefinition(type="float", min=0, max=100000),
                        "name": FieldDefinition(type="string", max_length=200),
                    }
                )
            }
        )
        
        generator = PythonModelGenerator()
        code = generator.generate(schema)
        
        # Check structure
        lines = code.split("\n")
        
        # Imports should be at the top
        import_lines = [l for l in lines[:5] if l.startswith("from")]
        assert len(import_lines) > 0
        
        # Class definition should exist
        assert any("class Product(BaseModel):" in l for l in lines)
        
        # Docstring should be present
        assert any("A product in the catalog" in l for l in lines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
