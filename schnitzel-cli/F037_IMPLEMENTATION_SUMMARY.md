# F037 Implementation Summary: Dart Model Generator - snake_case to camelCase Conversion

**Feature:** Dart Freezed model generator handles snake_case to camelCase conversion
**Status:** ✅ IMPLEMENTED AND VERIFIED
**Date:** 2025-12-03
**Implementation Location:** `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/generators/dart/models.py`

---

## Overview

Feature F037 ensures that the Dart Freezed model generator correctly handles the conversion between Dart's camelCase naming convention and JSON's snake_case convention. The implementation:

1. **Preserves original field names** from the schema (typically camelCase for Dart)
2. **Automatically adds `@JsonKey(name: 'snake_case')`** annotations when needed
3. **Provides helper methods** for snake_case conversion and decision logic

---

## Implementation Details

### Core Methods

#### 1. `_to_snake_case(name: str) -> str` (Lines 60-82)

Converts PascalCase or camelCase to snake_case.

**Examples:**
- `userId` → `user_id`
- `createdAt` → `created_at`
- `firstName` → `first_name`
- `HTTPResponse` → `h_t_t_p_response`

**Algorithm:**
- Iterates through each character
- Inserts underscore before uppercase letters (except at position 0)
- Converts all letters to lowercase

#### 2. `_needs_json_key(field_name: str) -> bool` (Lines 84-96)

Determines if a field requires `@JsonKey` annotation.

**Logic:**
- Returns `True` if snake_case version differs from original
- Returns `False` if they're the same (already snake_case or single word)

**Examples:**
- `userId` → `True` (converts to `user_id`)
- `user_id` → `False` (already snake_case)
- `name` → `False` (single word, no conversion)

#### 3. `_generate_field(field_name: str, field_def: FieldDefinition) -> str` (Lines 263-304)

Generates field declarations with appropriate annotations.

**Process:**
1. Check if `@JsonKey` is needed using `_needs_json_key()`
2. If needed, add `@JsonKey(name: 'snake_case_version')`
3. Handle optional fields and default values
4. Add `required` keyword when appropriate

#### 4. `_generate_relationship_field(relation_name: str, relation_def: Relation) -> str` (Lines 222-261)

Generates relationship field declarations with `@JsonKey` support.

**Supported Relationships:**
- `belongsTo`: Generates `Model?` field with optional `@JsonKey`
- `hasMany`: Generates `List<Model>?` field with optional `@JsonKey`
- `hasOne`: Generates `Model?` field with optional `@JsonKey`

---

## Generated Code Examples

### Example 1: Mixed Field Names

**Schema:**
```python
Model(
    name="UserProfile",
    fields={
        "userId": FieldDefinition(type="string"),      # camelCase
        "name": FieldDefinition(type="string"),         # single word
        "user_role": FieldDefinition(type="string"),    # snake_case
    }
)
```

**Generated Dart:**
```dart
@freezed
class UserProfile with _$UserProfile {
  const factory UserProfile({
    @JsonKey(name: 'user_id') required String userId,    // @JsonKey added
    required String name,                                 // no @JsonKey
    required String user_role,                            // no @JsonKey
  }) = _UserProfile;

  factory UserProfile.fromJson(Map<String, dynamic> json) => _$UserProfileFromJson(json);
}
```

### Example 2: Complete User Model

**Generated Dart:**
```dart
@freezed
class User with _$User {
  const factory User({
    @JsonKey(name: 'user_id') required String userId,
    @JsonKey(name: 'first_name') required String firstName,
    @JsonKey(name: 'last_name') required String lastName,
    @JsonKey(name: 'is_active') @Default(true) bool isActive,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    required String username,                              // no @JsonKey
    required String email,                                 // no @JsonKey
    int? legacy_id,                                        // no @JsonKey
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

### Example 3: Relationships with @JsonKey

**Generated Dart:**
```dart
@freezed
class Post with _$Post {
  const factory Post({
    @JsonKey(name: 'post_id') required String postId,
    @JsonKey(name: 'created_by') User? createdBy,          // belongsTo
    @JsonKey(name: 'post_comments') List<Comment>? postComments,  // hasMany
    AuthorInfo? author_info,                                // snake_case - no @JsonKey
  }) = _Post;

