"""Integration tests for F090: Dart generator handles DateTime fields with proper serialization.

Tests that the Dart model generator correctly handles DateTime fields with proper
type mapping and serialization support via json_serializable.

DateTime serialization behavior:
- json_serializable automatically handles DateTime serialization to/from ISO 8601 strings
- No special @JsonKey annotations are needed for basic DateTime serialization
- DateTime is a core Dart type (dart:core), so no additional imports are needed
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartDateTimeTypeMapping:
    """Test DateTime type mapping from schema to Dart."""

    def test_datetime_type_in_dart(self):
        """Test that datetime field has type DateTime in generated Dart code."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should map to DateTime type
        assert "required DateTime createdAt," in code
        # Should generate Event model
        assert "class Event with _$Event" in code

    def test_date_type_maps_to_datetime(self):
        """Test that 'date' type also maps to DateTime."""
        schema = SchnitzelSchema(
            models={
                "Appointment": Model(
                    name="Appointment",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "scheduledDate": FieldDefinition(type="date"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Both 'date' and 'datetime' map to DateTime
        assert "required DateTime scheduledDate," in code

    def test_datetime_vs_date_both_use_datetime(self):
        """Test that both 'datetime' and 'date' types use Dart DateTime."""
        schema = SchnitzelSchema(
            models={
                "Record": Model(
                    name="Record",
                    fields={
                        "timestamp": FieldDefinition(type="datetime"),
                        "eventDate": FieldDefinition(type="date"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Both should map to DateTime
        assert "required DateTime timestamp," in code
        assert "required DateTime eventDate," in code


class TestDartDateTimeOptional:
    """Test optional DateTime field handling."""

    def test_datetime_with_optional(self):
        """Test that optional datetime fields are nullable (DateTime?)."""
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "publishedAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Optional DateTime should be nullable
        assert "DateTime? publishedAt," in code
        # Should NOT have 'required' keyword
        assert "required DateTime? publishedAt," not in code

    def test_required_datetime_field(self):
        """Test that required datetime fields use 'required' keyword."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required DateTime should have 'required' keyword
        assert "required DateTime createdAt," in code

    def test_mixed_required_and_optional_datetime(self):
        """Test model with both required and optional DateTime fields."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "createdAt": FieldDefinition(type="datetime"),
                        "startedAt": FieldDefinition(type="datetime", optional=True),
                        "completedAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required DateTime
        assert "required DateTime createdAt," in code
        # Optional DateTimes
        assert "DateTime? startedAt," in code
        assert "DateTime? completedAt," in code


class TestDartDateTimeSerialization:
    """Test DateTime serialization annotations and behavior."""

    def test_datetime_serialization_annotation(self):
        """Test that DateTime fields work with json_serializable without special annotations.

        json_serializable automatically handles DateTime serialization to/from ISO 8601 strings.
        No @JsonKey annotation is needed unless customizing the serialization behavior.
        """
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "timestamp": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have fromJson factory for serialization
        assert "factory Event.fromJson(Map<String, dynamic> json) => _$EventFromJson(json);" in code
        # DateTime field should be present
        assert "required DateTime timestamp," in code
        # No special converter annotation needed for basic DateTime serialization
        # (json_serializable handles it automatically)

    def test_datetime_with_snake_case_conversion(self):
        """Test that DateTime fields with camelCase names get @JsonKey for snake_case."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "createdAt": FieldDefinition(type="datetime"),
                        "lastLoginAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @JsonKey for snake_case conversion
        assert "@JsonKey(name: 'created_at')" in code
        assert "@JsonKey(name: 'last_login_at')" in code
        # Field names remain camelCase in Dart
        assert "required DateTime createdAt," in code
        assert "DateTime? lastLoginAt," in code

    def test_datetime_already_snake_case(self):
        """Test that DateTime fields already in snake_case don't get @JsonKey."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime"),
                        "updated_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Fields already in snake_case should NOT get @JsonKey
        assert "@JsonKey(name: 'created_at')" not in code
        assert "@JsonKey(name: 'updated_at')" not in code
        # Field names remain as defined
        assert "DateTime created_at" in code
        assert "DateTime updated_at" in code


class TestDartDateTimeComplex:
    """Test DateTime fields in complex scenarios."""

    def test_multiple_datetime_fields(self):
        """Test model with multiple DateTime fields."""
        schema = SchnitzelSchema(
            models={
                "Subscription": Model(
                    name="Subscription",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "createdAt": FieldDefinition(type="datetime"),
                        "updatedAt": FieldDefinition(type="datetime"),
                        "startDate": FieldDefinition(type="date"),
                        "endDate": FieldDefinition(type="date", optional=True),
                        "canceledAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Required DateTimes
        assert "required DateTime createdAt," in code
        assert "required DateTime updatedAt," in code
        assert "required DateTime startDate," in code
        # Optional DateTimes
        assert "DateTime? endDate," in code
        assert "DateTime? canceledAt," in code

    def test_datetime_in_model_with_mixed_types(self):
        """Test DateTime fields alongside other field types."""
        schema = SchnitzelSchema(
            models={
                "Order": Model(
                    name="Order",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "userId": FieldDefinition(type="uuid"),
                        "total": FieldDefinition(type="float"),
                        "status": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime"),
                        "updatedAt": FieldDefinition(type="datetime"),
                        "shippedAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify all fields are present with correct types
        assert "required String id," in code
        assert "required String userId," in code
        assert "required double total," in code
        assert "required String status," in code
        assert "required DateTime createdAt," in code
        assert "required DateTime updatedAt," in code
        assert "DateTime? shippedAt," in code

    def test_multiple_models_with_datetime_fields(self):
        """Test multiple models containing DateTime fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "createdAt": FieldDefinition(type="datetime"),
                        "lastLoginAt": FieldDefinition(type="datetime", optional=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "publishedAt": FieldDefinition(type="datetime"),
                        "scheduledAt": FieldDefinition(type="datetime", optional=True),
                    }
                ),
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify both models have DateTime fields
        assert "class User with _$User" in code
        assert "required DateTime createdAt," in code
        assert "DateTime? lastLoginAt," in code

        assert "class Post with _$Post" in code
        assert "required DateTime publishedAt," in code
        assert "DateTime? scheduledAt," in code


class TestDartDateTimeImports:
    """Test that DateTime doesn't require additional imports."""

    def test_datetime_requires_no_additional_imports(self):
        """Test that DateTime fields don't require additional imports.

        DateTime is part of dart:core, so no import is needed.
        """
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "timestamp": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have standard Freezed imports
        assert "import 'package:freezed_annotation/freezed_annotation.dart';" in code
        assert "import 'package:json_annotation/json_annotation.dart';" in code
        # DateTime is built-in, no additional import needed
        # No import like "import 'dart:core';" should be present
        assert "import 'dart:core';" not in code

    def test_datetime_with_part_directives(self):
        """Test that DateTime fields work with generated part files."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "timestamp": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have part directives for code generation
        assert "part 'models.freezed.dart';" in code
        assert "part 'models.g.dart';" in code


class TestDartDateTimeFreezedStructure:
    """Test DateTime fields within Freezed model structure."""

    def test_datetime_in_freezed_factory_constructor(self):
        """Test that DateTime fields are properly included in factory constructor."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "startTime": FieldDefinition(type="datetime"),
                        "endTime": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have factory constructor
        assert "const factory Event({" in code
        assert "required String id," in code
        assert "required String name," in code
        assert "required DateTime startTime," in code
        assert "required DateTime endTime," in code
        assert "}) = _Event;" in code

    def test_datetime_with_freezed_annotation(self):
        """Test that models with DateTime fields have @freezed annotation."""
        schema = SchnitzelSchema(
            models={
                "Meeting": Model(
                    name="Meeting",
                    fields={
                        "scheduledAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have @freezed annotation
        assert "@freezed" in code
        assert "class Meeting with _$Meeting {" in code

    def test_datetime_with_from_json_factory(self):
        """Test that DateTime fields work with fromJson factory."""
        schema = SchnitzelSchema(
            models={
                "Timestamp": Model(
                    name="Timestamp",
                    fields={
                        "value": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have fromJson factory
        assert "factory Timestamp.fromJson(Map<String, dynamic> json) => _$TimestampFromJson(json);" in code
        # DateTime field should be present
        assert "required DateTime value," in code


class TestDartDateTimeEdgeCases:
    """Test edge cases for DateTime field handling."""

    def test_datetime_only_model(self):
        """Test a model with only DateTime fields."""
        schema = SchnitzelSchema(
            models={
                "TimeRange": Model(
                    name="TimeRange",
                    fields={
                        "start": FieldDefinition(type="datetime"),
                        "end": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should generate successfully
        assert "class TimeRange with _$TimeRange" in code
        assert "required DateTime start," in code
        assert "required DateTime end," in code

    def test_datetime_case_sensitivity(self):
        """Test that DateTime type mapping is case-insensitive."""
        # The _get_dart_type method uses .lower() for comparison
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "timestamp": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should work with lowercase 'datetime'
        assert "required DateTime timestamp," in code

    def test_datetime_all_optional(self):
        """Test model where all DateTime fields are optional."""
        schema = SchnitzelSchema(
            models={
                "Audit": Model(
                    name="Audit",
                    fields={
                        "createdAt": FieldDefinition(type="datetime", optional=True),
                        "updatedAt": FieldDefinition(type="datetime", optional=True),
                        "deletedAt": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All should be nullable
        assert "DateTime? createdAt," in code
        assert "DateTime? updatedAt," in code
        assert "DateTime? deletedAt," in code
        # None should have 'required' keyword
        assert "required DateTime?" not in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
