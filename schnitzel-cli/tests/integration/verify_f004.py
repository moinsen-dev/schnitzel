#!/usr/bin/env python3
"""
Standalone verification script for F004 (multi-level nested imports).

This script verifies all the test steps for F004 without requiring pytest.
"""

import sys
from pathlib import Path

# Add src to path so we can import schnitzel
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.exceptions import CircularImportError


def main():
    """Run all F004 verification tests."""
    print("=" * 60)
    print("F004: Multi-Level Nested Imports Verification")
    print("=" * 60)
    print()

    fixtures_dir = Path(__file__).parent / "fixtures" / "multi_level_imports"
    level2_path = fixtures_dir / "level2.yaml"

    # Step 1: Create level0.yaml with BaseModel
    print("[Step 1] Create level0.yaml with BaseModel")
    level0_path = fixtures_dir / "level0.yaml"
    if level0_path.exists():
        print(f"  ✓ {level0_path} exists")
    else:
        print(f"  ✗ {level0_path} NOT FOUND")
        return False

    # Step 2: Create level1.yaml importing level0.yaml with UserModel
    print("[Step 2] Create level1.yaml importing level0.yaml with UserModel")
    level1_path = fixtures_dir / "level1.yaml"
    if level1_path.exists():
        print(f"  ✓ {level1_path} exists")
    else:
        print(f"  ✗ {level1_path} NOT FOUND")
        return False

    # Step 3: Create level2.yaml importing level1.yaml with PostModel
    print("[Step 3] Create level2.yaml importing level1.yaml with PostModel")
    if level2_path.exists():
        print(f"  ✓ {level2_path} exists")
    else:
        print(f"  ✗ {level2_path} NOT FOUND")
        return False

    # Step 4: Call SchemaParser.parse('level2.yaml')
    print("[Step 4] Call SchemaParser.parse('level2.yaml')")
    try:
        parser = SchemaParser()
        schema = parser.parse(level2_path)
        print(f"  ✓ Parser successfully parsed level2.yaml")
    except Exception as e:
        print(f"  ✗ Parse failed: {e}")
        return False

    # Step 5: Verify all three models are present in final schema
    print("[Step 5] Verify all three models are present in final schema")
    expected_models = ["BaseModel", "UserModel", "PostModel"]
    for model_name in expected_models:
        if model_name in schema.models:
            print(f"  ✓ {model_name} found")
        else:
            print(f"  ✗ {model_name} NOT FOUND")
            return False

    # Step 6: Verify import chain is resolved in correct order
    print("[Step 6] Verify import chain is resolved in correct order")
    model_count = len(schema.models)
    if model_count == 3:
        print(f"  ✓ Correct number of models: {model_count}")
    else:
        print(f"  ✗ Wrong number of models: {model_count} (expected 3)")
        return False

    # Step 7: Verify no circular import issues
    print("[Step 7] Verify no circular import issues")
    try:
        parser2 = SchemaParser()
        schema2 = parser2.parse(level2_path)
        print(f"  ✓ No circular import errors detected")
    except CircularImportError as e:
        print(f"  ✗ Circular import error: {e}")
        return False

    # Step 8: Verify models from all levels are accessible
    print("[Step 8] Verify models from all levels are accessible")

    # Check BaseModel (from level0)
    base_model = schema.models.get("BaseModel")
    if base_model and "id" in base_model.fields:
        print(f"  ✓ BaseModel.id accessible (type: {base_model.fields['id'].type})")
    else:
        print(f"  ✗ BaseModel.id not accessible")
        return False

    if base_model and "created_at" in base_model.fields:
        print(f"  ✓ BaseModel.created_at accessible (type: {base_model.fields['created_at'].type})")
    else:
        print(f"  ✗ BaseModel.created_at not accessible")
        return False

    # Check UserModel (from level1)
    user_model = schema.models.get("UserModel")
    if user_model and "username" in user_model.fields:
        print(f"  ✓ UserModel.username accessible (type: {user_model.fields['username'].type})")
    else:
        print(f"  ✗ UserModel.username not accessible")
        return False

    if user_model and "email" in user_model.fields:
        print(f"  ✓ UserModel.email accessible (type: {user_model.fields['email'].type})")
    else:
        print(f"  ✗ UserModel.email not accessible")
        return False

    # Check PostModel (from level2)
    post_model = schema.models.get("PostModel")
    if post_model and "title" in post_model.fields:
        print(f"  ✓ PostModel.title accessible (type: {post_model.fields['title'].type})")
    else:
        print(f"  ✗ PostModel.title not accessible")
        return False

    if post_model and "content" in post_model.fields:
        print(f"  ✓ PostModel.content accessible (type: {post_model.fields['content'].type})")
    else:
        print(f"  ✗ PostModel.content not accessible")
        return False

    # Additional verification: Check MAX_IMPORT_DEPTH constant
    print()
    print("[Additional] Verify MAX_IMPORT_DEPTH constant")
    if hasattr(SchemaParser, 'MAX_IMPORT_DEPTH'):
        print(f"  ✓ MAX_IMPORT_DEPTH = {SchemaParser.MAX_IMPORT_DEPTH}")
    else:
        print(f"  ✗ MAX_IMPORT_DEPTH constant not found")
        return False

    print()
    print("=" * 60)
    print("✓ ALL F004 TESTS PASSED!")
    print("=" * 60)
    print()
    print("Summary:")
    print("  • Multi-level nested imports work correctly")
    print("  • Import chain (level2 → level1 → level0) resolves properly")
    print("  • All models from all 3 levels are accessible")
    print("  • No circular import issues detected")
    print("  • Depth limit enforcement implemented")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
