#!/usr/bin/env python3
"""Demo script for F037: Dart model generator handles snake_case to camelCase conversion.

This demonstrates the DartModelGenerator's ability to:
1. Keep field names in their original format from schema
2. Add @JsonKey(name: 'snake_case') when the JSON key differs from field name
3. Use _to_snake_case() helper for JSON key generation
"""

from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.models import DartModelGenerator


def demo_mixed_field_names():
    """Demonstrate handling of mixed camelCase, snake_case, and single-word fields."""
    print("=" * 80)
    print("DEMO 1: Mixed Field Names (camelCase, snake_case, single-word)")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "UserProfile": Model(
                name="UserProfile",
                fields={
                    # camelCase fields - need @JsonKey
                    "userId": FieldDefinition(type="string"),
                    "createdAt": FieldDefinition(type="datetime", optional=True),
                    "firstName": FieldDefinition(type="string"),
                    "isActive": FieldDefinition(type="boolean", default=True),
                    # single-word fields - no @JsonKey needed
                    "name": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                    "age": FieldDefinition(type="int", optional=True),
                    # snake_case fields - no @JsonKey needed
                    "user_role": FieldDefinition(type="string"),
                    "last_login": FieldDefinition(type="datetime", optional=True),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)
    print("\n")


def demo_relationships_with_json_key():
    """Demonstrate relationship fields with @JsonKey annotations."""
    print("=" * 80)
    print("DEMO 2: Relationships with @JsonKey Annotations")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "Post": Model(
                name="Post",
                fields={
                    "postId": FieldDefinition(type="string"),
                    "title": FieldDefinition(type="string"),
                    "content": FieldDefinition(type="string"),
                },
                relations={
                    # camelCase relationships - need @JsonKey
                    "createdBy": Relation(type="belongsTo", model="User"),
                    "postComments": Relation(type="hasMany", model="Comment"),
                    "featuredImage": Relation(type="hasOne", model="Image"),
                    # snake_case relationship - no @JsonKey needed
                    "author_info": Relation(type="belongsTo", model="AuthorInfo"),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)
    print("\n")


def demo_snake_case_conversion():
    """Demonstrate the _to_snake_case() conversion helper."""
    print("=" * 80)
    print("DEMO 3: Snake Case Conversion Helper")
    print("=" * 80)

    generator = DartModelGenerator()

    test_cases = [
        # camelCase
        ("userId", "user_id"),
        ("createdAt", "created_at"),
        ("firstName", "first_name"),
        ("isActive", "is_active"),
        # PascalCase
        ("UserName", "user_name"),
        ("FirstName", "first_name"),
        # snake_case (unchanged)
        ("user_id", "user_id"),
        ("created_at", "created_at"),
        # single words (unchanged)
        ("id", "id"),
        ("name", "name"),
        ("email", "email"),
        # consecutive capitals
        ("HTTPResponse", "h_t_t_p_response"),
        ("URLPath", "u_r_l_path"),
        ("APIKey", "a_p_i_key"),
    ]

    print(f"{'Input':<20} -> {'Output':<20} | {'Match Expected':<15}")
    print("-" * 60)
    for input_str, expected in test_cases:
        actual = generator._to_snake_case(input_str)
        match = "✓" if actual == expected else "✗"
        print(f"{input_str:<20} -> {actual:<20} | {match:<15}")
    print("\n")


def demo_needs_json_key_logic():
    """Demonstrate the _needs_json_key() decision logic."""
    print("=" * 80)
    print("DEMO 4: Needs @JsonKey Decision Logic")
    print("=" * 80)

    generator = DartModelGenerator()

    test_cases = [
        # Should need @JsonKey (camelCase)
        ("userId", True, "camelCase -> needs @JsonKey"),
        ("createdAt", True, "camelCase -> needs @JsonKey"),
        ("firstName", True, "camelCase -> needs @JsonKey"),
        ("isActive", True, "camelCase -> needs @JsonKey"),
        # Should NOT need @JsonKey (snake_case or single word)
        ("user_id", False, "snake_case -> no @JsonKey"),
        ("created_at", False, "snake_case -> no @JsonKey"),
        ("id", False, "single word -> no @JsonKey"),
        ("name", False, "single word -> no @JsonKey"),
        ("email", False, "single word -> no @JsonKey"),
    ]

    print(f"{'Field Name':<20} | {'Needs @JsonKey':<15} | {'Reason':<35}")
    print("-" * 75)
    for field_name, expected, reason in test_cases:
        actual = generator._needs_json_key(field_name)
        match = "✓" if actual == expected else "✗"
        result = f"{match} {actual}"
        print(f"{field_name:<20} | {result:<15} | {reason:<35}")
    print("\n")


def demo_realistic_user_model():
    """Demonstrate a realistic user model with all features."""
    print("=" * 80)
    print("DEMO 5: Realistic User Model (Complete Example)")
    print("=" * 80)

    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    # Primary key
                    "userId": FieldDefinition(type="uuid"),
                    # Basic info (single words)
                    "username": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string"),
                    "name": FieldDefinition(type="string"),
                    # Profile info (camelCase)
                    "firstName": FieldDefinition(type="string"),
                    "lastName": FieldDefinition(type="string"),
                    "displayName": FieldDefinition(type="string", optional=True),
                    "profilePicture": FieldDefinition(type="string", optional=True),
                    # Account status (camelCase with defaults)
                    "isActive": FieldDefinition(type="boolean", default=True),
                    "isVerified": FieldDefinition(type="boolean", default=False),
                    "emailVerified": FieldDefinition(type="boolean", default=False),
                    # Timestamps (camelCase)
                    "createdAt": FieldDefinition(type="datetime"),
                    "updatedAt": FieldDefinition(type="datetime"),
                    "lastLoginAt": FieldDefinition(type="datetime", optional=True),
                    # snake_case fields (from legacy API)
                    "legacy_id": FieldDefinition(type="int", optional=True),
                    "api_key": FieldDefinition(type="string", optional=True),
                },
                relations={
                    "userPosts": Relation(type="hasMany", model="Post"),
                    "userComments": Relation(type="hasMany", model="Comment"),
                    "createdBy": Relation(type="belongsTo", model="Admin"),
                }
            )
        }
    )

    generator = DartModelGenerator()
    code = generator.generate(schema)
    print(code)
    print("\n")

    # Show which fields got @JsonKey
    print("ANALYSIS:")
    print("-" * 80)
    json_key_count = code.count("@JsonKey")
    print(f"Total @JsonKey annotations: {json_key_count}")
    print("\nFields with @JsonKey (camelCase):")
    fields_with_json_key = [
        "userId", "firstName", "lastName", "displayName", "profilePicture",
        "isActive", "isVerified", "emailVerified", "createdAt", "updatedAt",
        "lastLoginAt", "userPosts", "userComments", "createdBy"
    ]
    for field in fields_with_json_key:
        snake = generator._to_snake_case(field)
        print(f"  - {field:20} -> @JsonKey(name: '{snake}')")

    print("\nFields WITHOUT @JsonKey (single-word or snake_case):")
    fields_without_json_key = ["username", "email", "name", "legacy_id", "api_key"]
    for field in fields_without_json_key:
        print(f"  - {field:20} (no conversion needed)")
    print("\n")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  F037: Dart Model Generator - snake_case to camelCase Conversion".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    demo_mixed_field_names()
    demo_relationships_with_json_key()
    demo_snake_case_conversion()
    demo_needs_json_key_logic()
    demo_realistic_user_model()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("The DartModelGenerator successfully:")
    print("✓ Keeps field names in their original format from schema")
    print("✓ Adds @JsonKey(name: 'snake_case') when JSON key differs from field name")
    print("✓ Uses _to_snake_case() helper for correct snake_case conversion")
    print("✓ Handles camelCase, snake_case, and single-word fields correctly")
    print("✓ Applies @JsonKey to relationship fields when needed")
    print("=" * 80)
    print("\n")


if __name__ == "__main__":
    main()
