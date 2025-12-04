"""Integration tests for F034: Dart model generator handles default values correctly."""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartDefaultValues:
    """Test default value handling in Dart Freezed model generation."""

    def test_string_default_value(self):
        """Test that string defaults use single quotes and are properly formatted."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "language": FieldDefinition(type="string", default="en"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @Default annotation with single quotes
        assert "@Default('en')" in code
        assert "String language," in code
        # Verify double quotes are NOT used
        assert '@Default("en")' not in code

    def test_bool_default_value(self):
        """Test that boolean defaults use lowercase true/false."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "isEnabled": FieldDefinition(type="bool", default=True),
                        "isDeleted": FieldDefinition(type="bool", default=False),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify lowercase boolean values
        assert "@Default(true)" in code
        assert "@Default(false)" in code
        # Verify NOT uppercase (Python style)
        assert "@Default(True)" not in code
        assert "@Default(False)" not in code

    def test_int_default_value(self):
        """Test that integer defaults are unquoted."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "count": FieldDefinition(type="int", default=0),
                        "stock": FieldDefinition(type="int", default=100),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify unquoted integers
        assert "@Default(0)" in code
        assert "@Default(100)" in code
        # Verify NOT quoted
        assert "@Default('0')" not in code
        assert "@Default('100')" not in code

    def test_float_default_value(self):
        """Test that float defaults are unquoted."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "price": FieldDefinition(type="float", default=9.99),
                        "discount": FieldDefinition(type="float", default=0.0),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify unquoted floats
        assert "@Default(9.99)" in code
        assert "@Default(0.0)" in code
        # Verify NOT quoted
        assert "@Default('9.99')" not in code

    def test_list_default_value(self):
        """Test that list defaults are properly formatted."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>", default=[]),
                        "categories": FieldDefinition(type="list<string>", default=["a", "b"]),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify empty list
        assert "@Default([])" in code
        # Verify list with string items (using single quotes)
        assert "@Default(['a', 'b'])" in code

    def test_default_makes_field_not_required(self):
        """Test that fields with defaults do not have 'required' keyword."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "language": FieldDefinition(type="string", default="en"),
                        "name": FieldDefinition(type="string"),  # No default
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Field with default should NOT have required keyword
        assert "@Default('en') String language," in code
        assert "required" not in code.split("language")[0].split("\n")[-1]

        # Field without default SHOULD have required keyword
        assert "required String name," in code

    def test_multiple_defaults_in_model(self):
        """Test a model with multiple fields having different default types."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "isEnabled": FieldDefinition(type="bool", default=True),
                        "language": FieldDefinition(type="string", default="en"),
                        "count": FieldDefinition(type="int", default=0),
                        "tags": FieldDefinition(type="list<string>", default=[]),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all defaults are present
        assert "@Default(true)" in code
        assert "@Default('en')" in code
        assert "@Default(0)" in code
        assert "@Default([])" in code

    def test_optional_with_default(self):
        """Test that optional fields with defaults are handled correctly."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string", optional=True, default="No bio"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @Default but NOT nullable type (String not String?)
        assert "@Default('No bio')" in code
        assert "String bio," in code
        # Should NOT be nullable since it has a default
        assert "String? bio" not in code

    def test_optional_without_default(self):
        """Test that optional fields without defaults are nullable."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should be nullable and NOT have required keyword
        assert "String? bio," in code
        assert "@Default" not in code.split("bio")[0].split("\n")[-1]
        assert "required" not in code.split("bio")[0].split("\n")[-1]

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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Empty string should still be quoted
        assert "@Default('')" in code

    def test_string_with_quotes_escaped(self):
        """Test that strings with quotes are properly escaped."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Message": Model(
                    name="Message",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "template": FieldDefinition(type="string", default="Hello 'World'"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Single quotes in string should be escaped
        assert "@Default('Hello \\'World\\'')" in code

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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Negative numbers should be unquoted
        assert "@Default(-273.15)" in code

    def test_list_with_mixed_types(self):
        """Test that lists with different item types are formatted correctly."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Config": Model(
                    name="Config",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "numbers": FieldDefinition(type="list<int>", default=[1, 2, 3]),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # List of numbers should not have quotes around numbers
        assert "@Default([1, 2, 3])" in code

    def test_field_without_default_is_required(self):
        """Test that fields without defaults are marked as required."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),  # No default
                        "email": FieldDefinition(type="string"),  # No default
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Both fields should be required
        assert "required String name," in code
        assert "required String email," in code

    def test_default_with_camelcase_field(self):
        """Test that defaults work with camelCase field names that need @JsonKey."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "firstName": FieldDefinition(type="string", default="John"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have both @JsonKey and @Default annotations
        assert "@JsonKey(name: 'first_name')" in code
        assert "@Default('John')" in code
        assert "String firstName," in code


class TestDartDefaultValueEdgeCases:
    """Test edge cases for Dart default value handling."""

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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Zero should be unquoted
        assert "@Default(0)" in code
        assert "@Default(0.0)" in code

    def test_false_as_default(self):
        """Test that false (boolean) is correctly handled as a default."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "isEnabled": FieldDefinition(type="bool", default=False),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # False should be lowercase and unquoted
        assert "@Default(false)" in code
        assert "@Default(False)" not in code

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

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify both models have correct defaults
        assert "@Default('active')" in code
        assert "@Default(0)" in code
        assert "class User with _$User" in code
        assert "class Post with _$Post" in code
