# F077 Implementation Summary: Schema Validator Detects Duplicate Field Names

## Overview
Feature F077 adds duplicate field name detection to the Schnitzel CLI schema parser. When a model definition contains the same field name multiple times, the parser now detects this and provides a clear, helpful error message.

## Implementation Details

### Architecture
The implementation consists of two main components:

1. **Custom YAML Loader (`DuplicateKeyDetector`)**
   - Extends `yaml.SafeLoader` to detect duplicate keys during YAML parsing
   - Overrides `construct_mapping()` to check for duplicate keys
   - Raises `yaml.constructor.ConstructorError` when duplicates are found

2. **Enhanced Error Handling in `SchemaParser`**
   - Catches `ConstructorError` from the custom loader
   - Extracts duplicate key information and line numbers
   - Formats user-friendly error messages with context

### Key Files Modified

#### `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/schema/parser.py`
- Added `DuplicateKeyDetector` class (custom YAML loader)
- Added `DuplicateFieldError` exception class
- Modified `_load_yaml()` to use `DuplicateKeyDetector`
- Enhanced error handling for duplicate key detection

### Key Files Created

#### `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/tests/integration/test_duplicate_field_names_f077.py`
Comprehensive test suite with 7 tests covering:
- Duplicate field detection in YAML files
- Unique field names pass validation
- Multiple models can have fields with same names
- YAML parser duplicate key detection
- Error message clarity and helpfulness
- Field count verification
- Field iteration functionality

#### `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/demo_f077_duplicate_fields.py`
Demonstration script showing:
- Duplicate field detection with clear error messages
- Valid schemas with unique field names
- Different models with same field names (valid case)
- Duplicate fields with different types

## How It Works

### Duplicate Detection Process

1. **YAML Parsing**
   - When `SchemaParser.parse()` is called, it reads the YAML file
   - Uses `DuplicateKeyDetector` instead of standard `yaml.safe_load()`
   - The custom loader checks each key in every mapping

2. **Duplicate Found**
   - If a key appears twice in the same mapping, `ConstructorError` is raised
   - Error includes the duplicate key name and line number

3. **Error Formatting**
   - Parser catches the `ConstructorError`
   - Extracts line number, duplicate key name, and line content
   - Creates a `YAMLParseError` with detailed context

4. **User Feedback**
   - Error message shows:
     - File name and line number
     - The duplicate field name
     - The actual line content
     - Clear explanation that field names must be unique
     - Helpful tip to check for duplicate names

### Example Error Message

```
tmp2sr0vjod.yaml: Invalid YAML syntax at line 13
  Reason: Duplicate key found in tmp2sr0vjod.yaml
Line 13
Content: name:

Error: 'name'
  in "<unicode string>", line 13, column 7:
          name:
          ^

Each field name must be unique within a model.
Tip: Check for field names that appear multiple times.
  Line content: "name:"
```

## Test Coverage

### Test Suite (`test_duplicate_field_names_f077.py`)

1. **test_duplicate_field_detected**
   - Creates YAML with duplicate `name` field
   - Verifies `YAMLParseError` is raised
   - Confirms error mentions "duplicate" and the field name

2. **test_unique_fields_pass**
   - Verifies schemas with unique field names pass validation
   - Tests multiple unique fields in a single model

3. **test_multiple_models_with_unique_fields**
   - Confirms different models can have fields with same names
   - Tests `User.name` and `Product.name` coexisting

4. **test_yaml_duplicate_detection**
   - Verifies custom YAML parser detects duplicates
   - Tests duplicate `email` field detection

5. **test_error_mentions_field_and_model**
   - Validates error message quality
   - Checks for "duplicate", field name, and "unique" in message

6. **test_field_count_after_construction**
   - Ensures programmatic model creation has correct field count
   - Verifies all field names are unique

7. **test_field_iteration**
   - Tests iterating over model fields
   - Verifies field name and definition types

### Test Results
```
7 passed in 0.05s
```

All tests pass successfully, and no existing tests were broken by the implementation.

## Design Decisions

### Why Custom YAML Loader?

**Decision**: Implement a custom YAML loader instead of post-parse validation

