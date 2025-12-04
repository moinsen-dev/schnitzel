"""Dart Freezed model generator for Schnitzel schemas.

Generates Dart Freezed models with JSON serialization support using json_serializable.
"""

from datetime import datetime
from pathlib import Path
from typing import Set
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation, DART_TYPE_MAP


class DartModelGenerator:
    """Generates Dart Freezed models from Schnitzel schemas."""

    def __init__(self):
        """Initialize the Dart model generator."""
        self.imports: Set[str] = set()
        self.part_directives: Set[str] = set()

    def _format_default_dart(self, value) -> str:
        """Format a default value with proper quoting for Dart code.

        Args:
            value: The default value to format

        Returns:
            Formatted string representation for Dart @Default() annotation

        Rules:
            - Strings: Use single quotes ('active')
            - Numbers: No quotes (0, 9.99)
            - Booleans: No quotes (true, false) - lowercase in Dart
            - Lists: Format as Dart list literal ([]) or (['a', 'b'])
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            # Boolean check must come before int (bool is subclass of int)
            # Dart uses lowercase true/false
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Use single quotes and escape quotes/backslashes
            escaped = value.replace('\\', '\\\\').replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(value, list):
            # Format list items
            if not value:
                return "[]"
            formatted_items = [self._format_default_dart(item) for item in value]
            return f"[{', '.join(formatted_items)}]"
        elif isinstance(value, dict):
            # Format dict/map - for now return empty map
            return "{}"
        else:
            # For other complex types, use string representation
            return repr(value)

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase or camelCase to snake_case.

        Args:
            name: The field name to convert

        Returns:
            snake_case version of the name

        Examples:
            userId -> user_id
            createdAt -> created_at
            userName -> user_name
        """
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                # Add underscore before uppercase letter
                result.append('_')
                result.append(char.lower())
            else:
                result.append(char.lower())
        return ''.join(result)

    def _needs_json_key(self, field_name: str) -> bool:
        """Check if a field needs @JsonKey annotation.

        A field needs @JsonKey if its snake_case version differs from the original.

        Args:
            field_name: The field name to check

        Returns:
            True if @JsonKey annotation is needed
        """
        snake_case = self._to_snake_case(field_name)
        return snake_case != field_name

    def generate(self, schema: SchnitzelSchema) -> str:
        """
        Generate Dart Freezed models from a schema.

        Args:
            schema: The Schnitzel schema to generate models from

        Returns:
            Generated Dart code as a string
        """
        self.imports = set()
        self.part_directives = set()

        # Add base imports for Freezed and JSON serialization
        self.imports.add("import 'package:freezed_annotation/freezed_annotation.dart';")
        self.imports.add("import 'package:json_annotation/json_annotation.dart';")

        # Add part directives for models.dart (used for multi-model files)
        self.part_directives.add("part 'models.freezed.dart';")
        self.part_directives.add("part 'models.g.dart';")

        # Generate model classes first to determine what we need to import
        model_code_sections = []
        for model_name, model in schema.models.items():
            model_code = self._generate_model(model)
            model_code_sections.append(model_code)

        # Collect additional imports based on field types
        self._collect_type_imports(schema)

        # Build final code with proper import ordering
        imports_code = "\n".join(sorted(self.imports))
        part_code = "\n".join(sorted(self.part_directives))
        models_code = "\n\n".join(model_code_sections)

        return f"{imports_code}\n\n{part_code}\n\n{models_code}\n"

    def generate_to_file(self, schema: SchnitzelSchema, output_dir: str | Path, schema_source: str = "schema.schnitzel.yaml", dry_run: bool = False) -> tuple[Path, int]:
        """
        Generate Dart Freezed models and write them to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the models to 'models.dart' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate models from
            output_dir: Directory where models.dart should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to models.dart file, size in bytes)

        Example:
            >>> generator = DartModelGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "lib/models")
            >>> print(f"Models written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the model code
        models_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        # Combine header with generated code
        full_code = header + models_code

        # Calculate file path and size
        models_file = output_path / "models.dart"
        file_size = len(full_code.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return models_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Warn if file already exists
        if models_file.exists():
            print(f"Warning: Overwriting existing file: {models_file}")

        models_file.write_text(full_code, encoding="utf-8")

        return models_file, file_size

    def _generate_model(self, model: Model) -> str:
        """Generate a single Freezed model class."""
        lines = []

        # Add documentation comment if model has a description
        if model.description:
            lines.append(f"/// {model.description}")

        lines.extend(["@freezed", f"class {model.name} with _${model.name} {{"])

        # Add factory constructor
        factory_params = []

        # Generate fields
        if model.fields:
            for field_name, field_def in model.fields.items():
                field_line = self._generate_field(field_name, field_def)
                # Handle multi-line field definitions (with doc comments)
                if "\n" in field_line:
                    # Indent each line with 4 spaces
                    indented_lines = [f"    {line}" for line in field_line.split("\n")]
                    factory_params.extend(indented_lines)
                else:
                    factory_params.append(f"    {field_line}")

        # Generate relationship fields
        if model.relations:
            for relation_name, relation_def in model.relations.items():
                relation_line = self._generate_relationship_field(relation_name, relation_def)
                if relation_line:
                    factory_params.append(f"    {relation_line}")

        # Build factory constructor
        if factory_params:
            lines.append(f"  const factory {model.name}({{")
            lines.extend(factory_params)
            lines.append(f"  }}) = _{model.name};")
        else:
            lines.append(f"  const factory {model.name}() = _{model.name};")

        # Add fromJson factory
        lines.append("")
        lines.append(f"  factory {model.name}.fromJson(Map<String, dynamic> json) => _${model.name}FromJson(json);")
        lines.append("}")

        return "\n".join(lines)

    def _generate_relationship_field(self, relation_name: str, relation_def: Relation) -> str:
        """Generate a relationship field definition.

        Args:
            relation_name: Name of the relationship field
            relation_def: Relation definition from schema

        Returns:
            Field definition string or empty string if not supported

        Supported relationships:
            - belongsTo: generates Model? field (nullable)
            - hasMany: generates List<Model> field
            - hasOne: generates Model? field (nullable)
        """
        # Handle belongsTo relationship
        if relation_def.type == "belongsTo":
            json_key = ""
            if self._needs_json_key(relation_name):
                snake_name = self._to_snake_case(relation_name)
                json_key = f"@JsonKey(name: '{snake_name}') "
            return f"{json_key}{relation_def.model}? {relation_name},"

        # Handle hasMany relationship
        if relation_def.type == "hasMany":
            json_key = ""
            if self._needs_json_key(relation_name):
                snake_name = self._to_snake_case(relation_name)
                json_key = f"@JsonKey(name: '{snake_name}') "
            return f"{json_key}List<{relation_def.model}>? {relation_name},"

        # Handle hasOne relationship
        if relation_def.type == "hasOne":
            json_key = ""
            if self._needs_json_key(relation_name):
                snake_name = self._to_snake_case(relation_name)
                json_key = f"@JsonKey(name: '{snake_name}') "
            return f"{json_key}{relation_def.model}? {relation_name},"

        return ""

    def _generate_field(self, field_name: str, field_def: FieldDefinition) -> str:
        """Generate a single field definition with type and JSON annotation.

        Args:
            field_name: Name of the field
            field_def: Field definition from schema

        Returns:
            Dart field declaration with @JsonKey and @Default if needed.
            If the field has a description, returns multi-line string with doc comment.
        """
        # Build the field lines list to support multi-line output
        field_lines = []

        # Add documentation comment if field has a description
        if field_def.description:
            field_lines.append(f"/// {field_def.description}")

        # Get Dart type
        dart_type = self._get_dart_type_for_field(field_def)

        # Handle optional fields (only if no default is provided)
        if field_def.optional and field_def.default is None:
            dart_type = f"{dart_type}?"

        # Build annotations
        annotations = []

        # Check if we need @JsonKey annotation for snake_case
        if self._needs_json_key(field_name):
            snake_name = self._to_snake_case(field_name)
            annotations.append(f"@JsonKey(name: '{snake_name}')")

        # Add @Default annotation if there's a default value
        if field_def.default is not None:
            default_value = self._format_default_dart(field_def.default)
            annotations.append(f"@Default({default_value})")

        # Join annotations with space
        annotation_str = " ".join(annotations)
        if annotation_str:
            annotation_str += " "

        # Build required keyword
        # Field is required if it's not optional and has no default value
        required_keyword = ""
        if not field_def.optional and field_def.default is None:
            required_keyword = "required "

        # Build the field declaration
        field_declaration = f"{annotation_str}{required_keyword}{dart_type} {field_name},"
        field_lines.append(field_declaration)

        # Return single-line or multi-line depending on whether we have doc comments
        return "\n".join(field_lines)

    def _get_dart_type_for_field(self, field_def: FieldDefinition) -> str:
        """
        Get Dart type for a field, handling enum types.

        Args:
            field_def: Field definition

        Returns:
            Dart type string
        """
        schema_type_lower = field_def.type.lower()

        # Handle enum types - in Dart, we typically use String for enums
        # unless we have a custom enum class
        if schema_type_lower == "enum":
            return "String"

        # Use standard type mapping
        return self._get_dart_type(field_def.type)

    def _get_dart_type(self, schema_type: str) -> str:
        """
        Map schema type to Dart type.

        Supports:
        - Basic types: string -> String, int -> int, uuid -> String, etc.
        - List types: list<string> -> List<String>
        - Vector types: vector -> List<double>
        - JSON type: json -> Map<String, dynamic>
        """
        schema_type_lower = schema_type.lower()

        # Handle list types: list<string> -> List<String>
        if schema_type_lower.startswith("list<") and schema_type_lower.endswith(">"):
            inner_type = schema_type_lower[5:-1].strip()
            inner_dart_type = DART_TYPE_MAP.get(inner_type, inner_type.capitalize())
            return f"List<{inner_dart_type}>"

        # Handle vector types: vector -> List<double>
        if schema_type_lower == "vector":
            return "List<double>"

        # Handle standard types
        return DART_TYPE_MAP.get(schema_type, schema_type)

    def _collect_type_imports(self, schema: SchnitzelSchema) -> None:
        """Collect necessary imports based on field types used.

        Note: Dart doesn't need explicit imports for basic types like String, int, etc.
        DateTime is part of dart:core, so no import needed.
        """
        # Currently, Freezed models don't need additional imports for basic types
        # This method is kept for future extensibility (e.g., custom types)
        pass
