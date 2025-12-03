# Multi-Level Nested Imports Test Fixtures (F004)

This directory contains test fixtures for verifying F004: multi-level nested import resolution.

## Import Chain Structure

```
level2.yaml
    ↓ imports
level1.yaml
    ↓ imports
level0.yaml
```

## File Contents

### level0.yaml (Base Level)
- **Project**: Level 0 Base
- **Models**: `BaseModel`
- **Fields**: id (uuid), created_at (datetime), updated_at (datetime)
- **Imports**: None

### level1.yaml (Middle Level)
- **Project**: Level 1 User
- **Models**: `UserModel`
- **Fields**: username (string), email (string), is_active (bool)
- **Imports**: level0.yaml

### level2.yaml (Top Level)
- **Project**: Level 2 Post
- **Models**: `PostModel`
- **Fields**: title (string), content (string), author_id (uuid)
- **Imports**: level1.yaml

## Expected Behavior

When parsing `level2.yaml`, the SchemaParser should:

1. Parse level2.yaml
2. Detect import of level1.yaml
3. Recursively parse level1.yaml
4. Detect import of level0.yaml
5. Recursively parse level0.yaml
6. Merge models from all three levels
7. Return a schema with all 3 models accessible

## Verification

Run the verification script:

```bash
python3 tests/integration/verify_f004.py
```

Or use pytest:

```bash
pytest tests/integration/test_multi_level_imports.py -v
```

## Success Criteria

- ✓ All three models (BaseModel, UserModel, PostModel) are present
- ✓ Import chain resolves in correct order
- ✓ No circular import issues
- ✓ Models from all levels are accessible
- ✓ Field types are correctly parsed
- ✓ Depth limit (MAX_IMPORT_DEPTH = 10) is enforced
