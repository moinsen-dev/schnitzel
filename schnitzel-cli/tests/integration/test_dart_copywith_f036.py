"""Integration tests for F036: Dart model generator supports copyWith via Freezed.

Tests that the DartModelGenerator produces Freezed models with the proper mixin
pattern that enables automatic copyWith method generation.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestFreezedCopyWithSupport:
    """Test that Freezed models have copyWith support via mixin."""

    def test_freezed_model_has_mixin(self):
        """Test that generated Freezed model includes the mixin pattern 'with _$ModelName'.

        This mixin is what provides the copyWith method automatically in Freezed.
        Format: class ModelName with _$ModelName
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify the mixin pattern: class User with _$User
        assert "class User with _$User {" in code

        # Verify the @freezed annotation is present
        assert "@freezed" in code

        # Verify the factory constructor pattern
        assert "const factory User({" in code
        assert "}) = _User;" in code

    def test_mixin_naming_convention(self):
        """Test that the mixin follows proper naming convention: _$ModelName.

        The naming convention is critical:
        - Must start with underscore dollar sign (_$)
        - Must match the model name exactly
        - This enables Freezed's code generation to create copyWith
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                        "inStock": FieldDefinition(type="bool", default=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify exact mixin pattern
        assert "class Product with _$Product {" in code

        # Should NOT have incorrect patterns
        assert "class Product with $Product {" not in code
        assert "class Product with _Product {" not in code
        assert "class Product with Product {" not in code

    def test_multiple_models_have_mixins(self):
        """Test that multiple models each get their own properly named mixin.

        Each model must have its own mixin with the correct naming:
        - User -> with _$User
        - Post -> with _$Post
        - Comment -> with _$Comment
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "username": FieldDefinition(type="string"),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "title": FieldDefinition(type="string"),
                        "content": FieldDefinition(type="string"),
                    }
                ),
                "Comment": Model(
                    name="Comment",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "text": FieldDefinition(type="string"),
                    }
                ),
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify each model has its own mixin
        assert "class User with _$User {" in code
        assert "class Post with _$Post {" in code
        assert "class Comment with _$Comment {" in code

        # Verify no cross-contamination
        assert "class User with _$Post" not in code
        assert "class Post with _$User" not in code
        assert "class Comment with _$User" not in code


class TestCopyWithUsagePatterns:
    """Test various field patterns to ensure copyWith will work correctly."""

    def test_copywith_with_optional_fields(self):
        """Test that models with optional fields support copyWith.

        Optional fields (nullable) can be updated with copyWith, allowing:
        - Setting a null value to a non-null value
        - Changing a non-null value to null
        - Leaving the value unchanged
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "name": FieldDefinition(type="string"),
                        "bio": FieldDefinition(type="string", optional=True),
                        "avatarUrl": FieldDefinition(type="string", optional=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify mixin is present for copyWith
        assert "class UserProfile with _$UserProfile {" in code

        # Verify optional fields are nullable (copyWith can handle nulls)
        assert "String? bio" in code
        assert "String? avatarUrl" in code

        # Verify required fields
        assert "required String id" in code
        assert "required String name" in code

    def test_copywith_with_default_values(self):
        """Test that models with default values support copyWith.

        Fields with defaults can still be updated via copyWith.
        The @Default annotation doesn't prevent copyWith functionality.
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Settings": Model(
                    name="Settings",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "theme": FieldDefinition(type="string", default="light"),
                        "notifications": FieldDefinition(type="bool", default=True),
                        "fontSize": FieldDefinition(type="int", default=14),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify mixin is present
        assert "class Settings with _$Settings {" in code

        # Verify @Default annotations are present
        assert "@Default('light') String theme" in code
        assert "@Default(true) bool notifications" in code
        assert "@Default(14) int fontSize" in code

    def test_copywith_with_complex_types(self):
        """Test that models with complex types (lists, maps) support copyWith.

        Complex types like List and Map can be fully replaced via copyWith.
        Freezed generates deep copy logic for these types.
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Article": Model(
                    name="Article",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "title": FieldDefinition(type="string"),
                        "tags": FieldDefinition(type="list<string>"),
                        "metadata": FieldDefinition(type="json"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify mixin is present
        assert "class Article with _$Article {" in code

        # Verify complex types
        assert "required List<String> tags" in code
        assert "required Map<String, dynamic> metadata" in code


class TestCopyWithDocumentation:
    """Test that generated code structure enables proper copyWith usage."""

    def test_factory_constructor_supports_copywith(self):
        """Test that const factory pattern is used, which is required for copyWith.

        The const factory constructor is essential for Freezed's code generation.
        Without it, copyWith won't be generated properly.
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Task": Model(
                    name="Task",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "title": FieldDefinition(type="string"),
                        "completed": FieldDefinition(type="bool", default=False),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Verify const factory constructor (required for copyWith)
        assert "const factory Task({" in code
        assert "}) = _Task;" in code

        # Verify mixin is present (provides copyWith implementation)
        assert "class Task with _$Task {" in code

    def test_all_elements_for_copywith_present(self):
        """Test that all required elements for copyWith are present in generated code.

        For Freezed to generate copyWith, we need:
        1. @freezed annotation
        2. class with _$ClassName mixin
        3. const factory constructor
        4. = _ClassName implementation
        """
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Book": Model(
                    name="Book",
                    fields={
                        "isbn": FieldDefinition(type="string", primary=True),
                        "title": FieldDefinition(type="string"),
                        "author": FieldDefinition(type="string"),
                        "published": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # 1. @freezed annotation
        assert "@freezed" in code

        # 2. Mixin pattern
        assert "class Book with _$Book {" in code

        # 3. Const factory constructor
        assert "const factory Book({" in code

        # 4. Implementation reference
        assert "}) = _Book;" in code

        # 5. fromJson factory (bonus - needed for full Freezed functionality)
        assert "factory Book.fromJson(Map<String, dynamic> json) => _$BookFromJson(json);" in code
