"""Integration tests for F096: Schema parser handles comments in YAML files.

Feature F096 Requirements:
- Schema parser should preserve/handle YAML comments correctly
- Comments should not break parsing

Tests verify that:
1. YAML schemas with comments parse successfully
2. Comments don't affect the parsed model data
3. Multiple comment lines work correctly
4. Comments in various positions (inline, above fields, etc.) are handled
"""

import tempfile
from pathlib import Path

import pytest

from schnitzel.schema.parser import SchemaParser


class TestYAMLCommentsF096:
    """Test suite for F096: YAML comment handling in schema parser."""

    def test_yaml_with_comments_parses(self) -> None:
        """
        Test F096: Schema with comments should parse successfully.

        Steps:
        1. Create a YAML schema file with comments at various positions
        2. Call SchemaParser.parse(filepath)
        3. Verify parser returns a SchnitzelSchema object without errors
        4. Verify all models and fields are present despite comments
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema_with_comments.yaml"

            # Step 1: Create YAML with comments in various positions
            content = """
# Top-level comment describing the schema
schnitzel: 1.0.0  # Version specification

# Models section - defines all database models
models:
  # User model represents application users
  User:
    # User fields
    fields:
      id:  # Primary key for User
        type: uuid
      # User's email address (required)
      email:
        type: string
        optional: false
      name:  # Display name
        type: string
    # User relationships
    relations:
      posts:  # All posts by this user
        type: hasMany
        model: Post

  # Post model for user-generated content
  Post:
    fields:
      id:
        type: uuid  # Auto-generated UUID
      title:
        type: string  # Post title
      # Content of the post
      content:
        type: string
    relations:
      author:
        type: belongsTo
        model: User  # Reference to User model
        foreign_key: user_id
"""
            schema_path.write_text(content)

            # Step 2: Parse the schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3: Verify parser returns valid SchnitzelSchema
            assert schema is not None
            assert hasattr(schema, "models")
            assert schema.schnitzel == "1.0.0"

            # Step 4: Verify all models and fields are present
            assert len(schema.models) == 2
            assert "User" in schema.models
            assert "Post" in schema.models

            # Verify User model
            user = schema.models["User"]
            assert len(user.fields) == 3
            assert "id" in user.fields
            assert "email" in user.fields
            assert "name" in user.fields
            assert len(user.relations) == 1
            assert "posts" in user.relations

            # Verify Post model
            post = schema.models["Post"]
            assert len(post.fields) == 3
            assert "id" in post.fields
            assert "title" in post.fields
            assert "content" in post.fields
            assert len(post.relations) == 1
            assert "author" in post.relations

    def test_comments_dont_affect_models(self) -> None:
        """
        Test F096: Comments should not change model data.

        Steps:
        1. Create two identical schemas - one with comments, one without
        2. Parse both schemas
        3. Verify that the parsed data is identical
        4. Verify field types, optionality, and relationships match exactly
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create schema without comments
            schema_no_comments = Path(tmpdir) / "no_comments.yaml"
            content_no_comments = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
      email:
        type: string
        optional: false
      age:
        type: int
        min: 0
        max: 150
"""
            schema_no_comments.write_text(content_no_comments)

            # Create schema with comments (same structure)
            schema_with_comments = Path(tmpdir) / "with_comments.yaml"
            content_with_comments = """
# Schema version
schnitzel: 1.0.0  # Using version 1.0.0
# All models
models:
  # User model definition
  User:
    # User fields
    fields:
      # Primary key
      id:
        type: uuid  # UUID type
      # Email address
      email:
        type: string  # String type
        optional: false  # Required field
      # User age
      age:
        type: int  # Integer type
        min: 0  # Minimum value
        max: 150  # Maximum value