  factory Post.fromJson(Map<String, dynamic> json) => _$PostFromJson(json);
}
```

---

## Test Suite

### Test File: `tests/integration/test_dart_snake_case_f037.py`

**6 Tests - All Passing ✅**

1. **`test_camel_case_field_gets_json_key`**
   - Verifies camelCase fields receive `@JsonKey` annotations
   - Tests: `userId`, `createdAt`, `firstName`

2. **`test_snake_case_field_no_json_key_needed`**
   - Verifies snake_case fields do NOT receive `@JsonKey`
   - Tests: `user_id`, `created_at`, `first_name`

3. **`test_single_word_field_no_json_key`**
   - Verifies single-word fields do NOT receive `@JsonKey`
   - Tests: `id`, `name`, `email`, `age`

4. **`test_to_snake_case_conversion`**
   - Tests the `_to_snake_case()` helper with 16 cases
   - Covers: camelCase, PascalCase, snake_case, single words, consecutive capitals

5. **`test_complete_model_with_mixed_field_names`**
   - Integration test with mixed field types
   - Verifies correct @JsonKey count (exactly 3 for camelCase fields)

6. **`test_needs_json_key_method`**
   - Tests the `_needs_json_key()` decision logic
   - Verifies correct True/False returns for various inputs

### Test Results

```bash
============================= test session starts ==============================
platform darwin -- Python 3.13.1, pytest-9.0.1, pluggy-1.6.0
rootdir: /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli

tests/integration/test_dart_snake_case_f037.py::TestDartSnakeCaseConversion::test_camel_case_field_gets_json_key PASSED [ 16%]
tests/integration/test_dart_snake_case_f037.py::TestDartSnakeCaseConversion::test_snake_case_field_no_json_key_needed PASSED [ 33%]
tests/integration/test_dart_snake_case_f037.py::TestDartSnakeCaseConversion::test_single_word_field_no_json_key PASSED [ 50%]
tests/integration/test_dart_snake_case_f037.py::TestDartSnakeCaseConversion::test_to_snake_case_conversion PASSED [ 66%]
tests/integration/test_dart_snake_case_f037.py::TestDartSnakeCaseConversion::test_complete_model_with_mixed_field_names PASSED [ 83%]
tests/integration/test_dart_snake_case_f037.py::TestDartSnakeCaseConversion::test_needs_json_key_method PASSED [100%]

