"""Integration tests for F078: Python generator handles models with no relationships.

This test suite verifies that the Python model generator correctly handles models
that have no relations defined:
- Models should generate without relationship fields
- Should NOT import __future__ annotations if no relations exist
- Should work correctly with multiple models all without relations

Test Coverage:
1. Single model with no relations generates correctly
2. No forward references (__future__ annotations) imported when no relations
3. Multiple models all without relations
4. Mixed scenario: models with and without relations (control test)
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.python.models import PythonModelGenerator


class TestPythonNoRelationships:
    """Test Python model generator for models without relationships."""

    def test_model_with_no_relations_generates(self):
        """Test that a model without relations generates correctly.

        Verifies:
        - Model class is generated
        - All fields are present
        - No relationship fields
        - Code is valid Python
        """
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A simple user model",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string", max_length=100),
                        "email": FieldDefinition(type="string", max_length=255),
                        "age": FieldDefinition(type="int", min=0, max=150),
                        "active": FieldDefinition(type="bool", default=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code for model without relations:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Verify class definition and docstring
        assert "class User(BaseModel):" in generated_code, \
            "User model class should be generated"
        assert '"""A simple user model"""' in generated_code, \
            "Model description should be in docstring"

        # Verify all fields are present with correct types
        assert "id: UUID" in generated_code, "id field should be UUID"
        assert "name: str = Field(max_length=100)" in generated_code, \
            "name field should have max_length constraint"
        assert "email: str = Field(max_length=255)" in generated_code, \
            "email field should have max_length constraint"
        assert "age: int = Field(ge=0, le=150)" in generated_code, \
            "age field should have min/max constraints"
        assert "active: bool = True" in generated_code, \
            "active field should have default value"

        # Verify necessary imports
        assert "from pydantic import BaseModel, Field" in generated_code, \
            "Should import BaseModel and Field"
        assert "from uuid import UUID" in generated_code, \
            "Should import UUID for uuid fields"

        # Verify code is valid Python
        try:
            compile(generated_code, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_no_forward_references_needed(self):
        """Test that __future__ annotations are NOT imported when no relations exist.

        This is the key test for F078 - models without relationships should not
        need forward references, so __future__ annotations should not be imported.
        """
        schema = SchnitzelSchema(
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float", min=0),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code - checking for __future__ imports:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # KEY ASSERTION: Should NOT have __future__ annotations import
        assert "from __future__ import annotations" not in generated_code, \
            "Should NOT import __future__ annotations when no relations exist"

        # Verify basic imports are still present
        assert "from pydantic import BaseModel" in generated_code, \
            "Should still import BaseModel"
        assert "from uuid import UUID" in generated_code, \
            "Should still import UUID"

        # Verify the model is still generated correctly
        assert "class Product(BaseModel):" in generated_code
        assert "id: UUID" in generated_code
        assert "name: str" in generated_code
        assert "price: float = Field(ge=0)" in generated_code

    def test_multiple_models_no_relations(self):
        """Test multiple models all without relations.

        Verifies:
        - Multiple models can be generated without relations
        - No __future__ annotations import
        - Each model is complete and valid
        """
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "username": FieldDefinition(type="string", max_length=50),
                        "email": FieldDefinition(type="string"),
                    }
                ),
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float", min=0),
                        "in_stock": FieldDefinition(type="bool", default=True),
                    }
                ),
                "Category": Model(
                    name="Category",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string", max_length=100),
                        "description": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code for multiple models without relations:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Should NOT have __future__ annotations since no relations
        assert "from __future__ import annotations" not in generated_code, \
            "Should NOT import __future__ annotations when no models have relations"

        # Verify all three models are generated
        assert "class User(BaseModel):" in generated_code, \
            "User model should be generated"
        assert "class Product(BaseModel):" in generated_code, \
            "Product model should be generated"
        assert "class Category(BaseModel):" in generated_code, \
            "Category model should be generated"

        # Verify some fields from each model
        assert "username: str = Field(max_length=50)" in generated_code
        assert "price: float = Field(ge=0)" in generated_code
        assert "description: str | None = None" in generated_code

        # Verify imports
        assert "from pydantic import BaseModel, Field" in generated_code
        assert "from uuid import UUID" in generated_code

        # Verify code is valid Python
        try:
            compile(generated_code, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_model_with_relations_has_future_import(self):
        """Control test: Verify that models WITH relations DO get __future__ import.

        This is a control test to ensure our test of models without relations
        is actually testing the right thing - when relations exist, the import
        should be present.
        """
        schema = SchnitzelSchema(
            models={
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User",
                            foreign_key="author_id"
                        )
                    }
                ),
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
        generated_code = generator.generate(schema)

        print("\nGenerated code WITH relations (control test):")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # With relations, __future__ import SHOULD be present
        assert "from __future__ import annotations" in generated_code, \
            "SHOULD import __future__ annotations when relations exist"

        # Verify relationship field is generated
        assert "author: User | None = None" in generated_code, \
            "Should generate relationship field"

    def test_mixed_models_some_with_relations(self):
        """Test schema with some models having relations and some without.

        When ANY model has relations, __future__ annotations should be imported
        for the entire file (since it's a file-level import).
        """
        schema = SchnitzelSchema(
            models={
                # Model WITHOUT relations
                "Category": Model(
                    name="Category",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                ),
                # Model WITH relations
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "author_id": FieldDefinition(type="uuid"),
                    },
                    relations={
                        "author": Relation(
                            type="belongsTo",
                            model="User"
                        )
                    }
                ),
                # Another model WITHOUT relations
                "Tag": Model(
                    name="Tag",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "label": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code with mixed models:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Should have __future__ import because Post has relations
        assert "from __future__ import annotations" in generated_code, \
            "Should import __future__ annotations when any model has relations"

        # All models should be generated
        assert "class Category(BaseModel):" in generated_code
        assert "class Post(BaseModel):" in generated_code
        assert "class Tag(BaseModel):" in generated_code

        # Post should have relationship field
        assert "author: User | None = None" in generated_code

    def test_empty_model_no_relations(self):
        """Test model with no fields and no relations (edge case)."""
        schema = SchnitzelSchema(
            models={
                "EmptyModel": Model(
                    name="EmptyModel",
                    description="An empty model for testing"
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code for empty model:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Should generate with pass statement
        assert "class EmptyModel(BaseModel):" in generated_code
        assert "pass" in generated_code

        # Should NOT have __future__ import
        assert "from __future__ import annotations" not in generated_code

        # Should still be valid Python
        try:
            compile(generated_code, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_complex_types_no_relations(self):
        """Test models with complex field types but no relations.

        Verifies that complex types (lists, enums, vectors, json) work
        correctly without needing forward references.
        """
        schema = SchnitzelSchema(
            models={
                "DataModel": Model(
                    name="DataModel",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "tags": FieldDefinition(type="list<string>"),
                        "scores": FieldDefinition(type="list<int>"),
                        "status": FieldDefinition(
                            type="enum",
                            values=["draft", "published", "archived"]
                        ),
                        "embedding": FieldDefinition(type="vector", dimensions=384),
                        "metadata": FieldDefinition(type="json"),
                        "created_at": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = PythonModelGenerator()
        generated_code = generator.generate(schema)

        print("\nGenerated code with complex types but no relations:")
        print("=" * 80)
        print(generated_code)
        print("=" * 80)

        # Should NOT have __future__ import
        assert "from __future__ import annotations" not in generated_code, \
            "Complex types don't require __future__ annotations"

        # Verify complex type mappings
        assert "tags: list[str]" in generated_code
        assert "scores: list[int]" in generated_code
        assert 'status: Literal["draft", "published", "archived"]' in generated_code
        assert "embedding: list[float]" in generated_code
        assert "metadata: dict[str, Any]" in generated_code
        assert "created_at: datetime" in generated_code

        # Verify necessary imports
        assert "from typing import Any" in generated_code
        assert "from typing import Literal" in generated_code
        assert "from datetime import datetime" in generated_code
        assert "from uuid import UUID" in generated_code

        # Verify code is valid Python
        try:
            compile(generated_code, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
