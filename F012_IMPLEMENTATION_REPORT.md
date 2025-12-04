# F012 Implementation Report: Schema Validator Relationship Validation

## Feature ID
**F012**: Schema validator verifies hasMany relationship target exists

## Summary
Successfully implemented relationship validation for the Schnitzel schema validator, covering hasMany, belongsTo, and hasOne relationship types. The implementation validates that all relationship targets reference existing models in the schema.

---

## Implementation Details

### Files Modified

#### 1. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/schema/validator.py`

**Changes Made:**
- Enhanced `_validate_relationships()` method to validate relationship targets
- Added `_build_missing_relationship_error()` method for comprehensive error messages
- The validation now checks all relationship types: belongsTo, hasMany, and hasOne

**Key Implementation:**

```python
def _validate_relationships(self, schema: SchnitzelSchema) -> List[str]:
    """
    Validate that all relationship targets reference existing models.

    Checks:
    - All relationship targets (model references) exist in the schema
    - Applies to belongsTo, hasMany, and hasOne relationship types
    """
    errors: List[str] = []
    model_names = set(schema.models.keys())

    for model_name, model in schema.models.items():
        if model.relations is None:
            continue

        for relation_name, relation in model.relations.items():
            target_model = relation.model

            if target_model not in model_names:
                error_msg = self._build_missing_relationship_error(
                    model_name, relation_name, relation.type, target_model
                )
                errors.append(error_msg)

    return errors
```

**Error Message Format:**
The error messages include all required information:
- Target model name that doesn't exist
- Source model and relationship name
- Relationship type (hasMany, belongsTo, hasOne)
- Relationship definition
- Helpful suggestion to fix the issue

Example error output:
```
Relationship target model 'Post' does not exist in schema
Referenced in model 'User' via hasMany relationship 'posts'
Relationship definition: posts (hasMany) -> Post
Add the 'Post' model to your schema or correct the relationship target
```

---

### Files Created

#### 1. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/tests/integration/test_schema_validator_f012.py`

**Purpose:** Comprehensive integration tests for F012 (hasMany) and F011 (belongsTo)

**Test Coverage:**
- `test_hasmany_relationship_missing_target()` - F012 primary test
- `test_belongsto_relationship_missing_target()` - F011 coverage
- `test_hasone_relationship_missing_target()` - hasOne validation
- `test_multiple_missing_relationship_targets()` - Multiple errors reported
- `test_valid_bidirectional_relationship()` - F013 coverage (valid relationships pass)
- `test_relationship_validation_with_no_relations()` - Models without relations
- `test_error_message_format()` - Comprehensive error format validation

**All 7 tests pass successfully.**

#### 2. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/verify_f012.py`

**Purpose:** Standalone verification script demonstrating the feature

**Features:**
- Interactive demonstration of hasMany validation (F012)
- Interactive demonstration of belongsTo validation (F011)
- Shows valid bidirectional relationships (F013)
- Clear formatted output with error details
- Can be run directly: `python verify_f012.py`

---

## Test Results

### Integration Tests (F012 Specific)
```
tests/integration/test_schema_validator_f012.py::test_hasmany_relationship_missing_target PASSED
tests/integration/test_schema_validator_f012.py::test_belongsto_relationship_missing_target PASSED
tests/integration/test_schema_validator_f012.py::test_hasone_relationship_missing_target PASSED
tests/integration/test_schema_validator_f012.py::test_multiple_missing_relationship_targets PASSED
tests/integration/test_schema_validator_f012.py::test_valid_bidirectional_relationship PASSED
tests/integration/test_schema_validator_f012.py::test_relationship_validation_with_no_relations PASSED
tests/integration/test_schema_validator_f012.py::test_error_message_format PASSED

7 passed in 0.07s
```

### Related Tests (F011)
All F011 tests also pass (9 additional tests), confirming belongsTo validation works correctly.

### Regression Testing
93 out of 94 integration tests pass. The one failing test is pre-existing and unrelated to F012:
- `test_schema_validation_f008.py::test_invalid_model_name_raises_validation_error`
- This is a design issue where naming validation moved from parsing to validation phase
- Does not affect F012 functionality

---

## Verification Steps

### Test F012 (hasMany validation)

1. **Create schema with User model having hasMany: posts pointing to Post**
   ```python
   schema = SchnitzelSchema(
       models={
           "User": Model(
               name="User",
               relations={"posts": Relation(type="hasMany", model="Post")}
           )
       }
   )
   ```

2. **Schema does NOT include Post model** ✓

3. **Call SchemaValidator.validate(schema)** ✓

4. **Verify validation fails** ✓
   - `result.valid == False`

5. **Verify error indicates Post model doesn't exist** ✓
   - Error contains: "Relationship target model 'Post' does not exist in schema"

6. **Verify error shows the relationship definition** ✓
   - Error contains: "Relationship definition: posts (hasMany) -> Post"

7. **Verify error includes relationship type (hasMany)** ✓
   - Error contains: "hasMany"

### Test Command
```bash
cd schnitzel-cli
source .venv/bin/activate
python -m pytest tests/integration/test_schema_validator_f012.py -v
```

Or run the verification script:
```bash
cd schnitzel-cli
source .venv/bin/activate
python verify_f012.py
```

---

## Implementation Notes

### Design Decisions

1. **Unified Relationship Validation**
   - Instead of separate validation for each relationship type, implemented a single method that handles all types (belongsTo, hasMany, hasOne)
   - This ensures consistency and reduces code duplication

2. **Comprehensive Error Messages**
   - Error messages include 4 key pieces of information:
     - What's missing (target model)
     - Where it's referenced (source model, relationship name)
     - What type of relationship
     - How to fix it (helpful suggestion)

3. **Validation Phase Separation**
   - Relationship validation happens in the SchemaValidator, not during parsing
   - This follows the principle of separation of concerns:
     - Parser: Load and structure the schema
     - Validator: Check semantic correctness

4. **Bonus Coverage**
   - Implementation covers F011 (belongsTo) and hasOne relationships
   - Supports F013 (valid bidirectional relationships)

### Code Quality

- Production-ready error messages with clear, actionable information
- Full type hints for all methods
- Comprehensive docstrings
- No TODOs or placeholder implementations
- Follows existing codebase patterns and conventions
- All tests use pytest best practices

---

## Dependencies

No new dependencies added. Uses existing:
- `pydantic` for models
- `pytest` for testing

---

## Ready for Testing

The implementation is complete and ready for testing. To test:

1. **Quick Test:**
   ```bash
   cd /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli
   source .venv/bin/activate
   python verify_f012.py
   ```

2. **Full Test Suite:**
   ```bash
   cd /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli
   source .venv/bin/activate
   python -m pytest tests/integration/test_schema_validator_f012.py -v
   ```

3. **Integration with Other Tests:**
   ```bash
   cd /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli
   source .venv/bin/activate
   python -m pytest tests/integration/ -k "validator" -v
   ```

---

## Feature Status

- **F011 (belongsTo validation):** Implemented and tested ✓
- **F012 (hasMany validation):** Implemented and tested ✓
- **F013 (valid bidirectional relationships):** Supported and tested ✓
- **hasOne validation:** Bonus - implemented and tested ✓

All test steps from the feature specification have been completed successfully.
