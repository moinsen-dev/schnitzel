"""Dart test factory generator for Schnitzel schemas.

Generates test factories using faker for realistic fake data generation.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict
from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition


class DartTestFactoryGenerator:
    """Generates Dart test factories from Schnitzel schemas."""

    def __init__(self):
        """Initialize the Dart test factory generator."""
        pass

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case.

        Args:
            name: The name to convert

        Returns:
            snake_case version of the name

        Examples:
            UserFactory -> user_factory
            BlogPost -> blog_post
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

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to lowerCamelCase.

        Args:
            name: The field name to convert (may be snake_case)

        Returns:
            lowerCamelCase version of the name

        Examples:
            user_id -> userId
            created_at -> createdAt
            email -> email
        """
        # If no underscores, already camelCase or single word
        if '_' not in name:
            return name

        # Split by underscore and capitalize each part except the first
        parts = name.split('_')
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])

    def _get_faker_expression(self, field_name: str, field_def: FieldDefinition) -> str:
        """Get the appropriate faker expression for a field.

        Args:
            field_name: Name of the field
            field_def: Field definition from schema

        Returns:
            Dart faker expression as string

        Field type mappings (using faker package):
            - uuid/string(primary): _faker.guid.guid()
            - string: _faker.lorem.word() or context-specific
            - string(email): _faker.internet.email()
            - string(name): _faker.person.name()
            - int: _faker.randomGenerator.integer(1000)
            - double/float: _faker.randomGenerator.decimal(min: 0, scale: 100)
            - bool: _faker.randomGenerator.boolean()
            - datetime: DateTime.now()
            - text: _faker.lorem.sentence()
        """
        field_type = field_def.type.lower()
        field_name_lower = field_name.lower()

        # UUID or primary key string
        if field_type == "uuid" or (field_type in ["string", "str"] and field_def.primary):
            return "_faker.guid.guid()"

        # String types - context-aware
        if field_type in ["string", "str"]:
            # Email field
            if "email" in field_name_lower:
                return "_faker.internet.email()"
            # Name fields
            elif "name" in field_name_lower:
                if "first" in field_name_lower:
                    return "_faker.person.firstName()"
                elif "last" in field_name_lower:
                    return "_faker.person.lastName()"
                else:
                    return "_faker.person.name()"
            # Username
            elif "username" in field_name_lower or "user_name" in field_name_lower:
                return "_faker.internet.userName()"
            # Phone
            elif "phone" in field_name_lower:
                return "_faker.phoneNumber.us()"
            # Address-related
            elif "address" in field_name_lower:
                return "_faker.address.streetAddress()"
            elif "city" in field_name_lower:
                return "_faker.address.city()"
            elif "country" in field_name_lower:
                return "_faker.address.country()"
            # URL
            elif "url" in field_name_lower:
                return "_faker.internet.httpsUrl()"
            # Default string
            else:
                return "_faker.lorem.word()"

        # Text (long string)
        if field_type == "text":
            return "_faker.lorem.sentence()"

        # Integer
        if field_type in ["int", "integer"]:
            return "_faker.randomGenerator.integer(1000)"

        # Float/Double
        if field_type in ["float", "double", "decimal"]:
            return "_faker.randomGenerator.decimal(min: 0, scale: 100)"

        # Boolean
        if field_type in ["bool", "boolean"]:
            return "_faker.randomGenerator.boolean()"

        # DateTime/Date
        if field_type in ["datetime", "date"]:
            return "DateTime.now()"

        # JSON
        if field_type == "json":
            return "{}"

        # List
        if field_type.startswith("list"):
            return "[]"

        # Vector
        if field_type == "vector":
            return "[]"

        # Default fallback
        return "_faker.lorem.word()"

    def _get_dart_type(self, field_def: FieldDefinition) -> str:
        """Get the Dart type for a field.

        Args:
            field_def: Field definition from schema

        Returns:
            Dart type as string
        """
        from schnitzel.schema.models import DART_TYPE_MAP

        field_type = field_def.type.lower()

        # Handle list types
        if field_type.startswith("list<") and field_type.endswith(">"):
            inner_type = field_type[5:-1].strip()
            inner_dart_type = DART_TYPE_MAP.get(inner_type, inner_type.capitalize())
            return f"List<{inner_dart_type}>"

        # Handle vector types
        if field_type == "vector":
            return "List<double>"

        # Standard type mapping
        dart_type = DART_TYPE_MAP.get(field_type, field_def.type)

        # Make nullable if optional
        if field_def.optional:
            dart_type = f"{dart_type}?"

        return dart_type

    def generate(self, schema: SchnitzelSchema) -> Dict[str, str]:
        """Generate test factory files for all CRUD models in the schema.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dictionary mapping file names to their content:
            {
                "factories.dart": "...",
            }
        """
        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
        shared_package = f"{package_name}_shared"

        # Filter models that have CRUD enabled
        crud_models = {}
        for model_name, model in schema.models.items():
            if model.crud:
                crud_models[model_name] = model

        # Generate factory classes
        factory_classes = []
        for model_name, model in crud_models.items():
            factory_class = self._generate_factory_class(model_name, model)
            factory_classes.append(factory_class)

        # Build the complete file content
        factories_code = self._build_factories_file(shared_package, factory_classes)

        return {
            "factories.dart": factories_code
        }

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> Dict[Path, int]:
        """Generate test factory files and write them to disk.

        Creates the output directory if it doesn't exist and writes factories.dart.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where files should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Dictionary mapping Path objects to file sizes in bytes

        Example:
            >>> generator = DartTestFactoryGenerator()
            >>> files = generator.generate_to_file(schema, "test/factories")
            >>> for path, size in files.items():
            ...     print(f"{path.name}: {size} bytes")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the factory files
        files = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        # Write files and collect results
        result = {}
        for filename, content in files.items():
            full_code = header + content
            file_path = output_path / filename
            file_size = len(full_code.encode("utf-8"))

            # If dry-run, just record the info
            if dry_run:
                result[file_path] = file_size
                continue

            # Create directory if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)

            # Warn if file already exists
            if file_path.exists():
                print(f"Warning: Overwriting existing file: {file_path}")

            file_path.write_text(full_code, encoding="utf-8")
            result[file_path] = file_size

        return result

    def _build_factories_file(self, shared_package: str, factory_classes: list) -> str:
        """Build the complete factories.dart file with imports and all factory classes.

        Args:
            shared_package: Name of the shared package for model imports
            factory_classes: List of factory class code strings

        Returns:
            Complete Dart file content as string
        """
        imports = f"""import 'package:faker/faker.dart';
