"""Integration tests for F089: Python generator handles datetime fields with proper imports.

Feature: F089
Requirements:
- Python model generator should add 'from datetime import datetime' when datetime fields exist
- Generated code should use datetime type correctly
- No datetime import when no datetime fields are present

Test Requirements:
- test_datetime_import_present - 'from datetime import datetime' should be in output
- test_datetime_type_correct - field should have type datetime
- test_no_datetime_import_when_not_needed - no import if no datetime fields
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.models import PythonModelGenerator


class TestPythonDatetimeImports:
    """Test Python model generator datetime field handling and imports."""

    def test_datetime_import_present(self):
        """Test that 'from datetime import datetime' is present when datetime fields exist."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "scheduled_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with datetime field:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import is present
        assert "from datetime import datetime" in code, \
            "datetime import should be present when datetime fields exist"

    def test_datetime_type_correct(self):
        """Test that datetime field has correct type annotation."""
        schema = SchnitzelSchema(
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "title": FieldDefinition(type="string"),
                        "published_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code for datetime type check:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify field has datetime type
        assert "published_at: datetime" in code, \
            "Field should have datetime type annotation"

        # Verify datetime import is present
        assert "from datetime import datetime" in code, \
            "datetime import should be present"

    def test_no_datetime_import_when_not_needed(self):
        """Test that datetime import is NOT present when no datetime fields exist."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                        "in_stock": FieldDefinition(type="bool"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code without datetime fields:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import is NOT present
        assert "from datetime import datetime" not in code, \
            "datetime import should NOT be present when no datetime fields exist"

        # Verify other imports are still present
        assert "from uuid import UUID" in code, \
            "UUID import should still be present"
        assert "from pydantic import BaseModel" in code, \
            "BaseModel import should be present"

    def test_multiple_datetime_fields(self):
        """Test that datetime import is present with multiple datetime fields."""
        schema = SchnitzelSchema(
            models={
                "Audit": Model(
                    name="Audit",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "created_at": FieldDefinition(type="datetime"),
                        "updated_at": FieldDefinition(type="datetime"),
                        "deleted_at": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with multiple datetime fields:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import appears only once
        import_lines = [line for line in code.split('\n') if 'from datetime import datetime' in line]
        assert len(import_lines) == 1, \
            "datetime import should appear exactly once"

        # Verify all datetime fields have correct type
        assert "created_at: datetime" in code
        assert "updated_at: datetime" in code
        assert "deleted_at: datetime | None" in code, \
            "Optional datetime field should use | None syntax"

    def test_datetime_in_list_type(self):
        """Test that datetime import is present for list<datetime> fields."""
        schema = SchnitzelSchema(
            models={
                "Schedule": Model(
                    name="Schedule",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "time_slots": FieldDefinition(type="list<datetime>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with list<datetime> field:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import is present
        assert "from datetime import datetime" in code, \
            "datetime import should be present for list<datetime> fields"

        # Verify list<datetime> maps to list[datetime]
        assert "time_slots: list[datetime]" in code, \
            "list<datetime> should map to list[datetime]"

    def test_datetime_with_optional_and_default(self):
        """Test datetime field with optional and default value."""
        schema = SchnitzelSchema(
            models={
                "Log": Model(
                    name="Log",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "message": FieldDefinition(type="string"),
                        "logged_at": FieldDefinition(type="datetime", optional=True, default=None),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with optional datetime field:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import is present
        assert "from datetime import datetime" in code

        # Verify optional datetime field with default
        assert "logged_at: datetime | None = None" in code, \
            "Optional datetime with default should use | None = None syntax"

    def test_datetime_across_multiple_models(self):
        """Test that datetime import is present when datetime fields exist across multiple models."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "published_at": FieldDefinition(type="datetime", optional=True),
                    }
                ),
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with datetime across multiple models:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import appears only once
        import_lines = [line for line in code.split('\n') if 'from datetime import datetime' in line]
        assert len(import_lines) == 1, \
            "datetime import should appear exactly once even with multiple models"

        # Verify datetime fields in different models
        assert "created_at: datetime" in code
        assert "published_at: datetime | None" in code

    def test_datetime_with_auto_create(self):
        """Test datetime field with auto='create' attribute."""
        schema = SchnitzelSchema(
            models={
                "Record": Model(
                    name="Record",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "data": FieldDefinition(type="string"),
                        "created_at": FieldDefinition(type="datetime", auto="create"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with auto='create' datetime field:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import is present
        assert "from datetime import datetime" in code

        # Verify datetime field is present (auto attribute doesn't affect type)
        assert "created_at: datetime" in code

    def test_datetime_with_auto_update(self):
        """Test datetime field with auto='update' attribute."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                        "updated_at": FieldDefinition(type="datetime", auto="update", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code with auto='update' datetime field:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify datetime import is present
        assert "from datetime import datetime" in code

        # Verify optional datetime field
        assert "updated_at: datetime | None" in code

    def test_generated_code_is_valid_python(self):
        """Test that generated code with datetime fields is valid Python."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "due_date": FieldDefinition(type="datetime"),
                        "completed_at": FieldDefinition(type="datetime", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code for syntax validation:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        # Verify the code is valid Python by compiling it
        try:
            compile(code, "<string>", "exec")
            print("\nGenerated code is valid Python!")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

        # Verify datetime import
        assert "from datetime import datetime" in code

    def test_datetime_import_placement(self):
        """Test that datetime import is placed in correct location (not in __future__ section)."""
        schema = SchnitzelSchema(
            models={
                "Notification": Model(
                    name="Notification",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "message": FieldDefinition(type="string"),
                        "sent_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        print("\nGenerated code for import placement check:")
        print("=" * 80)
        print(code)
        print("=" * 80)

        lines = code.split('\n')

        # Find import lines
        datetime_import_line = None
        for i, line in enumerate(lines):
            if 'from datetime import datetime' in line:
                datetime_import_line = i
                break

        assert datetime_import_line is not None, "datetime import should be present"

        # Verify it's not in the __future__ section
        assert 'from __future__' not in lines[datetime_import_line], \
            "datetime import should not be a __future__ import"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
