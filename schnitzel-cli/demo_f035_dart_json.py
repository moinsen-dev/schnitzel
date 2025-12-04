#!/usr/bin/env python3
"""Demo script for F035: Dart Freezed model generator with JSON serialization."""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.models import DartModelGenerator


def demo_basic_model():
    """Demonstrate basic model with JSON serialization."""
    print("=" * 80)
    print("DEMO 1: Basic User Model with JSON Serialization")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "userId": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                    "createdAt": FieldDefinition(type="datetime", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)


def demo_complex_model():
    """Demonstrate complex model with relationships."""
    print("\n" + "=" * 80)
    print("DEMO 2: Complex Model with Relationships and JSON Keys")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "postId": FieldDefinition(type="string"),
                    "title": FieldDefinition(type="string"),
                    "content": FieldDefinition(type="string"),
                    "publishedAt": FieldDefinition(type="datetime", optional=True),
                    "viewCount": FieldDefinition(type="int", optional=True),
                },
                relations={
                    "createdBy": Relation(type="belongsTo", model="User"),
                    "relatedPosts": Relation(type="hasMany", model="Post"),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)


def demo_multiple_models():
    """Demonstrate multiple models in one file."""
    print("\n" + "=" * 80)
    print("DEMO 3: Multiple Models with JSON Serialization")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "userId": FieldDefinition(type="string"),
                    "userName": FieldDefinition(type="string"),
                }
            ),
            "Product": Model(
                name="Product",
                fields={
                    "productId": FieldDefinition(type="string"),
                    "productName": FieldDefinition(type="string"),
                    "price": FieldDefinition(type="float"),
                    "createdAt": FieldDefinition(type="datetime", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)


def demo_snake_case_fields():
    """Demonstrate that snake_case fields don't get @JsonKey."""
    print("\n" + "=" * 80)
    print("DEMO 4: Snake Case Fields (No @JsonKey needed)")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "ApiResponse": Model(
                name="ApiResponse",
                fields={
                    "status_code": FieldDefinition(type="int"),
                    "message": FieldDefinition(type="string"),
                    "data": FieldDefinition(type="json", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)
    print("\nNOTE: Fields 'status_code', 'message', and 'data' are already in snake_case,")
    print("so they don't need @JsonKey annotations.")


if __name__ == "__main__":
    demo_basic_model()
    demo_complex_model()
    demo_multiple_models()
    demo_snake_case_fields()

    print("\n" + "=" * 80)
    print("All demos completed successfully!")
    print("=" * 80)
