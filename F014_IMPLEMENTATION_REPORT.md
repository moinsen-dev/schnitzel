# F014 Implementation Report

## Feature: Schema validator enforces PascalCase naming for models

### Implementation Complete

**Date:** 2025-12-03
**Feature ID:** F014
**Status:** ✓ Complete and Tested

---

## Files Modified

### 1. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/schema/validator.py`

**Changes:**
- Added `_validate_model_name()` method to validate PascalCase naming
- Added `_is_pascal_case()` helper to detect PascalCase names
- Added `_to_pascal_case()` helper to convert various naming conventions to PascalCase
- Updated `_validate_model()` to call model name validation
- Enhanced `_to_pascal_case()` to handle ALL_CAPS acronyms correctly

**Key Implementation:**
```python
def _validate_model_name(self, model_name: str) -> str | None:
    """Validate that a model name follows PascalCase naming convention."""
    if not model_name:
        return "Model name cannot be empty"

    if not self._is_pascal_case(model_name):
        error_parts = []
        error_parts.append(f"Model name '{model_name}' violates naming convention")
        error_parts.append("Model names must be PascalCase")
        suggested_name = self._to_pascal_case(model_name)
        error_parts.append(f"Suggested name: '{suggested_name}'")
        return "\n".join(error_parts)

    return None
```

### 2. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/schema/models.py`

**Changes:**
- Updated `Model.validate_name_pascal_case()` Pydantic validator to only check for empty names
- Renamed to `validate_name_not_empty()` to reflect new responsibility
- Added comment explaining that full PascalCase validation is in SchemaValidator

**Rationale:**
Moved PascalCase validation from Pydantic to SchemaValidator to provide better error messages with suggestions. Pydantic now only validates that names are not empty (basic syntax), while SchemaValidator handles semantic validation (naming conventions).

### 3. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/tests/integration/test_model_naming_convention_f014.py`

**Created:** New integration test file with 11 comprehensive tests

**Tests:**
1. `test_snake_case_model_name_fails_validation` - Main test case
2. `test_error_format_matches_specification` - Validates error message format
3. `test_kebab_case_model_name_fails` - Tests kebab-case detection
4. `test_lowercase_model_name_fails` - Tests lowercase detection
5. `test_camel_case_model_name_fails` - Tests camelCase detection
6. `test_valid_pascal_case_passes` - Tests valid PascalCase names
7. `test_multiple_models_with_naming_errors` - Tests multiple error reporting
8. `test_name_conversion_suggestions` - Tests name conversion accuracy
9. `test_empty_model_name_fails` - Tests empty name handling
10. `test_model_with_numbers_in_name` - Tests names with numbers
11. `test_model_naming_with_field_naming` - Tests combined validations

### 4. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/tests/integration/test_schema_validation_f008.py`

**Changes:**
- Updated `test_invalid_model_name_raises_validation_error()` to reflect new architecture
- Changed expectation from raising ValidationError to successfully parsing
- Added documentation explaining that PascalCase validation is now in F014

---

## Implementation Details

### PascalCase Detection

The `_is_pascal_case()` method checks:
- First character must be uppercase
- No underscores or hyphens allowed
- Only alphanumeric characters
- Whole name must match this pattern

### Name Conversion

The `_to_pascal_case()` method handles:
- **snake_case** → PascalCase (user_profile → UserProfile)
- **kebab-case** → PascalCase (user-profile → UserProfile)
- **camelCase** → PascalCase (userProfile → UserProfile)
- **space separated** → PascalCase (user profile → UserProfile)
- **ALL_CAPS** → PascalCase (API_KEY → ApiKey)

### Error Message Format

As specified in requirements:
```
Model name 'user_profile' violates naming convention
Model names must be PascalCase
Suggested name: 'UserProfile'
```

---

## Test Results

### All Integration Tests: ✓ PASS

```bash
pytest tests/integration/ -v
94 passed, 3 warnings in 0.16s
```

### F014 Specific Tests: ✓ PASS

```bash
pytest tests/integration/test_model_naming_convention_f014.py -v
11 passed in 0.06s
```

---

## Verification Steps

### Manual Testing

Created `demo_f014.py` to demonstrate the feature:

