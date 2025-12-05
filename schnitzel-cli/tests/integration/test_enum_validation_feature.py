"""
Test enum value consistency validation.

Feature ID: 6ad02136-810f-466b-a48d-062a865e5d07
Description: Validate command checks enum value consistency

Tests that the validate command verifies:
1. Enum fields have a values list defined
2. Enum default values are valid enum values (in the values list)
3. Multiple enum fields are validated correctly
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.schema.validator import SchemaValidator


class TestEnumValueConsistency:
    """Test that enum default values must be in the values list."""

    def test_enum_with_invalid_default_value_fails(self):
        """Test that enum with default not in values list fails validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"],
                            default="superadmin"  # Invalid - not in values
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert not result.valid
        assert len(result.errors) == 1
        assert "Invalid default value for enum field 'role'" in result.errors[0]
        assert "superadmin" in result.errors[0]
        assert "admin, user, guest" in result.errors[0]

    def test_enum_with_valid_default_value_passes(self):
        """Test that enum with valid default value passes validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"],
                            default="admin"  # Valid - in values list
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid
        assert len(result.errors) == 0

    def test_enum_without_default_passes(self):
        """Test that enum without default value passes validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"]
                            # No default specified - this is valid
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid
        assert len(result.errors) == 0

    def test_enum_default_is_case_sensitive(self):
        """Test that enum default value matching is case-sensitive."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"],
                            default="Admin"  # Different case - should fail
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert not result.valid
        assert len(result.errors) == 1
        assert "Invalid default value for enum field 'role'" in result.errors[0]
        assert "Admin" in result.errors[0]


class TestEnumValuesList:
    """Test that enum fields must have values defined."""

    def test_enum_without_values_list_fails(self):
        """Test that enum without values list fails validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            default="admin"
                            # No values defined - should fail
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert not result.valid
        assert len(result.errors) == 1
        assert "Enum field 'role' in model 'User' must have values defined" in result.errors[0]
        assert "values" in result.errors[0].lower()

    def test_enum_with_empty_values_list_fails(self):
        """Test that enum with empty values list fails validation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=[]  # Empty list - should fail
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert not result.valid
        assert len(result.errors) == 1
        assert "must have values defined" in result.errors[0]

    def test_enum_with_values_but_no_default_passes(self):
        """Test that enum with values but no default passes."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"]
                            # Has values, no default - this is valid
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid
        assert len(result.errors) == 0


class TestMultipleEnumFields:
    """Test validation of multiple enum fields."""

    def test_multiple_valid_enum_fields_pass(self):
        """Test that multiple valid enum fields pass validation."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "confirmed", "delivered"],
                            default="pending"
                        ),
                        "priority": FieldDefinition(
                            type="enum",
                            values=["low", "medium", "high"],
                            default="medium"
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid
        assert len(result.errors) == 0

    def test_one_invalid_enum_among_multiple_fails(self):
        """Test that one invalid enum among multiple causes validation failure."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "confirmed", "delivered"],
                            default="pending"  # Valid
                        ),
                        "priority": FieldDefinition(
                            type="enum",
                            values=["low", "medium", "high"],
                            default="urgent"  # Invalid
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert not result.valid
        assert len(result.errors) == 1
        assert "priority" in result.errors[0]
        assert "urgent" in result.errors[0]

    def test_enum_fields_across_multiple_models(self):
        """Test enum validation across multiple models."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "role": FieldDefinition(
                            type="enum",
                            values=["admin", "user", "guest"],
                            default="user"
                        )
                    }
                ),
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="enum",
                            values=["pending", "confirmed", "delivered"],
                            default="pending"
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid
        assert len(result.errors) == 0


class TestEnumWithOtherFieldTypes:
    """Test enum validation alongside other field types."""

    def test_enum_with_various_field_types(self):
        """Test that enum validation works alongside other field types."""
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
                            values=["electronics", "clothing", "food"],
                            default="electronics"
                        ),
                        "status": FieldDefinition(
                            type="enum",
                            values=["available", "out_of_stock", "discontinued"],
                            default="available"
                        )
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid
        assert len(result.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
