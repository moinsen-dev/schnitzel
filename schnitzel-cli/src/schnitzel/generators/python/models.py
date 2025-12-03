"""Python Pydantic model generator for Schnitzel schemas.

Generates Pydantic v2 models with modern syntax (| None instead of Optional).
"""

from typing import Set
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, PYTHON_TYPE_MAP


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
        
        # Always include base imports
        self.imports.add("from pydantic import BaseModel, Field")
        
        # Generate model classes
        model_code_sections = []
        for model_name, model in schema.models.items():
            model_code = self._generate_model(model)
            model_code_sections.append(model_code)
        
        # Collect additional imports based on field types
        self._collect_type_imports(schema)
        
        # Build final code
        imports_code = "\n".join(sorted(self.imports))
        models_code = "\n\n".join(model_code_sections)
        
        return f"{imports_code}\n\n\n{models_code}\n"

    def _generate_model(self, model: Model) -> str:
        """Generate a single Pydantic model class."""
        lines = [f"class {model.name}(BaseModel):"]
        
        # Add docstring if description exists
        if model.description:
            lines.append(f'    """{model.description}"""')
            lines.append("")
        
        # Generate fields
        if not model.fields:
            lines.append("    pass")
        else:
            for field_name, field_def in model.fields.items():
                field_line = self._generate_field(field_name, field_def)
                lines.append(f"    {field_line}")
        
        return "\n".join(lines)

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
