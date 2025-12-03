"""Schema validation for Schnitzel schemas."""

import re
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

        # Validate relationships across models
        relationship_errors = self._validate_relationships(schema)
        errors.extend(relationship_errors)

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

        # Validate model name follows PascalCase convention
        naming_error = self._validate_model_name(model.name)
        if naming_error:
            errors.append(naming_error)

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

        # Validate field name follows snake_case convention
        naming_error = self._validate_field_name(field_name, model_name)
        if naming_error:
            errors.append(naming_error)

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

    def _validate_model_name(self, model_name: str) -> str | None:
        """
        Validate that a model name follows PascalCase naming convention.

        Args:
            model_name: Name of the model to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not model_name:
            return "Model name cannot be empty"

        # Check if name is PascalCase
        if not self._is_pascal_case(model_name):
            # Build error message
            error_parts = []
            error_parts.append(f"Model name '{model_name}' violates naming convention")
            error_parts.append("Model names must be PascalCase")

            # Suggest correct name
            suggested_name = self._to_pascal_case(model_name)
            error_parts.append(f"Suggested name: '{suggested_name}'")

            return "\n".join(error_parts)

        return None

    def _validate_field_name(self, field_name: str, model_name: str) -> str | None:
        """
        Validate that a field name follows snake_case naming convention.

        Args:
            field_name: Name of the field to validate
            model_name: Name of the containing model

        Returns:
            Error message if invalid, None if valid
        """
        if not self._is_snake_case(field_name):
            suggested_name = self._to_snake_case(field_name)
            error_parts = [
                f"Field name '{field_name}' in model '{model_name}' violates naming convention",
                "Field names must be snake_case",
                f"Suggested name: '{suggested_name}'"
            ]
            return "\n".join(error_parts)
        return None

    def _is_snake_case(self, name: str) -> bool:
        """
        Check if a name follows snake_case convention.

        A valid snake_case name:
        - Contains only lowercase letters, digits, and underscores
        - Does not start or end with an underscore
        - Does not have consecutive underscores

        Args:
            name: The name to check

        Returns:
            True if the name is valid snake_case, False otherwise
        """
        if not name:
            return False

        # Check for valid snake_case pattern
        # Must contain only lowercase letters, digits, and underscores
        # Cannot start or end with underscore
        # Cannot have consecutive underscores
        pattern = r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
        return bool(re.match(pattern, name))

    def _to_snake_case(self, name: str) -> str:
        """
        Convert a name to snake_case.

        Handles conversion from:
        - camelCase -> snake_case
        - PascalCase -> snake_case
        - Already snake_case -> unchanged

        Args:
            name: The name to convert

        Returns:
            The name converted to snake_case
        """
        # Insert underscore before uppercase letters (for camelCase/PascalCase)
        # But not before consecutive uppercase letters (like "HTTPServer" -> "http_server")
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters that follow lowercase or digits
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Convert to lowercase
        return s2.lower()

    def _is_pascal_case(self, name: str) -> bool:
        """
        Check if a name follows PascalCase convention.

        PascalCase means:
        - First character is uppercase
        - No underscores or hyphens
        - Each word starts with an uppercase letter
        - Contains only alphanumeric characters

        Args:
            name: The name to check

        Returns:
            True if name is PascalCase, False otherwise
        """
        if not name:
            return False

        # Must start with uppercase letter
        if not name[0].isupper():
            return False

        # Must not contain underscores or hyphens
        if "_" in name or "-" in name:
            return False

        # Must contain only alphanumeric characters
        if not name.isalnum():
            return False

        return True

    def _to_pascal_case(self, name: str) -> str:
        """
        Convert a name to PascalCase.

        Handles conversion from:
        - snake_case (user_profile -> UserProfile)
        - kebab-case (user-profile -> UserProfile)
        - camelCase (userProfile -> UserProfile)
        - space separated (user profile -> UserProfile)
        - ALL_CAPS (API_KEY -> ApiKey)

        Args:
            name: The name to convert

        Returns:
            PascalCase version of the name
        """
        if not name:
            return ""

        # Split on underscores, hyphens, or spaces
        words = re.split(r"[_\-\s]+", name)

        # Also handle camelCase by splitting on uppercase letters
        all_words = []
        for word in words:
            if not word:
                continue
            # Split camelCase words (but not ALL_CAPS words)
            if word.isupper() and len(word) > 1:
                # For ALL_CAPS words, just add as-is (will be capitalized later)
                all_words.append(word)
            else:
                # Split camelCase words
                split_words = re.sub(r"([A-Z])", r" \1", word).split()
                all_words.extend(split_words)

        # Capitalize first letter of each word, lowercase the rest
        pascal_words = [word.capitalize() for word in all_words if word]

        return "".join(pascal_words)

    def _validate_relationships(self, schema: SchnitzelSchema) -> List[str]:
        """
        Validate that all relationship targets reference existing models.

        Args:
            schema: The schema to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # Build set of all model names for efficient lookup
        model_names = set(schema.models.keys())

        # Check each model's relationships
        for model_name, model in schema.models.items():
            if model.relations is None:
                continue

            # Validate each relationship
            for relation_name, relation in model.relations.items():
                target_model = relation.model

                # Check if target model exists
                if target_model not in model_names:
                    error_msg = self._build_missing_relationship_error(
                        model_name, relation_name, relation.type, target_model
                    )
                    errors.append(error_msg)

        return errors

    def _build_missing_relationship_error(
        self, source_model: str, relation_name: str, relation_type: str, target_model: str
    ) -> str:
        """
        Build an error message for a missing relationship target model.

        Args:
            source_model: Name of the model containing the relationship
            relation_name: Name of the relationship field
            relation_type: Type of relationship (belongsTo, hasMany, hasOne)
            target_model: Name of the target model that doesn't exist

        Returns:
            Formatted error message string
        """
        error_parts = []

        # Main error - clearly state what's missing
        error_parts.append(
            f"Relationship target model '{target_model}' does not exist in schema"
        )

        # Show which model and relationship this applies to
        error_parts.append(
            f"Referenced in model '{source_model}' via {relation_type} relationship '{relation_name}'"
        )

        # Show the relationship definition
        error_parts.append(
            f"Relationship definition: {relation_name} ({relation_type}) -> {target_model}"
        )

        # Helpful suggestion
        error_parts.append(
            f"Add the '{target_model}' model to your schema or correct the relationship target"
        )

        return "\n".join(error_parts)
