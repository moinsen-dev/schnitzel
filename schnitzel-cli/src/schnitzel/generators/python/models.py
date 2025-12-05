"""Python Pydantic model generator for Schnitzel schemas.

Generates Pydantic v2 models with modern syntax (| None instead of Optional).
"""

from datetime import datetime
from pathlib import Path
from typing import Set
from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation, PYTHON_TYPE_MAP


class PythonModelGenerator:
    """Generates Pydantic v2 models from Schnitzel schemas."""

    def __init__(self):
        """Initialize the Python model generator."""
        self.imports: Set[str] = set()

    def _format_default(self, value) -> str:
        """Format a default value with proper quoting for Python code.

        Args:
            value: The default value to format

        Returns:
            Formatted string representation

        Rules:
            - Strings: Use double quotes ("active")
            - Numbers: No quotes (0, 9.99)
            - Booleans: No quotes (True, False)
            - None: No quotes (None)
        """
        if value is None:
            return "None"
        elif isinstance(value, bool):
            # Boolean check must come before int (bool is subclass of int)
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Use double quotes and escape quotes/backslashes
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        else:
            # For complex types (dict, list), use repr
            return repr(value)

    def generate(self, schema: SchnitzelSchema) -> str:
        """
        Generate Python Pydantic models from a schema.

        Args:
            schema: The Schnitzel schema to generate models from

        Returns:
            Generated Python code as a string
        """
        self.imports = set()

        # Track if we need Field import
        self.needs_field_import = False

        # Track if we need forward references
        self.needs_future_annotations = self._has_relationships(schema)

        # Check if any endpoints use pagination
        needs_pagination_model = self._check_pagination_needed(schema)

        # Generate model classes first to determine what we need to import
        model_code_sections = []
        for model_name, model in schema.models.items():
            model_code = self._generate_model(model)
            model_code_sections.append(model_code)

        # Add PaginatedResponse utility model if needed
        if needs_pagination_model:
            pagination_model = self._generate_paginated_response_model()
            model_code_sections.append(pagination_model)
            # PaginatedResponse needs Generic and TypeVar
            self.imports.add("from typing import Generic, TypeVar")
            # Need Field for pagination metadata
            self.needs_field_import = True

        # Collect additional imports based on field types
        self._collect_type_imports(schema)

        # Add base imports
        # Only add __future__ annotations when we have forward references (relationships)
        if self.needs_future_annotations:
            self.imports.add("from __future__ import annotations")

        # Always need BaseModel
        if self.needs_field_import:
            self.imports.add("from pydantic import BaseModel, Field")
        else:
            self.imports.add("from pydantic import BaseModel")

        # Build final code with proper import ordering
        # __future__ imports must come first
        future_imports = [imp for imp in self.imports if imp.startswith("from __future__")]
        other_imports = [imp for imp in self.imports if not imp.startswith("from __future__")]

        imports_code = "\n".join(sorted(future_imports)) + "\n\n" + "\n".join(sorted(other_imports))
        models_code = "\n\n".join(model_code_sections)

        return f"{imports_code}\n\n\n{models_code}\n"

    def generate_to_file(self, schema: SchnitzelSchema, output_dir: str | Path, schema_source: str = "schema.schnitzel.yaml", dry_run: bool = False) -> tuple[Path, int]:
        """
        Generate Python Pydantic models and write them to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the models to 'models.py' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate models from
            output_dir: Directory where models.py should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to models.py file, size in bytes)

        Example:
            >>> generator = PythonModelGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "backend/app/generated")
            >>> print(f"Models written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the model code
        models_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""# Generated by Schnitzel Framework v{__version__}
# DO NOT EDIT - This file is auto-generated
# Generated at: {timestamp}
# Source: {schema_source}

"""

        # Combine header with generated code
        full_code = header + models_code

        # Calculate file path and size
        models_file = output_path / "models.py"
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
        """Generate a single Pydantic model class."""
        lines = [f"class {model.name}(BaseModel):"]

        # Add docstring if description exists
        if model.description:
            lines.append(f'    """{model.description}"""')
            lines.append("")

        # Generate fields
        has_content = False
        if model.fields:
            lines.append("    # Fields")
            for field_name, field_def in model.fields.items():
                field_line = self._generate_field(field_name, field_def)
                lines.append(f"    {field_line}")
            has_content = True

        # Generate relationship fields
        if model.relations:
            if has_content:
                lines.append("")
            lines.append("    # Relationships")
            for relation_name, relation_def in model.relations.items():
                relation_line = self._generate_relationship_field(relation_name, relation_def)
                if relation_line:
                    lines.append(f"    {relation_line}")
                    has_content = True

        # If no fields or relations, add pass
        if not has_content:
            lines.append("    pass")

        return "\n".join(lines)

    def _generate_relationship_field(self, relation_name: str, relation_def) -> str:
        """Generate a relationship field definition.

        Args:
            relation_name: Name of the relationship field
            relation_def: Relation definition from schema

        Returns:
            Field definition string or empty string if not supported

        Supported relationships:
            - belongsTo: generates Model | None = None (forward reference)
            - hasMany: generates list[Model] = [] with type: ignore for mutable default
            - hasOne: not generated yet (future enhancement)

        Note: With __future__ annotations, we don't need to quote forward references.
        """
        # Handle belongsTo relationship
        if relation_def.type == "belongsTo":
            # Forward reference without quotes (using __future__ annotations)
            # Use Pydantic v2 union syntax (| None instead of Optional)
            # Default to None since relationship is optional
            return f'{relation_name}: {relation_def.model} | None = None'

        # Handle hasMany relationship
        if relation_def.type == "hasMany":
            # Forward reference without quotes (using __future__ annotations)
            # Use built-in list[] not typing.List[]
            # Default to empty list []
            # Add type: ignore because mutable default [] can trigger type checker warnings
            return f'{relation_name}: list[{relation_def.model}] = []  # type: ignore[assignment]'

        # hasOne and other types not yet implemented
        return ""

    def _generate_field(self, field_name: str, field_def: FieldDefinition) -> str:
        """Generate a single field definition with type and validation.

        Uses Pydantic v2 syntax: 'str | None' instead of 'Optional[str]'.
        """
        # Get Python type (handles enums with Literal specially)
        python_type = self._get_python_type_for_field(field_def)

        # Handle optional fields with Pydantic v2 syntax (| None)
        if field_def.optional:
            python_type = f"{python_type} | None"

        # Build Field() constraints
        field_constraints = self._build_field_constraints(field_def)

        # Generate field line
        if field_constraints:
            self.needs_field_import = True
            field_value = f"Field({field_constraints})"
        elif field_def.default is not None:
            field_value = self._format_default(field_def.default)
        elif field_def.optional:
            field_value = "None"
        else:
            # Required field with no constraints
            return f"{field_name}: {python_type}"

        return f"{field_name}: {python_type} = {field_value}"

    def _get_python_type_for_field(self, field_def: FieldDefinition) -> str:
        """
        Get Python type for a field, handling enum types with Literal.

        Args:
            field_def: Field definition

        Returns:
            Python type string
        """
        schema_type_lower = field_def.type.lower()

        # Handle enum types with Literal
        if schema_type_lower == "enum" and field_def.values:
            # Generate Literal type from enum values
            values_str = ", ".join(f'"{v}"' for v in field_def.values)
            return f"Literal[{values_str}]"

        # Use standard type mapping
        return self._get_python_type(field_def.type)

    def _build_field_constraints(self, field_def: FieldDefinition) -> str:
        """Build Field() constraint parameters.

        Returns empty string if only default is needed (uses simple = syntax instead).
        """
        constraints = []

        # Numeric constraints: min/max -> ge/le
        if field_def.min is not None:
            constraints.append(f"ge={field_def.min}")

        if field_def.max is not None:
            constraints.append(f"le={field_def.max}")

        # String length constraint
        if field_def.max_length is not None:
            constraints.append(f"max_length={field_def.max_length}")

        # Only add default to Field() if there are other constraints
        if constraints:
            if field_def.default is not None:
                constraints.append(f"default={self._format_default(field_def.default)}")
            elif field_def.optional:
                constraints.append("default=None")

        return ", ".join(constraints)

    def _get_python_type(self, schema_type: str) -> str:
        """
        Map schema type to Python type.

        Supports:
        - Basic types: string -> str, int -> int, uuid -> UUID, etc.
        - List types: list<string> -> list[str]
        - Enum types: enum -> Literal[...] (requires field.values)
        - Vector types: vector -> list[float]
        - JSON type: json -> dict[str, Any]
        """
        schema_type_lower = schema_type.lower()

        # Handle list types: list<string> -> list[str]
        if schema_type_lower.startswith("list<") and schema_type_lower.endswith(">"):
            inner_type = schema_type_lower[5:-1].strip()
            inner_python_type = PYTHON_TYPE_MAP.get(inner_type, inner_type)
            return f"list[{inner_python_type}]"

        # Handle enum types (note: requires field.values in field_def)
        if schema_type_lower == "enum":
            # This will be handled in _generate_field with field_def.values
            return "str"  # Default fallback

        # Handle vector types: vector -> list[float]
        if schema_type_lower == "vector":
            return "list[float]"

        # Handle standard types
        return PYTHON_TYPE_MAP.get(schema_type, schema_type)

    def _has_relationships(self, schema: SchnitzelSchema) -> bool:
        """Check if schema has any relationships that need forward references.

        Returns True if any model has relations defined (belongsTo, hasMany, hasOne).
        This determines whether we need `from __future__ import annotations`.
        """
        for model in schema.models.values():
            if model.relations:
                return True
        return False

    def _collect_type_imports(self, schema: SchnitzelSchema) -> None:
        """Collect necessary imports based on field types used.

        Note: Does NOT import Optional since we use Pydantic v2 '| None' syntax.
        """
        needs_uuid = False
        needs_datetime = False
        needs_any = False
        needs_literal = False

        for model in schema.models.values():
            for field_def in model.fields.values():
                field_type_lower = field_def.type.lower()

                # Check for UUID type (including in list<uuid>)
                if "uuid" in field_type_lower:
                    needs_uuid = True

                # Check for datetime type (including in list<datetime>)
                if "datetime" in field_type_lower:
                    needs_datetime = True

                # Check for json type (needs Any for dict[str, Any])
                if field_type_lower == "json":
                    needs_any = True

                # Check for enum type (needs Literal)
                if field_type_lower == "enum" and field_def.values:
                    needs_literal = True

        # Add imports (no Optional import - we use | None syntax)
        if needs_uuid:
            self.imports.add("from uuid import UUID")

        if needs_datetime:
            self.imports.add("from datetime import datetime")

        if needs_any:
            self.imports.add("from typing import Any")

        if needs_literal:
            self.imports.add("from typing import Literal")

    def _check_pagination_needed(self, schema: SchnitzelSchema) -> bool:
        """Check if any endpoint has pagination enabled.

        Returns True if pagination: true is set on any endpoint,
        or if any response type is PaginatedResponse<T>.
        """
        if not schema.endpoints:
            return False

        for path, methods in schema.endpoints.items():
            if not isinstance(methods, dict):
                continue

            for method_name, endpoint_def in methods.items():
                if method_name == "params":
                    continue

                if not isinstance(endpoint_def, dict):
                    continue

                # Check if pagination is explicitly enabled
                if endpoint_def.get("pagination", False):
                    return True

                # Check if response type is PaginatedResponse<T>
                if "response" in endpoint_def:
                    responses = endpoint_def["response"]
                    for status_code, response_def in responses.items():
                        if isinstance(response_def, dict) and "type" in response_def:
                            response_type = response_def["type"]
                            if "PaginatedResponse<" in response_type:
                                return True

        return False

    def _generate_paginated_response_model(self) -> str:
        """Generate the PaginatedResponse generic model for paginated endpoints.

        Returns a Pydantic model that wraps paginated results with metadata:
        - items: List[T] - The actual items
        - total: int - Total number of items across all pages
        - page: int - Current page number (1-indexed)
        - per_page: int - Items per page
        - pages: int - Total number of pages
        """
        return """# Generic type variable for PaginatedResponse
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    \"\"\"Generic paginated response wrapper.

    Provides pagination metadata along with the actual items.
    \"\"\"

    items: list[T] = Field(description="Items for the current page")
    total: int = Field(ge=0, description="Total number of items across all pages")
    page: int = Field(ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(ge=1, description="Number of items per page")
    pages: int = Field(ge=0, description="Total number of pages")"""
