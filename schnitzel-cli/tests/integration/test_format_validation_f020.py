"""Test F020: Schema validator validates format constraints for string fields."""

import pytest
from schnitzel.schema import SchemaValidator, ValidationResult
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


def test_valid_email_format():
    """Test that validator accepts 'email' format on string field."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True, f"Expected validation to pass but got errors: {result.errors}"
    assert result.errors == []


def test_valid_phone_format():
    """Test that validator accepts 'phone' format on string field."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "phone": FieldDefinition(type="string", format="phone"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_multiple_format_constraints():
    """Test model with multiple fields having different format constraints."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email"),
                    "phone": FieldDefinition(type="string", format="phone"),
                    "website": FieldDefinition(type="string", format="url"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_all_supported_formats():
    """Test that all supported formats are recognized."""
    supported_formats = [
        "email", "phone", "url", "uri", "uuid",
        "date", "time", "datetime", "ip", "ipv4", "ipv6"
    ]

    for format_type in supported_formats:
        schema = SchnitzelSchema(
            models={
                "TestModel": Model(
                    name="TestModel",
                    fields={
                        "field": FieldDefinition(type="string", format=format_type),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is True, (
            f"Format '{format_type}' should be supported but validation failed: {result.errors}"
        )
        assert result.errors == []


def test_unsupported_format_rejected():
    """Test that unsupported format is rejected with helpful error."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "email": FieldDefinition(type="string", format="e-mail"),  # Invalid
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should fail validation
    assert result.valid is False
    assert len(result.errors) > 0

    error_message = "\n".join(result.errors)

    # Verify error message components
    assert "e-mail" in error_message, "Error should mention the unsupported format"
    assert "email" in error_message.lower(), "Error should mention field name"
    assert "User" in error_message, "Error should mention model name"
    assert "Supported formats:" in error_message, "Error should list supported formats"


def test_format_on_non_string_field_rejected():
    """Test that format constraint on non-string field is rejected."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "age": FieldDefinition(type="int", format="email"),  # Invalid - int with format
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should fail validation
    assert result.valid is False
    assert len(result.errors) > 0

    error_message = "\n".join(result.errors)

    # Verify error explains format is only for string fields
    assert "string" in error_message.lower(), "Error should mention string fields"
    assert "age" in error_message, "Error should mention field name"
    assert "User" in error_message, "Error should mention model name"
    assert "int" in error_message, "Error should mention the actual field type"


def test_error_message_lists_supported_formats():
    """Test that error message lists all supported formats."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "data": FieldDefinition(type="string", format="invalid_format"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    assert result.valid is False
    error_message = "\n".join(result.errors)

    # Verify all supported formats are listed
    assert "email" in error_message
    assert "phone" in error_message
    assert "url" in error_message
    assert "uri" in error_message
    assert "uuid" in error_message
    assert "date" in error_message
    assert "time" in error_message
    assert "datetime" in error_message
    assert "ip" in error_message
    assert "ipv4" in error_message
    assert "ipv6" in error_message


def test_format_suggestions_for_common_typos():
    """Test that validator suggests correct format for common typos."""
    test_cases = [
        ("e-mail", ["email"]),
        ("mail", ["email"]),
        ("telephone", ["phone"]),
        ("tel", ["phone"]),
        ("website", ["url"]),
        ("ipaddress", ["ip"]),
    ]

    for invalid_format, expected_suggestions in test_cases:
        schema = SchnitzelSchema(
            models={
                "TestModel": Model(
                    name="TestModel",
                    fields={
                        "field": FieldDefinition(type="string", format=invalid_format),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is False
        error_message = "\n".join(result.errors)

        # Verify at least one expected suggestion appears
        has_suggestion = any(
            suggestion in error_message for suggestion in expected_suggestions
        )
        assert has_suggestion, (
            f"Error should suggest one of {expected_suggestions} for '{invalid_format}'"
        )


def test_string_field_without_format_is_valid():
    """Test that string fields without format constraint are valid."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),  # No format - should be valid
                    "bio": FieldDefinition(type="string", optional=True),  # No format - should be valid
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_complex_schema_with_mixed_format_usage():
    """Test complex schema with some fields having formats and some without."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="email"),
                    "name": FieldDefinition(type="string"),  # No format
                    "phone": FieldDefinition(type="string", format="phone", optional=True),
                    "bio": FieldDefinition(type="string", optional=True),  # No format
                }
            ),
            "Company": Model(
                name="Company",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "name": FieldDefinition(type="string"),
                    "website": FieldDefinition(type="string", format="url"),
                    "description": FieldDefinition(type="string"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_format_validation_with_other_field_constraints():
    """Test that format validation works alongside other field constraints."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(
                        type="string",
                        format="email",
                        unique=True,
                        optional=False
                    ),
                    "phone": FieldDefinition(
                        type="string",
                        format="phone",
                        optional=True,
                        default=None
                    ),
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should pass validation
    assert result.valid is True
    assert result.errors == []


def test_multiple_models_with_format_errors():
    """Test that validator catches format errors across multiple models."""
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "email": FieldDefinition(type="string", format="e-mail"),  # Invalid
                }
            ),
            "Company": Model(
                name="Company",
                fields={
                    "id": FieldDefinition(type="uuid", primary=True),
                    "website": FieldDefinition(type="int", format="url"),  # Invalid - int with format
                }
            )
        }
    )

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should have validation errors
    assert result.valid is False
    assert len(result.errors) >= 2, "Should have at least 2 errors (one per model)"

    error_message = "\n".join(result.errors)
    assert "e-mail" in error_message
    assert "User" in error_message
    assert "Company" in error_message


def test_url_and_uri_formats_are_distinct():
    """Test that both 'url' and 'uri' formats are supported as distinct types."""
    # Test url format
    schema_url = SchnitzelSchema(
        models={
            "Resource": Model(
                name="Resource",
                fields={
                    "link": FieldDefinition(type="string", format="url"),
                }
            )
        }
    )

    validator = SchemaValidator()
    result_url = validator.validate(schema_url)
    assert result_url.valid is True

    # Test uri format
    schema_uri = SchnitzelSchema(
        models={
            "Resource": Model(
                name="Resource",
                fields={
                    "identifier": FieldDefinition(type="string", format="uri"),
                }
            )
        }
    )

    result_uri = validator.validate(schema_uri)
    assert result_uri.valid is True


def test_ip_formats_validation():
    """Test that all IP address formats (ip, ipv4, ipv6) are supported."""
    ip_formats = ["ip", "ipv4", "ipv6"]

    for ip_format in ip_formats:
        schema = SchnitzelSchema(
            models={
                "Server": Model(
                    name="Server",
                    fields={
                        "address": FieldDefinition(type="string", format=ip_format),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is True, f"IP format '{ip_format}' should be valid"
        assert result.errors == []


def test_datetime_related_formats():
    """Test that date, time, and datetime formats are all supported."""
    temporal_formats = ["date", "time", "datetime"]

    for temporal_format in temporal_formats:
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "timestamp": FieldDefinition(type="string", format=temporal_format),
                    }
                )
            }
        )

        validator = SchemaValidator()
        result = validator.validate(schema)

        assert result.valid is True, f"Temporal format '{temporal_format}' should be valid"
        assert result.errors == []
