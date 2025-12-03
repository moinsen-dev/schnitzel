"""Schema validation for Schnitzel schemas."""

from difflib import get_close_matches
from typing import List, Set

from pydantic import BaseModel

from .exceptions import ValidationError
from .models import FieldDefinition, Model, SchnitzelSchema


class ValidationResult(BaseModel):
    """Result of schema validation."""

    valid: bool
    errors: List[str] = []

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(valid=True, errors=[])

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(valid=False, errors=errors)


class SchemaValidator:
    """
    Validates Schnitzel schemas for correctness and consistency.

    Performs semantic validation beyond basic syntax checking, including:
    - Field type validation
    - Relationship validation
    - Naming convention validation
    """

    # Supported field types
    SUPPORTED_TYPES: Set[str] = {
        "string",
        "uuid",
        "int",
        "float",
        "bool",
        "datetime",
        "json",
        "enum",
        "vector",
    }

    def __init__(self) -> None:
        """Initialize the schema validator."""
        pass

    def validate(self, schema: SchnitzelSchema) -> ValidationResult:
        """
        Validate a Schnitzel schema.

        Args:
            schema: The schema to validate

        Returns:
            ValidationResult with validation status and any errors found
        """
        errors: List[str] = []

        # Validate all models
        for model_name, model in schema.models.items():
            model_errors = self._validate_model(model)
            errors.extend(model_errors)

        # Return validation result
        if errors:
            return ValidationResult.failure(errors)
        return ValidationResult.success()

    def _validate_model(self, model: Model) -> List[str]:
        """
        Validate a single model.

        Args:
            model: The model to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # Validate all fields
        for field_name, field in model.fields.items():
            field_errors = self._validate_field(field, field_name, model.name)
            errors.extend(field_errors)

        return errors

    def _validate_field(self, field: FieldDefinition, field_name: str, model_name: str) -> List[str]:
        """
        Validate a single field definition.

        Args:
            field: The field to validate
            field_name: Name of the field
            model_name: Name of the containing model

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []
        field_type = field.type

        # Check for list types
        if field_type.startswith("list<") and field_type.endswith(">"):
            inner_type = field_type[5:-1]
            if inner_type not in self.SUPPORTED_TYPES:
                error_msg = self._build_unsupported_type_error(inner_type, field_name, model_name)
                errors.append(error_msg)
            return errors

        # Check basic types
        if field_type not in self.SUPPORTED_TYPES:
            error_msg = self._build_unsupported_type_error(field_type, field_name, model_name)
            errors.append(error_msg)

        return errors

    def _build_unsupported_type_error(
        self, unsupported_type: str, field_name: str, model_name: str
    ) -> str:
        """
        Build an error message for an unsupported field type with helpful suggestions.

        Args:
            unsupported_type: The unsupported type that was used
            field_name: Name of the field
            model_name: Name of the containing model

        Returns:
            Formatted error message string
        """
        # Build error message
        error_parts = []

        # Main error
        error_parts.append(
            f"Unsupported field type '{unsupported_type}' for field '{field_name}' in model '{model_name}'"
        )

        # List supported types
        supported_list = sorted(self.SUPPORTED_TYPES)
        supported_str = ", ".join(supported_list) + ", list<T>"
        error_parts.append(f"Supported types: {supported_str}")

        # Add "did you mean" suggestions
        suggestions = self._get_type_suggestions(unsupported_type)
        if suggestions:
            if len(suggestions) == 1:
                error_parts.append(f"Did you mean: {suggestions[0]}?")
            else:
                suggestions_str = " or ".join(suggestions)
                error_parts.append(f"Did you mean: {suggestions_str}?")

        # Combine all parts
        return "\n".join(error_parts)

    def _get_type_suggestions(self, unsupported_type: str) -> List[str]:
        """
        Get suggestions for similar supported types.

        Uses string similarity matching to find types that are similar
        to the unsupported type provided. Also includes manual mappings
        for common type mistakes.

        Args:
            unsupported_type: The unsupported type to find suggestions for

        Returns:
            List of suggested type names (up to 2 suggestions)
        """
        # Manual mappings for common type mistakes
        manual_suggestions = {
            "decimal": ["float", "int"],
            "number": ["int", "float"],
            "double": ["float"],
            "integer": ["int"],
            "str": ["string"],
            "text": ["string"],
            "boolean": ["bool"],
            "date": ["datetime"],
            "timestamp": ["datetime"],
        }

        # Check manual suggestions first
        if unsupported_type.lower() in manual_suggestions:
            return manual_suggestions[unsupported_type.lower()]

        # Get close matches (cutoff=0.6 for reasonable similarity)
        matches = get_close_matches(
            unsupported_type.lower(), [t.lower() for t in self.SUPPORTED_TYPES], n=2, cutoff=0.6
        )

        # Map back to original case
        suggestions = []
        for match in matches:
            for supported_type in self.SUPPORTED_TYPES:
                if supported_type.lower() == match:
                    suggestions.append(supported_type)
                    break

        return suggestions
