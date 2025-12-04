# F050 Quick Reference - Generate Command

## Command Syntax

```bash
schnitzel generate [SCHEMA_PATH]
```

## Arguments

- `SCHEMA_PATH` (optional): Path to the Schnitzel schema YAML file
  - Default: `schema.schnitzel.yaml`

## Examples

### Use Default Schema
```bash
schnitzel generate
```

### Use Custom Schema
```bash
schnitzel generate my-schema.yaml
schnitzel generate schemas/production.yaml
```

## What It Does

1. **Parses** the schema file using `SchemaParser`
2. **Validates** the schema using `SchemaValidator`
3. **Reports** validation errors with detailed context
4. **Displays** model information and constraints
5. **Returns** exit code 1 on failures

## Success Output Example

```
Parsing schema: schema.schnitzel.yaml
✓ Schema parsed successfully
  Models found: 2

Validating schema...
✓ Schema validation passed

Models validated:
  - User (4 fields)
  - Post (4 fields)

Unique constraints:
  - User.email
  - User.username

✓ Schema is ready for code generation
```

## Error Output Example

```
Parsing schema: invalid.yaml
✓ Schema parsed successfully
  Models found: 1

Validating schema...
✗ Schema validation failed:

  Error:
    Unsupported field type 'invalid_type' for field 'name' in model 'User'
    Supported types: bool, datetime, enum, float, int, json, string, uuid, vector, list<T>
```

## Exit Codes

- `0`: Success - schema is valid
- `1`: Failure - validation errors or file not found

## Common Errors

### Missing File
```
Error: Schema file not found: nonexistent.yaml
  Please ensure the file exists
```

### Invalid YAML Syntax
```
✗ YAML parsing failed:
  schema.yaml: Invalid YAML syntax at line 6, column 1
  Reason: expected ',' or ']', but got '<stream end>'
```

### Naming Convention Violations
```
✗ Schema validation failed:

  Error:
    Model name 'user_model' violates naming convention
    Model names must be PascalCase
    Suggested name: 'UserModel'

  Error:
    Field name 'userName' in model 'user_model' violates naming convention
    Field names must be snake_case
    Suggested name: 'user_name'
```

### Invalid Relationships
```
✗ Schema validation failed:

  Error:
    Relationship target model 'NonexistentUser' does not exist in schema
    Referenced in model 'Post' via belongsTo relationship 'author'
```

### Invalid Constraints
```
✗ Schema validation failed:

  Error:
    Invalid constraint values for field 'age' in model 'User'
    Minimum value (150) cannot be greater than maximum value (0)
    Ensure min <= max
```

## Testing

Run tests:
```bash
pytest tests/integration/test_cli_generate_f050.py -v
```

Run demo:
```bash
python demo_f050_generate.py
```

## Implementation Files

- **Command**: `src/schnitzel/cli/commands/generate.py`
- **Registration**: `src/schnitzel/cli/__init__.py`
- **Tests**: `tests/integration/test_cli_generate_f050.py`
- **Demo**: `demo_f050_generate.py`

## Related Commands

- `schnitzel validate`: Validates schema without generation context
- `schnitzel init`: Creates new project with schema template
- `schnitzel version`: Shows CLI version
