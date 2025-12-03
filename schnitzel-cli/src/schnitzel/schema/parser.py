"""Schema parser with import resolution for Schnitzel."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from .models import SchnitzelSchema
from .exceptions import YAMLParseError, CircularImportError, ImportError as SchnitzelImportError, ValidationError


class DuplicateModelError(Exception):
    """Raised when duplicate model names are found."""

    pass


class SchemaParser:
    """
    Parse Schnitzel YAML schemas with multi-level import resolution.

    Supports nested imports up to MAX_IMPORT_DEPTH levels deep.
    """

    MAX_IMPORT_DEPTH = 10  # Maximum import nesting depth to prevent infinite recursion

    def __init__(self) -> None:
        """Initialize the schema parser."""
        self._import_stack: list[Path] = []
        self._visited_files: set[Path] = set()  # Track parsed files to avoid re-parsing

    def parse(self, schema_path: str | Path) -> SchnitzelSchema:
        """
        Parse a Schnitzel schema file with import resolution.

        Args:
            schema_path: Path to the schema YAML file

        Returns:
            Parsed and validated SchnitzelSchema object

        Raises:
            YAMLParseError: If YAML syntax is invalid
            CircularImportError: If circular imports are detected
            DuplicateModelError: If duplicate model names exist
            FileNotFoundError: If schema file or imports don't exist
            ValidationError: If schema validation fails
        """
        schema_path = Path(schema_path).resolve()

        # Reset import stack and visited files for new parse operation
        self._import_stack = []
        self._visited_files = set()

        # Load and merge all imports
        yaml_data = self._load_with_imports(schema_path)

        # Validate and return schema
        try:
            return SchnitzelSchema(**yaml_data)
        except PydanticValidationError as e:
            # Re-raise as our custom ValidationError with detailed context
            raise self._format_validation_error(e, schema_path) from e

    def _format_validation_error(self, error: PydanticValidationError, schema_path: Path) -> ValidationError:
        """
        Format a Pydantic validation error with detailed context.

        Extracts information about which model/field failed validation and provides
        a human-readable error message explaining what went wrong and what was expected.

        Args:
            error: The Pydantic validation error
            schema_path: Path to the schema file being parsed

        Returns:
            ValidationError with formatted message
        """
        error_messages = []

        # Process each validation error from Pydantic
        for err in error.errors():
            # Extract location information (e.g., ('models', 'User', 'fields', 'id', 'type'))
            location = err.get('loc', ())
            error_type = err.get('type', 'unknown')
            msg = err.get('msg', 'Validation failed')
            input_value = err.get('input', None)

            # Parse location to identify model, field, and attribute
            model_name = None
            field_name = None
            attribute_name = None
            relation_name = None

            # Build context by walking through location tuple
            i = 0
            while i < len(location):
                part = location[i]

                if part == 'models' and i + 1 < len(location):
                    # Next part is the model name
                    model_name = location[i + 1]
                    i += 2
                elif part == 'fields' and i + 1 < len(location) and model_name:
                    # Next part is the field name
                    field_name = location[i + 1]
                    i += 2
                elif part == 'relations' and i + 1 < len(location) and model_name:
                    # Next part is the relation name
                    relation_name = location[i + 1]
                    i += 2
                elif isinstance(part, str) and i == len(location) - 1:
                    # Last part is usually the attribute name
                    attribute_name = part
                    i += 1
                else:
                    i += 1

            # Build human-readable location string
            location_parts = []
            if model_name:
                location_parts.append(f"model '{model_name}'")
            if relation_name:
                location_parts.append(f"relation '{relation_name}'")
            elif field_name:
                location_parts.append(f"field '{field_name}'")
            if attribute_name and attribute_name not in ('fields', 'models', 'relations'):
                location_parts.append(f"attribute '{attribute_name}'")

            location_str = " -> ".join(location_parts) if location_parts else "schema root"

            # Build detailed error message based on error type
            if error_type == 'missing':
                # Missing required field
                if attribute_name:
                    detail = f"Missing required attribute in {location_str}"
                    detail += f"\n      Required: '{attribute_name}' must be specified"
                    detail += f"\n      Hint: {msg}"
                else:
                    detail = f"Missing required field at {location_str}"
                    detail += f"\n      Expected: {msg}"
            elif error_type == 'value_error':
                # Custom validation error (e.g., invalid type, PascalCase violation)
                detail = f"Invalid value in {location_str}"
                detail += f"\n      Error: {msg}"
                if input_value is not None:
                    detail += f"\n      Got: {input_value!r}"
            elif error_type.startswith('literal_'):
                # Literal/enum validation errors
                detail = f"Invalid value in {location_str}"
                detail += f"\n      Error: {msg}"
                if input_value is not None:
                    detail += f"\n      Got: {input_value!r}"
            elif error_type.startswith('string_'):
                # String validation errors
                detail = f"Invalid string value in {location_str}"
                detail += f"\n      Error: {msg}"
                if input_value is not None:
                    detail += f"\n      Got: {input_value!r}"
            elif error_type.startswith('int_') or error_type.startswith('float_'):
                # Numeric validation errors
                detail = f"Invalid numeric value in {location_str}"
                detail += f"\n      Error: {msg}"
                if input_value is not None:
                    detail += f"\n      Got: {input_value!r}"
            elif error_type == 'model_type' or error_type.startswith('type_'):
                # Type mismatch errors
                detail = f"Type mismatch in {location_str}"
                detail += f"\n      Error: {msg}"
                if input_value is not None:
                    value_type = type(input_value).__name__
                    detail += f"\n      Got: {value_type}"
            else:
                # Generic validation error
                detail = f"Validation error in {location_str}"
                detail += f"\n      Error: {msg}"
                if input_value is not None:
                    detail += f"\n      Got: {input_value!r}"

            error_messages.append(f"  - {detail}")

        # Build final error message
        final_message = f"Schema validation failed for {schema_path.name}\n"
        final_message += f"\nValidation errors found:\n"
        final_message += "\n\n".join(error_messages)
        final_message += f"\n\nTip: Ensure all models have required fields and "
        final_message += "all field definitions have a 'type' attribute."

        return ValidationError(final_message)

    def _load_with_imports(self, schema_path: Path) -> dict[str, Any]:
        """
        Load YAML file and recursively resolve imports (multi-level support).

        This method handles multi-level nested imports by recursively processing
        each import and merging models from all levels. It includes:
        - Depth limit enforcement (MAX_IMPORT_DEPTH)
        - Circular import detection
        - File deduplication to avoid re-parsing
        - Model merging from all import levels

        Args:
            schema_path: Path to the YAML file to load

        Returns:
            Merged YAML data with all imports resolved

        Raises:
            SchnitzelImportError: If max depth exceeded
            CircularImportError: If circular import detected
            FileNotFoundError: If file doesn't exist
            YAMLParseError: If YAML is invalid
            DuplicateModelError: If duplicate models found
        """
        # Check import depth limit (F004 requirement)
        current_depth = len(self._import_stack)
        if current_depth >= self.MAX_IMPORT_DEPTH:
            chain_str = " -> ".join(p.name for p in self._import_stack)
            raise SchnitzelImportError(
                f"Import depth exceeded maximum of {self.MAX_IMPORT_DEPTH} levels.\n"
                f"  Import chain: {chain_str} -> {schema_path.name}\n"
                f"  This may indicate a circular import or overly complex import structure.",
                missing_file=str(schema_path),
                importing_file=str(self._import_stack[-1]) if self._import_stack else None
            )

        # Check for circular imports
        if schema_path in self._import_stack:
            # Build import chain with file names
            chain_names = [p.name for p in self._import_stack] + [schema_path.name]
            raise CircularImportError(chain_names)

        # Add to import stack
        self._import_stack.append(schema_path)

        # Mark file as visited
        self._visited_files.add(schema_path)

        try:
            # Load the current file
            yaml_data = self._load_yaml(schema_path)

            # Get imports list
            imports = yaml_data.get("imports", [])

            # If no imports, return as-is
            if not imports:
                return yaml_data

            # Resolve and merge all imports
            merged_models: dict[str, Any] = {}

            for import_path_str in imports:
                # Resolve path relative to current file
                import_path = (schema_path.parent / import_path_str).resolve()

                # Check if import file exists
                if not import_path.exists():
                    raise SchnitzelImportError(
                        f"Cannot resolve import: {import_path_str}",
                        missing_file=import_path_str,
                        importing_file=str(schema_path.name)
                    )

                # Recursively load imported file
                imported_data = self._load_with_imports(import_path)

                # Merge models from imported file
                imported_models = imported_data.get("models", {})
                for model_name, model_def in imported_models.items():
                    if model_name in merged_models:
                        raise DuplicateModelError(
                            f"Duplicate model '{model_name}' found in import chain"
                        )
                    merged_models[model_name] = model_def

            # Merge models from current file
            current_models = yaml_data.get("models", {})
            for model_name, model_def in current_models.items():
                if model_name in merged_models:
                    raise DuplicateModelError(
                        f"Duplicate model '{model_name}' found: "
                        f"defined in {schema_path.name} and imported files"
                    )
                merged_models[model_name] = model_def

            # Update yaml_data with merged models
            yaml_data["models"] = merged_models

            # Remove imports from final schema (already processed)
            yaml_data.pop("imports", None)

            return yaml_data

        finally:
            # Remove from import stack when done
            self._import_stack.pop()

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """
        Load and parse a YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            YAMLParseError: If YAML syntax is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Schema file not found: {file_path}")

        # Read file content for error reporting
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                file_lines = file_content.splitlines()
        except OSError as read_error:
            raise YAMLParseError(
                message=f"Failed to read file: {read_error}",
                filename=file_path.name,
            ) from read_error

        # Parse YAML with enhanced error handling
        try:
            data = yaml.safe_load(file_content)

            if data is None:
                return {}

            if not isinstance(data, dict):
                raise YAMLParseError(
                    message=f"expected YAML object, got {type(data).__name__}",
                    filename=file_path.name,
                )

            return data

        except yaml.YAMLError as e:
            # Extract error details from PyYAML exception
            line_num = None
            column_num = None
            line_content = None
            error_message = str(e)

            # PyYAML provides a Mark object with position information
            if hasattr(e, "problem_mark"):
                mark = e.problem_mark
                line_num = mark.line + 1  # Convert 0-indexed to 1-indexed
                column_num = mark.column + 1  # Convert 0-indexed to 1-indexed

                # Extract the problematic line content from file_lines
                if 0 <= mark.line < len(file_lines):
                    line_content = file_lines[mark.line].rstrip()

            # Extract the problem description for cleaner error message
            if hasattr(e, "problem"):
                error_message = e.problem
            elif hasattr(e, "context"):
                error_message = e.context

            raise YAMLParseError(
                message=error_message,
                line=line_num,
                column=column_num,
                line_content=line_content,
                filename=file_path.name,
            ) from e
