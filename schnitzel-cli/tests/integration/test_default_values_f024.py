"""Integration tests for F024: Python model generator handles default values correctly."""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


class TestDefaultValues:
    """Test default value handling in Python model generation."""

    def test_string_default_uses_double_quotes(self):
        """Test that string defaults are quoted with double quotes."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(type="string", default="active"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify double quotes are used
        assert 'status: str = "active"' in code
        # Verify single quotes are NOT used
        assert "status: str = 'active'" not in code

    def test_numeric_defaults_unquoted(self):
        """Test that numeric defaults are not quoted."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "count": FieldDefinition(type="int", default=0),
                        "price": FieldDefinition(type="float", default=9.99),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify int default is unquoted
        assert "count: int = 0" in code
        assert 'count: int = "0"' not in code

        # Verify float default is unquoted
        assert "price: float = 9.99" in code
        assert 'price: float = "9.99"' not in code

    def test_boolean_defaults_unquoted_and_capitalized(self):
        """Test that boolean defaults are unquoted and use Python capitalization."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "is_active": FieldDefinition(type="bool", default=True),
                        "is_deleted": FieldDefinition(type="bool", default=False),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify True/False (not true/false or "True"/"False")
        assert "is_active: bool = True" in code
        assert "is_deleted: bool = False" in code
        assert "true" not in code.lower() or "True" in code  # Ensure Python-style
        assert 'is_active: bool = "True"' not in code

    def test_optional_with_explicit_default_uses_default_not_none(self):
        """Test that optional fields with explicit defaults use the default, not None."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(
                            type="string",
                            optional=True,
                            default="No bio provided"
                        ),
                        "age": FieldDefinition(
                            type="int",
                            optional=True,
                            default=0
                        ),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify explicit defaults are used
        assert '= "No bio provided"' in code
        assert "age: int | None = 0" in code

        # Verify None is NOT used when explicit default is present
        assert "bio: str | None = None" not in code

    def test_optional_without_default_gets_none(self):
        """Test that optional fields without explicit defaults get None."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                        "phone": FieldDefinition(type="string", optional=True),
                        "website": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify optional fields without defaults get None
        assert "phone: str | None = None" in code
        assert "website: str | None = None" in code

        # Required field should not have default
        assert "email: str\n" in code or "email: str = " not in code

    def test_required_field_with_default(self):
        """Test that required fields can have defaults."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "status": FieldDefinition(
                            type="string",
                            required=True,
                            default="pending"
                        ),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Required field with default should have the default
        assert 'status: str = "pending"' in code

    def test_string_with_special_characters_escaped(self):
        """Test that strings with special characters are properly escaped."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Message": Model(
                    name="Message",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "template": FieldDefinition(
                            type="string",
                            default='Hello "World"'
                        ),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify quotes are escaped
        assert 'template: str = "Hello \\"World\\""' in code

    def test_mixed_field_types_with_defaults(self):
        """Test all supported field types with defaults."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Example": Model(
                    name="Example",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", default="unnamed"),
                        "count": FieldDefinition(type="int", default=0),
                        "score": FieldDefinition(type="float", default=0.0),
                        "enabled": FieldDefinition(type="bool", default=True),
                        "metadata": FieldDefinition(type="json", default={}),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify all defaults are formatted correctly
        assert 'name: str = "unnamed"' in code
        assert "count: int = 0" in code
        assert "score: float = 0.0" in code
        assert "enabled: bool = True" in code
        assert "metadata: dict[str, Any] = {}" in code

    def test_default_with_constraints_uses_field(self):
        """Test that fields with both defaults and constraints use Field()."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "price": FieldDefinition(
                            type="float",
                            min=0,
                            max=10000,
                            default=0.0
                        ),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # When there are constraints, Field() should be used
        assert "Field(" in code
        assert "ge=0" in code
        assert "le=10000" in code
        assert 'default=0.0' in code or "default=0.0" in code

    def test_multiple_models_with_defaults(self):
        """Test multiple models with various default configurations."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(type="string", default="active"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "views": FieldDefinition(type="int", default=0),
                    }
                ),
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify both models have correct defaults
        assert 'status: str = "active"' in code
        assert "views: int = 0" in code
        assert "class User(BaseModel):" in code
        assert "class Post(BaseModel):" in code

    def test_none_as_default(self):
        """Test that None can be used as an explicit default."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "nickname": FieldDefinition(
                            type="string",
                            optional=True,
                            default=None
                        ),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify None is unquoted
        assert "nickname: str | None = None" in code
        assert 'nickname: str | None = "None"' not in code


class TestDefaultValueEdgeCases:
    """Test edge cases for default value handling."""

    def test_empty_string_default(self):
        """Test that empty string defaults are handled correctly."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string", default=""),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Empty string should still be quoted
        assert 'bio: str = ""' in code

    def test_zero_as_default(self):
        """Test that 0 (zero) is correctly handled as a default."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Counter": Model(
                    name="Counter",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "count": FieldDefinition(type="int", default=0),
                        "balance": FieldDefinition(type="float", default=0.0),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Zero should be unquoted
        assert "count: int = 0" in code
        assert "balance: float = 0.0" in code

    def test_negative_number_default(self):
        """Test that negative numbers are handled correctly."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Temperature": Model(
                    name="Temperature",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "celsius": FieldDefinition(type="float", default=-273.15),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Negative numbers should be unquoted
        assert "celsius: float = -273.15" in code