```bash
PYTHONPATH=schnitzel-cli/src python3 demo_f014.py
```

**Demo Output:**
- Invalid snake_case: `user_profile` → Suggested: `UserProfile` ✓
- Invalid kebab-case: `user-profile` → Suggested: `UserProfile` ✓
- Invalid camelCase: `userProfile` → Suggested: `UserProfile` ✓
- Valid PascalCase: `User`, `UserProfile`, `OrderItem`, `HTTPServer` ✓
- Multiple errors: Correctly reports all violations ✓

### Automated Testing

```python
# Test Case 1: Create schema with model named 'user_profile' (snake_case)
schema = SchnitzelSchema(
    models={
        "user_profile": Model(
            name="user_profile",
            fields={"id": FieldDefinition(type="uuid", primary=True)}
        )
    }
)

# Test Case 2: Call SchemaValidator.validate(schema)
validator = SchemaValidator()
result = validator.validate(schema)

# Test Case 3: Verify validation fails
assert result.valid is False  ✓

# Test Case 4: Verify error indicates naming convention violation
assert "violates naming convention" in error_message  ✓

# Test Case 5: Verify error suggests correct name 'UserProfile'
assert "UserProfile" in error_message  ✓

# Test Case 6: Verify error references naming convention rules
assert "PascalCase" in error_message  ✓
```

---

## Edge Cases Handled

1. **Empty names**: Returns "Model name cannot be empty"
2. **Names with numbers**: Correctly validates (User2FA ✓, user_2fa ✗)
3. **All uppercase acronyms**: Converts properly (API_KEY → ApiKey)
4. **Multiple violations**: Reports all errors at once
5. **Mixed validation**: Works alongside field name validation (F015)

---

## Architecture Decisions

### Separation of Concerns

1. **Pydantic (models.py)**: Basic syntax validation (non-empty)
2. **SchemaValidator (validator.py)**: Semantic validation (naming conventions)

This separation allows:
- Better error messages with suggestions
- Consistent validation API across all validations
- Easier testing and maintenance

### Validation Flow

```
YAML File
    ↓
SchemaParser.parse()
    ↓ (Pydantic validates non-empty)
SchnitzelSchema object
    ↓
SchemaValidator.validate()
    ↓ (Validates PascalCase)
ValidationResult
```

---

## Test Command

To run all tests including F014:

```bash
cd schnitzel-cli
source .venv/bin/activate
pytest tests/integration/test_model_naming_convention_f014.py -v
```

To run the demo:

```bash
PYTHONPATH=schnitzel-cli/src python3 demo_f014.py
```

---

## Dependencies Added

None - uses existing dependencies (re, typing, pydantic)

---

## Implementation Notes

### Design Decisions

1. **Moved validation from Pydantic to SchemaValidator**: This provides better error messages and maintains consistency with other validations (field type validation, relationship validation).

2. **Helper methods are reusable**: The `_is_pascal_case()` and `_to_pascal_case()` methods can be reused for other PascalCase validations in the future.

3. **Field name validation already existed**: The validator already had `_validate_field_name()` for snake_case validation (F015), so we followed the same pattern.

### Breaking Changes

The Pydantic validator in `Model` class previously checked if the first character was uppercase. This has been relaxed to only check for non-empty. This is intentional and improves error messages.

**Impact:** Test F008's `test_invalid_model_name_raises_validation_error` was updated to reflect the new architecture.

---

## Ready for Production

- ✓ All tests pass
- ✓ No regressions in existing tests
- ✓ Error messages follow specification
- ✓ Suggestions are accurate
- ✓ Edge cases handled
- ✓ Documentation complete
- ✓ Demo script works

---

## Future Enhancements

Potential improvements (not in scope for F014):

1. Custom naming convention configuration (e.g., allow snake_case in specific contexts)
2. Auto-fix capability to rename models automatically
3. VS Code extension integration for real-time validation
4. Performance optimization for large schemas (if needed)

---

## Summary

Feature F014 has been successfully implemented and thoroughly tested. The SchemaValidator now enforces PascalCase naming for models with clear error messages and helpful suggestions. All 94 integration tests pass, including 11 new tests specifically for F014.
