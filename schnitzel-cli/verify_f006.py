#!/usr/bin/env python3
"""
Verification script for F006: Schema parser can merge feature schemas without conflicts.

This script demonstrates that the SchemaParser correctly merges multiple feature schemas
(auth.yaml and posts.yaml) without conflicts and maintains cross-feature relationships.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from schnitzel.schema.parser import SchemaParser


def main():
    """Run F006 verification."""
    print("=" * 70)
    print("F006 VERIFICATION: Schema parser merges feature schemas")
    print("=" * 70)
    print()

    # Setup paths
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    main_schema = fixtures_dir / "multi_feature_main.yaml"
    auth_schema = fixtures_dir / "auth.yaml"
    posts_schema = fixtures_dir / "posts.yaml"

    # Verify fixture files exist
    print("Step 1: Verify fixture files exist")
    print(f"  - auth.yaml: {auth_schema.exists()}")
    print(f"  - posts.yaml: {posts_schema.exists()}")
    print(f"  - multi_feature_main.yaml: {main_schema.exists()}")
    print()

    if not all([auth_schema.exists(), posts_schema.exists(), main_schema.exists()]):
        print("ERROR: One or more fixture files missing!")
        return 1

    # Parse the main schema
    print("Step 2: Parse main schema (imports auth.yaml + posts.yaml)")
    parser = SchemaParser()
    schema = parser.parse(main_schema)
    print("  ✓ Schema parsed successfully")
    print()

    # Verify all 4 models are present
    print("Step 3: Verify all 4 models are present")
    expected_models = ["User", "Session", "Post", "Comment"]
    for model_name in expected_models:
        if model_name in schema.models:
            print(f"  ✓ {model_name} model found")
        else:
            print(f"  ✗ {model_name} model NOT found")
            return 1
    print()

    # Verify no naming conflicts
    print("Step 4: Verify no naming conflicts")
    model_names = list(schema.models.keys())
    unique_count = len(set(model_names))
    total_count = len(model_names)
    print(f"  Total models: {total_count}")
    print(f"  Unique models: {unique_count}")
    if total_count == unique_count:
        print("  ✓ No duplicate model names")
    else:
        print("  ✗ Duplicate model names found!")
        return 1
    print()

    # Verify each model retains its original fields
    print("Step 5: Verify each model retains its original fields")

    # Check User model
    user = schema.models["User"]
    user_fields = ["id", "email", "created_at"]
    for field in user_fields:
        if field in user.fields:
            print(f"  ✓ User.{field}")
        else:
            print(f"  ✗ User.{field} missing")
            return 1

    # Check Session model
    session = schema.models["Session"]
    session_fields = ["id", "user_id", "token", "expires_at"]
    for field in session_fields:
        if field in session.fields:
            print(f"  ✓ Session.{field}")
        else:
            print(f"  ✗ Session.{field} missing")
            return 1

    # Check Post model
    post = schema.models["Post"]
    post_fields = ["id", "title", "content", "author_id", "created_at"]
    for field in post_fields:
        if field in post.fields:
            print(f"  ✓ Post.{field}")
        else:
            print(f"  ✗ Post.{field} missing")
            return 1

    # Check Comment model
    comment = schema.models["Comment"]
    comment_fields = ["id", "post_id", "author_id", "text", "created_at"]
    for field in comment_fields:
        if field in comment.fields:
            print(f"  ✓ Comment.{field}")
        else:
            print(f"  ✗ Comment.{field} missing")
            return 1
    print()

    # Verify relationships across feature boundaries work
    print("Step 6: Verify cross-feature relationships")

    # Post.author -> User (posts -> auth)
    if post.relations and "author" in post.relations:
        author_rel = post.relations["author"]
        if author_rel.model == "User" and author_rel.type == "belongsTo":
            print(f"  ✓ Post.author -> User (cross-feature)")
        else:
            print(f"  ✗ Post.author relationship incorrect")
            return 1
    else:
        print(f"  ✗ Post.author relationship missing")
        return 1

    # Comment.author -> User (posts -> auth)
    if comment.relations and "author" in comment.relations:
        author_rel = comment.relations["author"]
        if author_rel.model == "User" and author_rel.type == "belongsTo":
            print(f"  ✓ Comment.author -> User (cross-feature)")
        else:
            print(f"  ✗ Comment.author relationship incorrect")
            return 1
    else:
        print(f"  ✗ Comment.author relationship missing")
        return 1

    # Comment.post -> Post (within posts)
    if comment.relations and "post" in comment.relations:
        post_rel = comment.relations["post"]
        if post_rel.model == "Post" and post_rel.type == "belongsTo":
            print(f"  ✓ Comment.post -> Post (within feature)")
        else:
            print(f"  ✗ Comment.post relationship incorrect")
            return 1
    else:
        print(f"  ✗ Comment.post relationship missing")
        return 1

    # Session.user -> User (within auth)
    if session.relations and "user" in session.relations:
        user_rel = session.relations["user"]
        if user_rel.model == "User" and user_rel.type == "belongsTo":
            print(f"  ✓ Session.user -> User (within feature)")
        else:
            print(f"  ✗ Session.user relationship incorrect")
            return 1
    else:
        print(f"  ✗ Session.user relationship missing")
        return 1

    print()
    print("=" * 70)
    print("✓ F006 VERIFICATION PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Successfully merged auth.yaml (User, Session)")
    print("  - Successfully merged posts.yaml (Post, Comment)")
    print("  - All 4 models present with correct fields")
    print("  - Cross-feature relationships work correctly")
    print("  - No naming conflicts detected")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
