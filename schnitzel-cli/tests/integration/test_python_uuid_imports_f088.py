"""Integration tests for F088: Python generator handles UUID fields with proper imports."""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python import PythonModelGenerator


class TestPythonUUIDImports:
    """Test Python model generator UUID field handling and imports."""

    def test_uuid_import_present(self):
        """Test that 'from uuid import UUID' is present when UUID fields exist."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is present
        assert "from uuid import UUID" in code

    def test_uuid_type_correct(self):
        """Test that field with UUID type has correct type annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify field has UUID type
        assert "id: UUID" in code

    def test_no_uuid_import_when_not_needed(self):
        """Test that UUID import is not present when no UUID fields exist."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is NOT present
        assert "from uuid import UUID" not in code

    def test_multiple_uuid_fields(self):
        """Test multiple UUID fields in the same model."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "owner_id": FieldDefinition(type="uuid"),
                        "created_by": FieldDefinition(type="uuid"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is present (only once)
        assert code.count("from uuid import UUID") == 1

        # Verify all fields have UUID type
        assert "id: UUID" in code
        assert "owner_id: UUID" in code
        assert "created_by: UUID" in code

    def test_uuid_across_multiple_models(self):
        """Test UUID fields across multiple models."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "author_id": FieldDefinition(type="uuid"),
                        "title": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is present (only once)
        assert code.count("from uuid import UUID") == 1

        # Verify both models are present with UUID fields
        assert "class User(BaseModel):" in code
        assert "class Post(BaseModel):" in code

    def test_optional_uuid_field(self):
        """Test optional UUID field handling."""
        schema = SchnitzelSchema(
            models={
                "Document": Model(
                    name="Document",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "parent_id": FieldDefinition(type="uuid", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is present
        assert "from uuid import UUID" in code

        # Verify required UUID field
        assert "id: UUID" in code

        # Verify optional UUID field uses Pydantic v2 syntax (| None)
        assert "parent_id: UUID | None" in code

    def test_uuid_with_default_none(self):
        """Test UUID field with default None."""
        schema = SchnitzelSchema(
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "assigned_to": FieldDefinition(type="uuid", optional=True, default=None),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is present
        assert "from uuid import UUID" in code

        # Verify field has correct type and default
        assert "assigned_to: UUID | None = None" in code

    def test_list_of_uuids(self):
        """Test list<uuid> field type."""
        schema = SchnitzelSchema(
            models={
                "Group": Model(
                    name="Group",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "member_ids": FieldDefinition(type="list<uuid>"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import is present
        assert "from uuid import UUID" in code

        # Verify list of UUIDs is correctly typed
        assert "member_ids: list[UUID]" in code

    def test_uuid_field_structure(self):
        """Test complete structure with UUID field."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify overall structure
        lines = code.split("\n")

        # Imports should be at the top
        import_lines = [l for l in lines[:10] if l.startswith("from")]
        assert any("from uuid import UUID" in l for l in import_lines)
        assert any("from pydantic import BaseModel" in l for l in import_lines)

        # Class definition should exist
        assert "class User(BaseModel):" in code

        # Docstring should be present
        assert "A user in the system" in code

        # UUID field should be present
        assert "id: UUID" in code

    def test_mixed_types_with_uuid(self):
        """Test model with UUID and other types."""
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float", min=0),
                        "quantity": FieldDefinition(type="int"),
                        "active": FieldDefinition(type="bool", default=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify UUID import
        assert "from uuid import UUID" in code

        # Verify all field types
        assert "id: UUID" in code
        assert "name: str" in code
        assert "price: float = Field(ge=0)" in code
        assert "quantity: int" in code
        assert "active: bool = True" in code

    def test_import_ordering_with_uuid(self):
        """Test that imports are properly ordered when UUID is present."""
        schema = SchnitzelSchema(
            models={
                "Event": Model(
                    name="Event",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "timestamp": FieldDefinition(type="datetime"),
                        "data": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify all necessary imports are present
        assert "from datetime import datetime" in code
        assert "from uuid import UUID" in code
        assert "from typing import Any" in code
        assert "from pydantic import BaseModel" in code

        # Get import section
        lines = code.split("\n")
        import_section = []
        for line in lines:
            if line.startswith("from") or line.startswith("import"):
                import_section.append(line)
            elif line.strip() == "":
                continue
            else:
                break

        # Verify imports are sorted (excluding __future__)
        non_future_imports = [imp for imp in import_section if not imp.startswith("from __future__")]
        assert non_future_imports == sorted(non_future_imports)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