"""
            schema_with_comments.write_text(content_with_comments)

            # Step 2: Parse both schemas
            parser = SchemaParser()
            schema1 = parser.parse(schema_no_comments)
            schema2 = parser.parse(schema_with_comments)

            # Step 3-4: Verify parsed data is identical
            assert schema1.schnitzel == schema2.schnitzel

            # Verify same models exist
            assert set(schema1.models.keys()) == set(schema2.models.keys())

            # Verify User model is identical in both
            user1 = schema1.models["User"]
            user2 = schema2.models["User"]

            # Check same fields
            assert set(user1.fields.keys()) == set(user2.fields.keys())

            # Check field properties match exactly
            for field_name in user1.fields:
                field1 = user1.fields[field_name]
                field2 = user2.fields[field_name]

                assert field1.type == field2.type
                assert field1.optional == field2.optional
                assert field1.min == field2.min
                assert field1.max == field2.max

    def test_multiline_comments(self) -> None:
        """
        Test F096: Multiple consecutive comment lines work correctly.

        Steps:
        1. Create a YAML schema with multiple consecutive comment lines
        2. Parse the schema
        3. Verify parsing succeeds without errors
        4. Verify all data after comments is correctly parsed
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "multiline_comments.yaml"

            # Step 1: Create schema with multiple consecutive comments
            content = """
################################
# Schnitzel Schema Definition
# Version: 1.0.0
# Author: Test Suite
# Purpose: Testing multiline comments
################################

schnitzel: 1.0.0

# ============================
# Models Section
# ============================
# This section defines all database models
# Each model can have fields and relations
# ============================
models:
  # ===== User Model =====
  # Represents an application user
  # Contains authentication and profile data
  # ===== User Model =====
  User:
    fields:
      ###
      # Primary Key Field
      # Type: UUID (universally unique identifier)
      # Auto-generated on creation
      ###
      id:
        type: uuid

      ###
      # Email Field
      # Used for authentication and communication
      # Must be unique across all users
      # Validation: Valid email format required
      ###
      email:
        type: string
        optional: false
        unique: true

      # Name field - simple comment
      name:
        type: string
"""
            schema_path.write_text(content)

            # Step 2: Parse the schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3-4: Verify parsing succeeded and data is correct
            assert schema is not None
            assert schema.schnitzel == "1.0.0"

            # Verify User model
            assert "User" in schema.models
            user = schema.models["User"]

            # Verify all fields present
            assert len(user.fields) == 3
            assert "id" in user.fields
            assert "email" in user.fields
            assert "name" in user.fields

            # Verify field properties
            assert user.fields["id"].type == "uuid"
            assert user.fields["email"].type == "string"
            assert user.fields["email"].optional is False
            assert user.fields["email"].unique is True
            assert user.fields["name"].type == "string"

    def test_comments_in_relations(self) -> None:
        """
        Test F096: Comments within relation definitions work correctly.

        Steps:
        1. Create a schema with comments in relation definitions
        2. Parse the schema
        3. Verify relations are parsed correctly
        4. Verify relation properties match expected values
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "relations_with_comments.yaml"

            content = """
schnitzel: 1.0.0
models:
  User:
    fields:
      id:
        type: uuid
    # Relations for User model
    relations:
      # Has many posts - one user can create multiple posts
      posts:
        type: hasMany  # One-to-many relationship
        model: Post  # References Post model

      # Has many comments - user can comment on posts
      comments:
        type: hasMany
        model: Comment

  Post:
    fields:
      id:
        type: uuid
    relations:
      # Belongs to one user - every post has an author
      author:
        type: belongsTo  # Many-to-one relationship
        model: User  # References User model
        foreign_key: user_id  # Foreign key column name

  Comment:
    fields:
      id:
        type: uuid
    relations:
      # Author of the comment
      author:
        type: belongsTo
        model: User
        foreign_key: user_id
      # Post being commented on
      post:
        type: belongsTo
        model: Post
        foreign_key: post_id
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Verify all models present
            assert len(schema.models) == 3

            # Verify User relations
            user = schema.models["User"]
            assert len(user.relations) == 2
            assert "posts" in user.relations
            assert user.relations["posts"].type == "hasMany"
            assert user.relations["posts"].model == "Post"
            assert "comments" in user.relations
            assert user.relations["comments"].type == "hasMany"
            assert user.relations["comments"].model == "Comment"

            # Verify Post relations
            post = schema.models["Post"]
            assert len(post.relations) == 1
            assert "author" in post.relations
            assert post.relations["author"].type == "belongsTo"
            assert post.relations["author"].model == "User"
            assert post.relations["author"].foreign_key == "user_id"

            # Verify Comment relations
            comment = schema.models["Comment"]
            assert len(comment.relations) == 2
            assert "author" in comment.relations
            assert comment.relations["author"].foreign_key == "user_id"
            assert "post" in comment.relations
            assert comment.relations["post"].foreign_key == "post_id"

    def test_empty_comment_lines(self) -> None:
        """
        Test F096: Empty comment lines (just #) are handled correctly.

        Steps:
        1. Create schema with empty comment lines
        2. Parse the schema
        3. Verify parsing succeeds
        4. Verify data integrity
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "empty_comments.yaml"

            content = """
schnitzel: 1.0.0
#
# Models
#
models:
  #
  User:
    #
    fields:
      #
      id:
        #
        type: uuid
      #
      name:
        type: string
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            assert schema.schnitzel == "1.0.0"
            assert "User" in schema.models
            user = schema.models["User"]
            assert len(user.fields) == 2
            assert user.fields["id"].type == "uuid"
            assert user.fields["name"].type == "string"

    def test_comments_with_special_characters(self) -> None:
        """
        Test F096: Comments with special characters are handled correctly.

        Steps:
        1. Create schema with comments containing special characters
        2. Parse the schema
        3. Verify parsing succeeds
        4. Verify model data is unaffected by special characters in comments
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "special_chars.yaml"

            content = """