**Rationale**:
1. **Early Detection**: Catches duplicates during parsing, not after
2. **Better Error Context**: YAML parser provides exact line numbers
3. **Prevents Silent Errors**: Default PyYAML behavior is to silently use the last value
4. **User-Friendly**: Users get immediate feedback at the source of the problem

### Why Not Validator-Based Detection?

**Consideration**: Could add duplicate detection to `SchemaValidator`

**Why Not Chosen**:
1. By the time validator runs, duplicates are already lost (Python dicts can't have duplicate keys)
2. Parser-level detection provides better error messages with line numbers
3. Validation happens after parsing, so errors are caught later
4. YAML-level detection is more accurate and informative

### Python Dict Behavior

**Important Note**: Python dictionaries inherently prevent duplicate keys. When you write:
```python
{"name": "string", "name": "int"}
```
Python automatically uses the last value. The YAML parser exhibits the same behavior by default, which is why custom loader is essential.

## Integration with Existing Code

### Backward Compatibility
- ✅ All existing tests pass (57 tests in parser/validator suite)
- ✅ No changes to public APIs
- ✅ Existing schemas continue to work
- ✅ Only affects schemas with duplicate fields (which were silently broken before)

### Error Handling Chain
1. YAML file contains duplicate field
2. `DuplicateKeyDetector.construct_mapping()` detects it
3. Raises `yaml.constructor.ConstructorError`
4. `SchemaParser._load_yaml()` catches it
5. Extracts context and formats error
6. Raises `YAMLParseError` with detailed message
7. User sees clear, actionable error

## Usage Examples

### Invalid Schema (Detected)
```yaml
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      name:  # ❌ Duplicate field - will be detected
        type: int
```

**Result**: Clear error message identifying the duplicate field

### Valid Schema
```yaml
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      first_name:  # ✅ Unique field name
        type: string
      last_name:   # ✅ Unique field name
        type: string
```

**Result**: Schema parses successfully

### Multiple Models (Valid)
```yaml
schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
      name:  # ✅ OK in User model
        type: string
  Product:
    fields:
      id:
        type: uuid
      name:  # ✅ OK in Product model (different model)
        type: string
```

**Result**: Schema parses successfully - different models can have fields with the same name

## Benefits

### For Users
1. **Immediate Feedback**: Errors detected during parsing, not later
2. **Clear Error Messages**: Line numbers and field names clearly identified
3. **Actionable Guidance**: Tips help users fix the problem
4. **Prevents Silent Bugs**: No more "last value wins" silent failures

### For Developers
1. **Early Detection**: Catches errors before they reach code generation
2. **Better Debugging**: Line numbers make issues easy to locate
3. **Type Safety**: Prevents schema inconsistencies
4. **Maintainability**: Clear separation of concerns (parsing vs validation)

## Testing Instructions

### Run F077 Tests
```bash
cd /Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli
.venv/bin/python -m pytest tests/integration/test_duplicate_field_names_f077.py -v
```

### Run Demo
```bash
.venv/bin/python demo_f077_duplicate_fields.py
```

### Run All Parser/Validator Tests
```bash
.venv/bin/python -m pytest tests/integration/test_schema_parser*.py tests/integration/test_schema_validator*.py -v
```

## Verification

### Test Results
- ✅ 7 F077-specific tests pass
- ✅ 57 parser/validator tests pass
- ✅ No regression in existing functionality
- ✅ Demo script runs successfully

### Code Quality
- ✅ Type hints maintained
- ✅ Docstrings added to new classes/methods
- ✅ Error messages are clear and actionable
- ✅ Follows existing code patterns

## Conclusion

Feature F077 successfully implements duplicate field name detection at the YAML parsing level. The implementation:

1. **Detects duplicates early** during file parsing
2. **Provides clear error messages** with line numbers and context
3. **Maintains backward compatibility** with existing schemas
4. **Passes all tests** without breaking existing functionality
5. **Follows best practices** for error handling and user feedback

The custom YAML loader approach ensures users get immediate, actionable feedback when they accidentally define duplicate fields in their schema files.