import 'package:{shared_package}/models/models.dart';
"""

        factories = "\n\n".join(factory_classes)

        return f"{imports}\n{factories}\n"

    def _generate_factory_class(self, model_name: str, model: Model) -> str:
        """Generate a factory class for a single model.

        Args:
            model_name: Name of the model (e.g., "User")
            model: Model definition from schema

        Returns:
            Dart factory class code

        Example output:
            class UserFactory {
              static final _faker = Faker();

              static User create({
                String? id,
                String? email,
                String? name,
                DateTime? createdAt,
              }) {
                return User(
                  id: id ?? _faker.datatype.uuid(),
                  email: email ?? _faker.internet.email(),
                  name: name ?? _faker.person.fullName(),
                  createdAt: createdAt ?? DateTime.now(),
                );
              }

              static List<User> createList(int count) {
                return List.generate(count, (_) => create());
              }
            }
        """
        lines = []

        # Add class documentation
        description = model.description or f"Test factory for {model_name} model"
        lines.append(f"/// {description}")
        lines.append("///")
        lines.append("/// Example usage:")
        lines.append(f"/// ```dart")
        lines.append(f"/// final {model_name.lower()} = {model_name}Factory.create();")
        lines.append(f"/// final custom = {model_name}Factory.create(")

        # Add example with first field override (if we have fields)
        if model.fields:
            first_field = list(model.fields.keys())[0]
            camel_field = self._to_camel_case(first_field)
            field_def = model.fields[first_field]

            # Generate example value based on type
            example_value = "'custom_value'"
            if field_def.type.lower() in ["int", "integer"]:
                example_value = "42"
            elif field_def.type.lower() in ["bool", "boolean"]:
                example_value = "true"
            elif field_def.type.lower() in ["datetime", "date"]:
                example_value = "DateTime(2024, 1, 1)"

            lines.append(f"///   {camel_field}: {example_value},")
            lines.append("/// );")
        else:
            lines.append("/// );")

        lines.append(f"/// final list = {model_name}Factory.createList(10);")
        lines.append("/// ```")
        lines.append(f"class {model_name}Factory {{")
        lines.append("  static final _faker = Faker();")
        lines.append("")

        # Generate create method
        lines.append(f"  static {model_name} create({{")

        # Generate method parameters
        param_lines = []
        for field_name, field_def in model.fields.items():
            dart_field_name = self._to_camel_case(field_name)
            dart_type = self._get_dart_type(field_def)

            # Make parameter nullable to allow overrides
            if not dart_type.endswith("?"):
                dart_type = f"{dart_type}?"

            param_lines.append(f"    {dart_type} {dart_field_name},")

        lines.extend(param_lines)
        lines.append("  }) {")

        # Generate return statement with model constructor
        lines.append(f"    return {model_name}(")

        # Generate field assignments
        for field_name, field_def in model.fields.items():
            dart_field_name = self._to_camel_case(field_name)
            faker_expr = self._get_faker_expression(field_name, field_def)
            lines.append(f"      {dart_field_name}: {dart_field_name} ?? {faker_expr},")

        lines.append("    );")
        lines.append("  }")
        lines.append("")

        # Generate createList method
        lines.append(f"  static List<{model_name}> createList(int count) {{")
        lines.append("    return List.generate(count, (_) => create());")
        lines.append("  }")
        lines.append("}")

        return "\n".join(lines)