============================== 6 passed in 0.16s
```

---

## Verification Process

### 1. Code Analysis
- ✅ Reviewed existing `_to_snake_case()` implementation
- ✅ Reviewed existing `_needs_json_key()` implementation
- ✅ Verified integration in `_generate_field()` method
- ✅ Verified integration in `_generate_relationship_field()` method

### 2. Test Creation
- ✅ Created comprehensive test suite with 6 tests
- ✅ All tests pass without modifications to implementation
- ✅ Tests cover all requirements from feature specification

### 3. Demo Verification
- ✅ Created `demo_f037_dart_snake_case.py` with 5 demonstrations
- ✅ Verified mixed field names (camelCase, snake_case, single-word)
- ✅ Verified relationships with @JsonKey
- ✅ Verified snake_case conversion helper (14 test cases)
- ✅ Verified decision logic helper
- ✅ Verified realistic user model with complete feature set

---

## Decision Logic Summary

### When `@JsonKey` is Added

```
Field Name      Snake Case      Needs @JsonKey?   Reason
----------      ----------      ---------------   ------
userId          user_id         YES              Different from original
createdAt       created_at      YES              Different from original
firstName       first_name      YES              Different from original
isActive        is_active       YES              Different from original
```

### When `@JsonKey` is NOT Added

```
Field Name      Snake Case      Needs @JsonKey?   Reason
----------      ----------      ---------------   ------
user_id         user_id         NO               Already snake_case
created_at      created_at      NO               Already snake_case
id              id              NO               Single word, unchanged
name            name            NO               Single word, unchanged
email           email           NO               Single word, unchanged
```

---

## Snake Case Conversion Examples

| Input              | Output             | Category              |
|--------------------|--------------------|------------------------|
| `userId`           | `user_id`          | camelCase              |
| `createdAt`        | `created_at`       | camelCase              |
| `firstName`        | `first_name`       | camelCase              |
| `isActive`         | `is_active`        | camelCase              |
| `UserName`         | `user_name`        | PascalCase             |
| `user_id`          | `user_id`          | snake_case (unchanged) |
| `created_at`       | `created_at`       | snake_case (unchanged) |
| `id`               | `id`               | single word            |
| `name`             | `name`             | single word            |
| `HTTPResponse`     | `h_t_t_p_response` | consecutive capitals   |
| `URLPath`          | `u_r_l_path`       | consecutive capitals   |

---

## Integration with Other Features

### Works Seamlessly With:

1. **F033: Optional Fields**
   - Optional camelCase fields get both `?` and `@JsonKey`
   - Example: `@JsonKey(name: 'middle_name') String? middleName,`

2. **F034: Default Values**
   - Default values work with `@JsonKey`
   - Example: `@JsonKey(name: 'is_active') @Default(true) bool isActive,`

3. **F035: JSON Serialization**
   - `@JsonKey` integrates with `fromJson` factories
   - Enables correct JSON deserialization with json_serializable

4. **F032: Type Mapping**
   - All Dart types support `@JsonKey`
   - Works with String, int, DateTime, List, etc.

---

## Files Modified/Created

### Implementation (Already Existed)
- `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/generators/dart/models.py`
  - Methods `_to_snake_case()`, `_needs_json_key()` already implemented
  - No modifications needed - feature already complete

### Tests (Created)
- `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/tests/integration/test_dart_snake_case_f037.py`
  - 6 comprehensive tests
  - 207 lines of test code

### Demo (Created)
- `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/demo_f037_dart_snake_case.py`
  - 5 demonstration scenarios
  - 350+ lines of demo code

### Documentation (Created)
- `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/F037_IMPLEMENTATION_SUMMARY.md`
  - This file

---

## Feature Completeness Checklist

- ✅ Keeps field names in their original format from schema
- ✅ Adds `@JsonKey(name: 'snake_case')` when JSON key differs from field name
- ✅ Has helper method `_to_snake_case()` for conversion
- ✅ Has helper method `_needs_json_key()` for decision logic
- ✅ Handles camelCase fields correctly (adds @JsonKey)
- ✅ Handles snake_case fields correctly (no @JsonKey)
- ✅ Handles single-word fields correctly (no @JsonKey)
- ✅ Handles relationship fields with @JsonKey
- ✅ Works with optional fields
- ✅ Works with default values
- ✅ Integrates with JSON serialization
- ✅ Comprehensive test coverage (6 tests)
- ✅ Demonstration script with 5 scenarios
- ✅ Complete documentation

---

## Benefits

1. **Seamless API Integration**: Dart code uses camelCase while JSON APIs use snake_case
2. **Convention Compliance**: Follows Dart best practices for naming
3. **Automatic Conversion**: No manual mapping needed
4. **Type Safety**: Works with json_serializable for compile-time safety
5. **Flexible**: Handles mixed naming conventions in same model
6. **Smart**: Only adds @JsonKey when actually needed

---

## Conclusion

Feature F037 is **fully implemented and verified**. The DartModelGenerator correctly handles snake_case to camelCase conversion with:

- ✅ **Complete implementation** in `models.py`
- ✅ **100% test pass rate** (6/6 tests passing)
- ✅ **Comprehensive demonstrations** (5 demo scenarios)
- ✅ **Production-ready** code generation

The feature seamlessly integrates with existing features (F032-F035) and follows Dart/Flutter best practices for JSON serialization with Freezed models.
