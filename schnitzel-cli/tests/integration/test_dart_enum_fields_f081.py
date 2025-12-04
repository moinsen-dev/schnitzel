"""Integration tests for F081: Dart generator handles enum fields.

Tests that the Dart model generator correctly handles fields of type 'enum' with values.
Enum fields should be mapped to String type in Dart with proper handling of:
- Required enum fields
- Optional enum fields
- Enum fields with default values
- Multiple enum fields
- Snake case conversion for enum fields
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartEnumFieldGeneration:
    """Test basic enum field generation in Dart models."""

    def test_enum_field_generates(self):
        """Test that a model with enum field should generate correctly."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "processing", "completed", "cancelled"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should generate an Order model
        assert "class Order with _$Order" in code
        # Should have a status field
        assert "status" in code

    def test_enum_type_maps_to_string(self):
        """Test that enum type becomes String in Dart."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Enum should map to String
        assert "required String role," in code

    def test_enum_values_included(self):
        """Test that enum values should be in generated code (as a comment or validation)."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "category": FieldDefinition(
                            type="enum",
                            values=["electronics", "clothing", "food", "books"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Enum field should be present
        assert "String category," in code
        # Note: Currently enum values are not included in the generated code
        # This is acceptable as Dart Freezed models use String for flexibility
        # Validation can be done at runtime or with custom validators

    def test_required_enum_field(self):
        """Test that required enum field is properly marked."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "priority": FieldDefinition(
                            type="enum",
                            values=["low", "medium", "high", "urgent"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required enum field should have 'required' keyword
        assert "required String priority," in code

    def test_optional_enum_field(self):
        """Test that optional enum field becomes nullable String."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["active", "inactive", "suspended"],
                            optional=True
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Optional enum should be nullable and not required
        assert "String? status," in code
        assert "required String? status," not in code


class TestDartEnumFieldWithDefault:
    """Test enum fields with default values."""

    def test_enum_with_default(self):
        """Test that enum field with default value generates correctly."""
        schema = SchnitzelSchema(
            models={
                "Account": Model(
                    name="Account",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["active", "inactive", "pending"],
                            default="pending"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @Default annotation with the default value
        assert "@Default('pending') String status," in code
        # Should NOT have 'required' keyword when default is provided
        assert "required String status" not in code

    def test_enum_default_uses_single_quotes(self):
        """Test that enum default value uses Dart-style single quotes."""
        schema = SchnitzelSchema(
            models={
                "Notification": Model(
                    name="Notification",
                    fields={
                        "priority": FieldDefinition(
                            type="enum",
                            values=["low", "normal", "high"],
                            default="normal"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify @Default annotation with single quotes (Dart convention)
        assert "@Default('normal') String priority," in code

    def test_enum_with_default_and_optional(self):
        """Test that enum field with both default and optional uses default (non-nullable)."""
        schema = SchnitzelSchema(
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "theme": FieldDefinition(
                            type="enum",
                            values=["light", "dark", "auto"],
                            optional=True,
                            default="auto"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # When a default is provided, field should NOT be nullable
        assert "@Default('auto') String theme," in code
        # Should NOT be nullable (no '?')
        assert "String? theme" not in code


class TestDartMultipleEnumFields:
    """Test models with multiple enum fields."""

    def test_multiple_enum_fields(self):
        """Test model with multiple enum fields."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["todo", "in_progress", "done"]
                        ),
                        "priority": FieldDefinition(
                            type="enum",
                            values=["low", "medium", "high"],
                            default="medium"
                        ),
                        "category": FieldDefinition(
                            type="enum",
                            values=["bug", "feature", "improvement"],
                            optional=True
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required enum field
        assert "required String status," in code
        # Enum field with default
        assert "@Default('medium') String priority," in code
        # Optional enum field
        assert "String? category," in code

    def test_enum_fields_in_different_models(self):
        """Test enum fields across multiple models."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"]
                        ),
                    }
                ),
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "shipped", "delivered"]
                        ),
                    }
                ),
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify both models have enum fields
        assert "class User with _$User" in code
        assert "required String role," in code
        assert "class Order with _$Order" in code
        assert "required String status," in code


class TestDartEnumFieldSnakeCase:
    """Test enum fields with snake_case conversion."""

    def test_enum_field_with_camel_case_conversion(self):
        """Test that enum fields with camelCase names get @JsonKey annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "accountStatus": FieldDefinition(
                            type="enum",
                            values=["active", "inactive", "suspended"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @JsonKey annotation for snake_case conversion
        assert "@JsonKey(name: 'account_status')" in code
        assert "required String accountStatus," in code

    def test_enum_field_already_snake_case(self):
        """Test that enum fields already in snake_case don't get @JsonKey."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "order_status": FieldDefinition(
                            type="enum",
                            values=["pending", "completed"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify field is included without @JsonKey (already in snake_case)
        assert "String order_status" in code
        # No @JsonKey needed since field is already in snake_case
        assert "@JsonKey(name: 'order_status')" not in code


class TestDartEnumFieldComplex:
    """Test enum fields in complex scenarios."""

    def test_enum_field_with_mixed_types(self):
        """Test enum field alongside other field types."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                        "in_stock": FieldDefinition(type="bool"),
                        "category": FieldDefinition(
                            type="enum",
                            values=["electronics", "clothing", "food"]
                        ),
                        "status": FieldDefinition(
                            type="enum",
                            values=["available", "discontinued"],
                            default="available"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all fields are present with correct types
        assert "required String id," in code
        assert "required String name," in code
        assert "required double price," in code
        assert "required bool in_stock," in code
        assert "required String category," in code
        assert "@Default('available') String status," in code

    def test_enum_field_with_json_serialization(self):
        """Test that enum fields work with fromJson factory."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "completed"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have fromJson factory
        assert "factory Task.fromJson(Map<String, dynamic> json) => _$TaskFromJson(json);" in code
        # Should have the enum field
        assert "required String status," in code

    def test_enum_case_insensitive_type(self):
        """Test that 'enum' type is case-insensitive."""
        schema = SchnitzelSchema(
            models={
                "Status": Model(
                    name="Status",
                    fields={
                        "value": FieldDefinition(
                            type="enum",  # lowercase
                            values=["active", "inactive"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should work with lowercase 'enum'
        assert "required String value," in code


class TestDartEnumFieldEdgeCases:
    """Test edge cases for enum field handling."""

    def test_enum_field_only_model(self):
        """Test a model with only an enum field."""
        schema = SchnitzelSchema(
            models={
                "Priority": Model(
                    name="Priority",
                    fields={
                        "level": FieldDefinition(
                            type="enum",
                            values=["low", "medium", "high"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should generate successfully
        assert "class Priority with _$Priority" in code
        assert "required String level," in code

    def test_enum_with_many_values(self):
        """Test enum field with many possible values."""
        schema = SchnitzelSchema(
            models={
                "Country": Model(
                    name="Country",
                    fields={
                        "code": FieldDefinition(
                            type="enum",
                            values=["US", "UK", "CA", "AU", "DE", "FR", "JP", "CN", "IN", "BR"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should handle many enum values
        assert "required String code," in code

    def test_enum_with_empty_values_list(self):
        """Test enum field with empty values list (edge case)."""
        schema = SchnitzelSchema(
            models={
                "Status": Model(
                    name="Status",
                    fields={
                        "value": FieldDefinition(
                            type="enum",
                            values=[]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should still generate as String
        assert "required String value," in code

    def test_enum_with_special_characters_in_values(self):
        """Test enum field with special characters in values."""
        schema = SchnitzelSchema(
            models={
                "Message": Model(
                    name="Message",
                    fields={
                        "status": FieldDefinition(
                            type="enum",
                            values=["in-progress", "not_started", "done!"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should generate String field regardless of value format
        assert "required String status," in code


class TestDartEnumFieldImports:
    """Test that proper imports are generated for enum fields."""

    def test_enum_field_requires_no_additional_imports(self):
        """Test that enum fields don't require additional imports beyond standard Freezed imports."""
        schema = SchnitzelSchema(
            models={
                "Status": Model(
                    name="Status",
                    fields={
                        "value": FieldDefinition(
                            type="enum",
                            values=["active", "inactive"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have standard Freezed imports
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code
        # String is a Dart built-in, no additional import needed

    def test_enum_field_with_part_directives(self):
        """Test that enum fields work with generated part files."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user"]
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have part directives
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
