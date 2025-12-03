#!/usr/bin/env python3
"""
Test depth limit enforcement for import resolution.

This test verifies that the MAX_IMPORT_DEPTH limit prevents
excessively deep import chains.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.exceptions import ImportError as SchnitzelImportError


def create_deep_import_chain(depth: int, temp_dir: Path) -> Path:
    """
    Create a chain of imports of specified depth.

    Returns the path to the deepest (top-level) file.
    """
    files = []

    for i in range(depth):
        filename = f"level{i}.yaml"
        filepath = temp_dir / filename

        content_lines = [
            f'project_name: "Level {i}"',
            'version: "1.0.0"',
            '',
        ]

        # Add import to previous level (if not the first file)
        if i > 0:
            content_lines.extend([
                'imports:',
                f'  - level{i-1}.yaml',
                '',
            ])

        # Add a unique model
        content_lines.extend([
            'models:',
            f'  Model{i}:',
            '    fields:',
            '      id:',
            '        type: uuid',
        ])

        filepath.write_text('\n'.join(content_lines))
        files.append(filepath)

    return files[-1]  # Return the top-level file


def test_depth_within_limit():
    """Test that imports within MAX_IMPORT_DEPTH work fine."""
    print("\n[Test] Import depth within limit (depth=5)")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a chain of 5 imports (well within the limit of 10)
        top_file = create_deep_import_chain(5, temp_path)

        try:
            parser = SchemaParser()
            schema = parser.parse(top_file)

            # Should have 5 models
            assert len(schema.models) == 5, f"Expected 5 models, got {len(schema.models)}"
            print(f"  ✓ Successfully parsed 5-level import chain")
            print(f"  ✓ Models found: {', '.join(schema.models.keys())}")
            return True

        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return False


def test_depth_at_limit():
    """Test that imports at exactly MAX_IMPORT_DEPTH work."""
    print("\n[Test] Import depth at limit (depth=10)")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a chain of exactly 10 imports (at the limit)
        top_file = create_deep_import_chain(10, temp_path)

        try:
            parser = SchemaParser()
            schema = parser.parse(top_file)

            # Should have 10 models
            assert len(schema.models) == 10, f"Expected 10 models, got {len(schema.models)}"
            print(f"  ✓ Successfully parsed 10-level import chain (at limit)")
            print(f"  ✓ Models found: {len(schema.models)}")
            return True

        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return False


def test_depth_exceeds_limit():
    """Test that imports exceeding MAX_IMPORT_DEPTH raise an error."""
    print("\n[Test] Import depth exceeds limit (depth=11)")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a chain of 11 imports (exceeds the limit of 10)
        top_file = create_deep_import_chain(11, temp_path)

        try:
            parser = SchemaParser()
            schema = parser.parse(top_file)

            print(f"  ✗ Should have raised ImportError for depth=11")
            return False

        except SchnitzelImportError as e:
            error_msg = str(e)
            if "depth exceeded" in error_msg.lower() or "maximum" in error_msg.lower():
                print(f"  ✓ Correctly raised ImportError for depth=11")
                print(f"  ✓ Error message: {error_msg[:100]}...")
                return True
            else:
                print(f"  ✗ Wrong error message: {error_msg}")
                return False

        except Exception as e:
            print(f"  ✗ Wrong exception type: {type(e).__name__}: {e}")
            return False


def main():
    """Run all depth limit tests."""
    print("=" * 60)
    print("Depth Limit Enforcement Tests")
    print("=" * 60)

    results = []

    # Test 1: Within limit
    results.append(test_depth_within_limit())

    # Test 2: At limit
    results.append(test_depth_at_limit())

    # Test 3: Exceeds limit
    results.append(test_depth_exceeds_limit())

    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL DEPTH LIMIT TESTS PASSED!")
        print("=" * 60)
        return True
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
