"""Integration tests for YAML anchors and aliases support (F097)."""

import tempfile
from pathlib import Path

import pytest

from schnitzel.schema.parser import SchemaParser


class TestYAMLAnchorsF097:
    """Test YAML anchor and alias functionality in schema parser."""

    def test_yaml_anchor_works(self) -> None:
        """
        Test F097: YAML anchors should be expanded correctly by the parser.

        This test verifies that:
        1. A field definition can be marked with an anchor using &anchor_name syntax
        2. The anchor is properly parsed and stored
        3. The anchored field itself works correctly as a normal field
        4. The parser doesn't error when encountering anchors

        Steps:
        1. Create a YAML schema with a field that has an anchor (&uuid_field)
        2. Parse the schema
        3. Verify the anchored field is parsed correctly
        4. Verify field type and properties are correct
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_anchor.yaml"

            # Step 1: Create YAML with anchor
            content = """
schnitzel: 1.0.0

models:
  User:
    fields:
      # Define field with anchor
      id: &uuid_field
        type: uuid
        optional: false

      name:
        type: string
"""
            schema_path.write_text(content)

            # Step 2: Parse schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3-4: Verify anchored field works correctly
            user = schema.models["User"]
            assert "id" in user.fields
            assert user.fields["id"].type == "uuid"
            assert user.fields["id"].optional is False

    def test_anchor_for_field_reuse(self) -> None:
        """
        Test F097: Anchors allow reusing common field definitions across multiple fields.

        This test verifies that:
        1. Multiple fields can reference the same anchor using *anchor_name syntax
        2. All fields that reference the anchor have identical properties
        3. Changes to the anchor definition affect all aliased fields
        4. This provides DRY (Don't Repeat Yourself) benefits in schema definitions

        Steps:
        1. Create a YAML schema with one anchored field definition
        2. Create multiple fields that reference this anchor using aliases
        3. Parse the schema
        4. Verify all aliased fields have identical type and properties
        5. Verify all properties from the anchor are correctly copied
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_reuse.yaml"

            # Step 1-2: Create YAML with anchor and multiple aliases
            content = """
schnitzel: 1.0.0

models:
  User:
    fields:
      # Define reusable string field with anchor
      base_field: &string_field
        type: string
        optional: false

      # Reuse the definition for multiple fields
      name: *string_field
      email: *string_field
      username: *string_field

      # Also have a different field type
      id:
        type: uuid
"""
            schema_path.write_text(content)

            # Step 3: Parse schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 4-5: Verify all aliased fields have identical properties
            user = schema.models["User"]

            # All these fields should have the same type and optional setting
            for field_name in ["base_field", "name", "email", "username"]:
                assert field_name in user.fields
                assert user.fields[field_name].type == "string"
                assert user.fields[field_name].optional is False

            # Verify the different field is not affected
            assert user.fields["id"].type == "uuid"

    def test_alias_references_anchor(self) -> None:
        """
        Test F097: Aliases correctly reference and expand anchor definitions.

        This test verifies that:
        1. An alias (*anchor_name) correctly references its anchor (&anchor_name)
        2. The alias expands to have the same structure as the anchor
        3. Complex field definitions with multiple properties work with anchors
        4. Anchors and aliases work correctly within nested YAML structures

        Steps:
        1. Create a YAML schema with a complex field definition (with type, optional, constraints)
        2. Mark this field with an anchor
        3. Create another field that aliases this anchor
        4. Parse the schema
        5. Verify both fields have identical properties
        6. Verify all properties (type, optional, min, max) are correctly copied
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_alias_reference.yaml"

            # Step 1-3: Create YAML with complex anchored field and alias
            content = """
schnitzel: 1.0.0

models:
  Product:
    fields:
      # Define complex field with multiple properties and anchor
      price: &price_field
        type: float
        optional: false
        min: 0.0
        max: 999999.99

      # Regular field
      name:
        type: string

      # Alias references the anchor - should have all same properties
      discount_price: *price_field
"""
            schema_path.write_text(content)

            # Step 4: Parse schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 5-6: Verify both fields have identical complex properties
            product = schema.models["Product"]

            # Verify anchor field (price)
            assert "price" in product.fields
            price_field = product.fields["price"]
            assert price_field.type == "float"
            assert price_field.optional is False
            assert price_field.min == 0.0
            assert price_field.max == 999999.99

            # Verify aliased field (discount_price) has identical properties
            assert "discount_price" in product.fields
            discount_field = product.fields["discount_price"]
            assert discount_field.type == "float"
            assert discount_field.optional is False
            assert discount_field.min == 0.0
            assert discount_field.max == 999999.99

            # Verify both fields are effectively identical
            assert discount_field.type == price_field.type
            assert discount_field.optional == price_field.optional
            assert discount_field.min == price_field.min
            assert discount_field.max == price_field.max

    def test_multiple_anchors_in_schema(self) -> None:
        """
        Test F097: Multiple different anchors can coexist in the same schema.

        This test verifies that:
        1. Multiple anchors with different names can be defined in one schema
        2. Each alias correctly references its corresponding anchor
        3. Anchors don't interfere with each other
        4. Different field types can have their own anchor patterns

        Steps:
        1. Create a YAML schema with multiple anchors for different field types
        2. Create aliases that reference different anchors
        3. Parse the schema
        4. Verify each alias correctly matches its anchor
        5. Verify anchors don't cross-contaminate
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_multiple_anchors.yaml"

            content = """
schnitzel: 1.0.0

models:
  Article:
    fields:
      # Multiple anchors for different field patterns
      id: &uuid_field
        type: uuid

      title: &string_field
        type: string
        optional: false

      views: &count_field
        type: int
        min: 0

      # Use different aliases
      author_id: *uuid_field
      category_id: *uuid_field

      subtitle: *string_field
      tags: *string_field

      likes: *count_field
      shares: *count_field
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            article = schema.models["Article"]

            # Verify UUID fields
            for field_name in ["id", "author_id", "category_id"]:
                assert article.fields[field_name].type == "uuid"

            # Verify string fields
            for field_name in ["title", "subtitle", "tags"]:
                assert article.fields[field_name].type == "string"
                assert article.fields[field_name].optional is False

            # Verify count fields
            for field_name in ["views", "likes", "shares"]:
                assert article.fields[field_name].type == "int"
                assert article.fields[field_name].min == 0

    def test_anchor_with_optional_and_default(self) -> None:
        """
        Test F097: Anchors work correctly with optional fields and default values.

        This test verifies that:
        1. Anchored fields can have optional=true and default values
        2. Aliases correctly inherit optional and default settings
        3. Complex field configurations work with anchors

        Steps:
        1. Create a YAML schema with anchored optional field with default
        2. Create aliases referencing this anchor
        3. Parse the schema
        4. Verify optional and default values are preserved in aliases
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_optional_default.yaml"

            content = """
schnitzel: 1.0.0

models:
  Settings:
    fields:
      # Anchor with optional and default
      theme: &optional_string
        type: string
        optional: true
        default: "light"

      language: *optional_string
      timezone: *optional_string

      # Non-optional for comparison
      user_id:
        type: uuid
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            settings = schema.models["Settings"]

            # Verify all aliased fields have optional=true and default value
            for field_name in ["theme", "language", "timezone"]:
                field = settings.fields[field_name]
                assert field.type == "string"
                assert field.optional is True
                assert field.default == "light"

    def test_anchor_across_multiple_models(self) -> None:
        """
        Test F097: Anchors can be used across different models in the same schema file.

        Note: YAML anchors are file-scoped, so anchors defined at the file level
        can be referenced by any model in that file.

        Steps:
        1. Create a YAML schema with multiple models
        2. Define an anchor in one model
        3. Attempt to use patterns that might reference across models
        4. Parse the schema
        5. Verify each model's fields work correctly
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_cross_model.yaml"

            # Note: YAML anchors are file-scoped, so we can define them at various levels
            content = """
schnitzel: 1.0.0

models:
  User:
    fields:
      id: &id_field
        type: uuid
      name:
        type: string

  Post:
    fields:
      # Can reference anchor from earlier in the file
      id: *id_field
      title:
        type: string
      author_id: *id_field
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Verify User model
            user = schema.models["User"]
            assert user.fields["id"].type == "uuid"

            # Verify Post model uses the same anchor
            post = schema.models["Post"]
            assert post.fields["id"].type == "uuid"
            assert post.fields["author_id"].type == "uuid"

    def test_yaml_anchor_in_relations(self) -> None:
        """
        Test F097: YAML anchors work in relation definitions, not just fields.

        This test verifies that:
        1. Anchors can be used in relation definitions
        2. Common relation patterns can be reused
        3. Aliases work for relation configurations

        Steps:
        1. Create a YAML schema with anchored relation definition
        2. Create multiple relations using aliases
        3. Parse the schema
        4. Verify relations are correctly defined
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_relation_anchor.yaml"

            content = """
schnitzel: 1.0.0

models:
  User:
    fields:
      id:
        type: uuid
      name:
        type: string
    relations:
      # Define relation pattern with anchor
      posts: &has_many_posts
        type: hasMany
        model: Post

      # Could reference if needed (though less common for relations)
      published_posts: *has_many_posts

  Post:
    fields:
      id:
        type: uuid
      title:
        type: string
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: user_id
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            user = schema.models["User"]

            # Verify both relations reference the same definition
            assert "posts" in user.relations
            assert user.relations["posts"].type == "hasMany"
            assert user.relations["posts"].model == "Post"

            assert "published_posts" in user.relations
            assert user.relations["published_posts"].type == "hasMany"
            assert user.relations["published_posts"].model == "Post"