# Schema with special chars: !@#$%^&*()_+-=[]{}|;:'",.<>?/~`
schnitzel: 1.0.0  # Version 1.0.0 - updated on 2024-12-03

models:
  # User model - handles auth & profile data (critical!)
  User:
    fields:
      # ID field - UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
      id:
        type: uuid
      # Email - format: user@example.com
      email:
        type: string
      # Age - range: 0-150 (inclusive)
      age:
        type: int
        min: 0  # Minimum: 0
        max: 150  # Maximum: 150
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            assert schema.schnitzel == "1.0.0"
            assert "User" in schema.models
            user = schema.models["User"]
            assert len(user.fields) == 3
            assert user.fields["id"].type == "uuid"
            assert user.fields["email"].type == "string"
            assert user.fields["age"].type == "int"
            assert user.fields["age"].min == 0
            assert user.fields["age"].max == 150

    def test_comments_in_imported_files(self) -> None:
        """
        Test F096: Comments in imported files are handled correctly.

        Steps:
        1. Create base schema with imports
        2. Create imported schema files with comments
        3. Parse the base schema (which loads imports)
        4. Verify all models from all files are parsed correctly
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create imported file with comments
            imported_path = Path(tmpdir) / "imported.yaml"
            imported_content = """
# Imported schema file
# Contains shared models
schnitzel: 1.0.0

models:
  # Shared User model
  User:
    fields:
      # User ID
      id:
        type: uuid
      # User name
      name:
        type: string
"""
            imported_path.write_text(imported_content)

            # Create base schema that imports the file
            base_path = Path(tmpdir) / "base.yaml"
            base_content = """
# Base schema file
schnitzel: 1.0.0

# Import shared models
imports:
  - imported.yaml  # Contains User model

# Define additional models
models:
  # Post model
  Post:
    fields:
      # Post ID
      id:
        type: uuid
      # Post title
      title:
        type: string
    relations:
      # Post author
      author:
        type: belongsTo
        model: User  # From imported file
        foreign_key: user_id
"""
            base_path.write_text(base_content)

            parser = SchemaParser()
            schema = parser.parse(base_path)

            # Verify both models are present
            assert len(schema.models) == 2
            assert "User" in schema.models
            assert "Post" in schema.models

            # Verify User model from imported file
            user = schema.models["User"]
            assert len(user.fields) == 2
            assert user.fields["id"].type == "uuid"
            assert user.fields["name"].type == "string"

            # Verify Post model from base file
            post = schema.models["Post"]
            assert len(post.fields) == 2
            assert post.fields["id"].type == "uuid"
            assert post.fields["title"].type == "string"
            assert len(post.relations) == 1
            assert post.relations["author"].model == "User"

    def test_comments_with_field_constraints(self) -> None:
        """
        Test F096: Comments don't interfere with field constraints.

        Steps:
        1. Create schema with comments around constraint definitions
        2. Parse the schema
        3. Verify all constraints are parsed correctly
        4. Verify constraint values match expected values
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "constraints.yaml"

            content = """
schnitzel: 1.0.0
models:
  Product:
    fields:
      id:
        type: uuid
      # Product name with length constraints
      name:
        type: string
        min: 3  # Minimum 3 characters
        max: 100  # Maximum 100 characters
      # Product price - must be positive
      price:
        type: float
        min: 0.01  # At least 1 cent
        max: 999999.99  # Maximum price
      # Product description - optional field
      description:
        type: string
        optional: true  # Can be null
        default: ""  # Empty string by default
      # Stock quantity
      stock:
        type: int
        min: 0  # Cannot be negative
        default: 0  # Default to 0
      # Unique product SKU
      sku:
        type: string
        unique: true  # Must be unique across all products
"""
            schema_path.write_text(content)

            parser = SchemaParser()
            schema = parser.parse(schema_path)

            product = schema.models["Product"]

            # Verify name constraints
            name_field = product.fields["name"]
            assert name_field.type == "string"
            assert name_field.min == 3
            assert name_field.max == 100

            # Verify price constraints
            price_field = product.fields["price"]
            assert price_field.type == "float"
            assert price_field.min == 0.01
            assert price_field.max == 999999.99

            # Verify description field
            desc_field = product.fields["description"]
            assert desc_field.type == "string"
            assert desc_field.optional is True
            assert desc_field.default == ""

            # Verify stock field
            stock_field = product.fields["stock"]
            assert stock_field.type == "int"
            assert stock_field.min == 0
            assert stock_field.default == 0

            # Verify sku field
            sku_field = product.fields["sku"]
            assert sku_field.type == "string"
            assert sku_field.unique is True
