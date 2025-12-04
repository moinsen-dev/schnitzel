# F033 Examples: Dart Freezed Optional/Nullable Fields

## Example 1: Required Fields Only

### Schema Definition
```python
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition

schema = SchnitzelSchema(
    models={
        "User": Model(
            name="User",
            fields={
                "id": FieldDefinition(type="string", optional=False),
                "name": FieldDefinition(type="string", optional=False),
                "email": FieldDefinition(type="string", optional=False),
            }
        )
    }
)
```

### Generated Dart Code
```dart
@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

## Example 2: Optional Fields Only

### Schema Definition
```python
schema = SchnitzelSchema(
    models={
        "Profile": Model(
            name="Profile",
            fields={
                "bio": FieldDefinition(type="string", optional=True),
                "age": FieldDefinition(type="int", optional=True),
                "website": FieldDefinition(type="string", optional=True),
            }
        )
    }
)
```

### Generated Dart Code
```dart
@freezed
class Profile with _$Profile {
  const factory Profile({
    String? bio,
    int? age,
    String? website,
  }) = _Profile;

  factory Profile.fromJson(Map<String, dynamic> json) => _$ProfileFromJson(json);
}
```

## Example 3: Mixed Required and Optional Fields

### Schema Definition
```python
schema = SchnitzelSchema(
    models={
        "User": Model(
            name="User",
            fields={
                # Required fields
                "id": FieldDefinition(type="string", optional=False),
                "name": FieldDefinition(type="string", optional=False),
                "email": FieldDefinition(type="string", optional=False),
                
                # Optional fields
                "bio": FieldDefinition(type="string", optional=True),
                "age": FieldDefinition(type="int", optional=True),
                "avatar_url": FieldDefinition(type="string", optional=True),
            }
        )
    }
)
```

### Generated Dart Code
```dart
@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
    String? bio,
    int? age,
    String? avatar_url,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

## Example 4: Various Data Types

### Schema Definition
```python
schema = SchnitzelSchema(
    models={
        "TestModel": Model(
            name="TestModel",
            fields={
                # Required fields with various types
                "id": FieldDefinition(type="uuid", optional=False),
                "created_at": FieldDefinition(type="datetime", optional=False),
                "active": FieldDefinition(type="bool", optional=False),
                
                # Optional fields with various types
                "score": FieldDefinition(type="float", optional=True),
                "metadata": FieldDefinition(type="json", optional=True),
                "updated_at": FieldDefinition(type="datetime", optional=True),
            }
        )
    }
)
```

### Generated Dart Code
```dart
@freezed
class TestModel with _$TestModel {
  const factory TestModel({
    required String id,
    required DateTime created_at,
    required bool active,
    double? score,
    Map<String, dynamic>? metadata,
    DateTime? updated_at,
  }) = _TestModel;

  factory TestModel.fromJson(Map<String, dynamic> json) => _$TestModelFromJson(json);
}
```

## Example 5: List Types

### Schema Definition
```python
schema = SchnitzelSchema(
    models={
        "Article": Model(
            name="Article",
            fields={
                # Required list field
                "tags": FieldDefinition(type="list<string>", optional=False),
                
                # Optional list field
                "categories": FieldDefinition(type="list<string>", optional=True),
            }
        )
    }
)
```

### Generated Dart Code
```dart
@freezed
class Article with _$Article {
  const factory Article({
    required List<String> tags,
    List<String>? categories,
  }) = _Article;

  factory Article.fromJson(Map<String, dynamic> json) => _$ArticleFromJson(json);
}
```

## Type Mapping Reference

| Schema Type | Dart Type | Required Example | Optional Example |
|-------------|-----------|------------------|------------------|
| `string` | `String` | `required String name` | `String? name` |
| `uuid` | `String` | `required String id` | `String? id` |
| `int` | `int` | `required int count` | `int? count` |
| `float` | `double` | `required double price` | `double? price` |
| `bool` | `bool` | `required bool active` | `bool? active` |
| `datetime` | `DateTime` | `required DateTime date` | `DateTime? date` |
| `json` | `Map<String, dynamic>` | `required Map<String, dynamic> data` | `Map<String, dynamic>? data` |
| `list<string>` | `List<String>` | `required List<String> items` | `List<String>? items` |

## Usage in Code

### Basic Usage
```python
from schnitzel.generators.dart.models import DartModelGenerator

# Create generator
generator = DartModelGenerator()

# Generate code
dart_code = generator.generate(schema)
print(dart_code)
```

### Write to File
```python
from pathlib import Path

# Generate and write to file
output_path = generator.generate_to_file(
    schema=schema,
    output_dir="lib/models",
    schema_source="schema.schnitzel.yaml"
)

print(f"Generated: {output_path}")
```

## Complete Import Structure

The generated Dart file includes proper imports and part directives:

```dart
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:json_annotation/json_annotation.dart';

part 'models.freezed.dart';
part 'models.g.dart';

// Your models here...
```

## Running Tests

```bash
# Run all F033 tests
.venv/bin/python -m pytest tests/integration/test_dart_optional_fields_f033.py -v

# Run specific test
.venv/bin/python -m pytest tests/integration/test_dart_optional_fields_f033.py::test_mixed_required_and_optional_fields -v

# Run verification script
.venv/bin/python verify_f033.py
```
