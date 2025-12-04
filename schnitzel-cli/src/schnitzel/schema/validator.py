"""Schema validation for Schnitzel schemas."""

import re
from difflib import get_close_matches
from typing import Dict, List, Set

from pydantic import BaseModel

from .exceptions import ValidationError
from .models import FieldDefinition, Model, SchnitzelSchema


class ValidationResult(BaseModel):
    """Result of schema validation."""

    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    unique_fields: Dict[str, List[str]] = {}  # model_name -> [field_names with unique=True]

    @classmethod
    def success(cls, unique_fields: Dict[str, List[str]] | None = None, warnings: List[str] | None = None) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(valid=True, errors=[], warnings=warnings or [], unique_fields=unique_fields or {})

    @classmethod
    def failure(cls, errors: List[str], warnings: List[str] | None = None) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(valid=False, errors=errors, warnings=warnings or [], unique_fields={})


class SchemaValidator:
    """
    Validates Schnitzel schemas for correctness and consistency.

    Performs semantic validation beyond basic syntax checking, including:
    - Field type validation
    - Relationship validation
    - Naming convention validation
    - Required/optional field constraint validation
    - Unique constraint tracking
    """

    # Supported field types
    SUPPORTED_TYPES: Set[str] = {
        "string",
        "text",  # Alias for string (long text)
        "uuid",
        "int",
        "float",
        "bool",
        "datetime",
        "json",
        "enum",
        "vector",
    }

    # Supported string formats
    SUPPORTED_FORMATS: Set[str] = {
        "email",
        "phone",
        "url",
        "uri",
        "uuid",
        "date",
        "time",
        "datetime",
        "ip",
        "ipv4",
        "ipv6",
    }

    def __init__(self) -> None:
        """Initialize the schema validator."""
        # Track required fields for each model
        self.required_fields: dict[str, Set[str]] = {}
        # Track optional fields for each model
        self.optional_fields: dict[str, Set[str]] = {}
        # Track warnings (non-critical issues)
        self.warnings: List[str] = []

    def validate(self, schema: SchnitzelSchema) -> ValidationResult:
        """
        Validate a Schnitzel schema.

        Args:
            schema: The schema to validate

        Returns:
            ValidationResult with validation status, any errors found, and tracked unique fields
        """
        errors: List[str] = []
        self.warnings = []  # Reset warnings
        unique_fields: Dict[str, List[str]] = {}

        # Check for duplicate model names
        duplicate_errors = self._check_duplicate_model_names(schema)
        errors.extend(duplicate_errors)

        # Validate all models and collect unique fields
        for model_name, model in schema.models.items():
            model_errors = self._validate_model(model)
            errors.extend(model_errors)

            # Track fields with unique constraint
            model_unique_fields = [
                field_name
                for field_name, field in model.fields.items()
                if field.unique
            ]
            if model_unique_fields:
                unique_fields[model_name] = model_unique_fields

        # Validate relationships across models
        relationship_errors = self._validate_relationships(schema)
        errors.extend(relationship_errors)

        # Validate endpoint paths naming conventions (warnings only)
        if schema.endpoints:
            endpoint_warnings = self._validate_endpoint_paths(schema.endpoints)
            self.warnings.extend(endpoint_warnings)

        # Return validation result
        if errors:
            return ValidationResult.failure(errors, warnings=self.warnings)
        return ValidationResult.success(unique_fields=unique_fields, warnings=self.warnings)

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

        # Initialize tracking sets for this model
        if model.name not in self.required_fields:
            self.required_fields[model.name] = set()
        if model.name not in self.optional_fields:
            self.optional_fields[model.name] = set()

        # Validate all fields and track required/optional constraints
        for field_name, field in model.fields.items():
            field_errors = self._validate_field(field, field_name, model.name)
            errors.extend(field_errors)

            # Track required fields
            if field.required:
                self.required_fields[model.name].add(field_name)

            # Track optional fields
            if field.optional:
                self.optional_fields[model.name].add(field_name)

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

        # Validate format constraints for string fields
        if field.format is not None:
            format_error = self._validate_format_constraint(field, field_name, model_name)
            if format_error:
                errors.append(format_error)

        # Validate min/max constraints for numeric fields
        constraint_errors = self._validate_numeric_constraints(field, field_name, model_name)
        errors.extend(constraint_errors)

        # Validate index constraint
        index_error = self._validate_index_constraint(field, field_name, model_name)
        if index_error:
            errors.append(index_error)

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

    def _validate_format_constraint(
        self, field: FieldDefinition, field_name: str, model_name: str
    ) -> str | None:
        """
        Validate format constraint for a field.

        Format constraints are only valid for string fields.
        The format must be one of the supported formats.

        Args:
            field: The field to validate
            field_name: Name of the field
            model_name: Name of the containing model

        Returns:
            Error message if invalid, None if valid
        """
        # Format constraint is only valid for string fields
        if field.type != "string":
            error_parts = [
                f"Format constraint '{field.format}' is not valid for field '{field_name}' in model '{model_name}'",
                f"Format constraints can only be applied to string fields",
                f"Field type: {field.type}",
                f"Remove the format constraint or change the field type to 'string'"
            ]
            return "\n".join(error_parts)

        # Check if format is supported
        if field.format not in self.SUPPORTED_FORMATS:
            error_parts = [
                f"Unsupported format '{field.format}' for field '{field_name}' in model '{model_name}'",
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            ]

            # Get suggestions for similar formats
            suggestions = self._get_format_suggestions(field.format)
            if suggestions:
                if len(suggestions) == 1:
                    error_parts.append(f"Did you mean: {suggestions[0]}?")
                else:
                    suggestions_str = " or ".join(suggestions)
                    error_parts.append(f"Did you mean: {suggestions_str}?")

            return "\n".join(error_parts)

        return None

    def _get_format_suggestions(self, unsupported_format: str) -> List[str]:
        """
        Get suggestions for similar supported formats.

        Args:
            unsupported_format: The unsupported format to find suggestions for

        Returns:
            List of suggested format names (up to 2 suggestions)
        """
        # Manual mappings for common format mistakes
        manual_suggestions = {
            "e-mail": ["email"],
            "mail": ["email"],
            "telephone": ["phone"],
            "tel": ["phone"],
            "phonenumber": ["phone"],
            "website": ["url"],
            "link": ["url", "uri"],
            "ipaddress": ["ip"],
            "ipv4address": ["ipv4"],
            "ipv6address": ["ipv6"],
            "timestamp": ["datetime"],
        }

        # Check manual suggestions first
        if unsupported_format.lower() in manual_suggestions:
            return manual_suggestions[unsupported_format.lower()]

        # Get close matches using string similarity
        matches = get_close_matches(
            unsupported_format.lower(),
            [f.lower() for f in self.SUPPORTED_FORMATS],
            n=2,
            cutoff=0.6
        )

        # Map back to original case
        suggestions = []
        for match in matches:
            for supported_format in self.SUPPORTED_FORMATS:
                if supported_format.lower() == match:
                    suggestions.append(supported_format)
                    break

        return suggestions

    def _validate_numeric_constraints(
        self, field: FieldDefinition, field_name: str, model_name: str
    ) -> List[str]:
        """
        Validate min/max constraints for numeric fields.

        Constraints are only valid for numeric field types (int, float).
        If both min and max are specified, validates that min <= max.

        Args:
            field: The field to validate
            field_name: Name of the field
            model_name: Name of the containing model

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # Check if min or max constraints are specified
        has_min = field.min is not None
        has_max = field.max is not None

        if not has_min and not has_max:
            return errors

        # Numeric types that support min/max constraints
        numeric_types = {"int", "float"}

        # Validate that constraints are only applied to numeric types
        if field.type not in numeric_types:
            constraint_names = []
            if has_min:
                constraint_names.append(f"min: {field.min}")
            if has_max:
                constraint_names.append(f"max: {field.max}")

            error_parts = [
                f"Numeric constraints are not valid for field '{field_name}' in model '{model_name}'",
                f"Constraints: {', '.join(constraint_names)}",
                f"Field type: {field.type}",
                f"Numeric constraints (min/max) can only be applied to 'int' or 'float' fields",
                f"Remove the constraints or change the field type to 'int' or 'float'"
            ]
            errors.append("\n".join(error_parts))
            return errors

        # Validate that min <= max (if both are specified)
        if has_min and has_max:
            if field.min > field.max:
                error_parts = [
                    f"Invalid constraint values for field '{field_name}' in model '{model_name}'",
                    f"Minimum value ({field.min}) cannot be greater than maximum value ({field.max})",
                    f"Ensure min <= max"
                ]
                errors.append("\n".join(error_parts))

        return errors

    def _validate_index_constraint(
        self, field: FieldDefinition, field_name: str, model_name: str
    ) -> str | None:
        """
        Validate index constraint for a field.

        The index constraint validates that index: true is a boolean value.
        This is automatically handled by Pydantic, but we ensure the field
        exists and is properly typed.

        Args:
            field: The field to validate
            field_name: Name of the field
            model_name: Name of the containing model

        Returns:
            Error message if invalid, None if valid
        """
        # Validate that index is a boolean (Pydantic handles this, but we document it)
        if not isinstance(field.index, bool):
            error_parts = [
                f"Invalid index value for field '{field_name}' in model '{model_name}'",
                f"Index must be a boolean value (true or false)",
                f"Got: {type(field.index).__name__}"
            ]
            return "\n".join(error_parts)

        return None

    def _check_duplicate_model_names(self, schema: SchnitzelSchema) -> List[str]:
        """
        Check for duplicate model names in the schema.

        This checks if the same model name appears multiple times across
        different dictionary keys in schema.models. For example:
        - models["User"] has name="User" (OK)
        - models["Account"] has name="User" (DUPLICATE!)

        Args:
            schema: The schema to check for duplicate model names

        Returns:
            List of error messages for duplicate model names (empty if none)
        """
        errors: List[str] = []

        # Track which model names we've seen and where
        # model_name -> list of dictionary keys where it appears
        name_to_keys: Dict[str, List[str]] = {}

        # Scan all models
        for dict_key, model in schema.models.items():
            model_name = model.name

            if model_name not in name_to_keys:
                name_to_keys[model_name] = []

            name_to_keys[model_name].append(dict_key)

        # Report duplicates
        for model_name, dict_keys in name_to_keys.items():
            if len(dict_keys) > 1:
                # Found a duplicate!
                keys_str = "', '".join(dict_keys)
                error_parts = []
                error_parts.append(
                    f"Duplicate model name '{model_name}' found in schema"
                )
                error_parts.append(
                    f"Model '{model_name}' is defined multiple times at keys: '{keys_str}'"
                )
                error_parts.append(
                    "Each model must have a unique name"
                )
                errors.append("\n".join(error_parts))

        return errors

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

        # Check for circular dependencies in relationships
        circular_errors = self._detect_circular_dependencies(schema)
        errors.extend(circular_errors)

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

    def get_required_fields(self, model_name: str) -> Set[str]:
        """
        Get the set of required fields for a given model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Set of required field names
        """
        return self.required_fields.get(model_name, set())
    
    def get_optional_fields(self, model_name: str) -> Set[str]:
        """
        Get the set of optional fields for a given model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Set of optional field names
        """
        return self.optional_fields.get(model_name, set())

    def _detect_circular_dependencies(self, schema: SchnitzelSchema) -> List[str]:
        """
        Detect circular dependencies in relationships.

        Builds a directed graph of relationships and detects cycles using
        depth-first search. Only tracks belongsTo relationships, as these
        create actual data insertion order dependencies. hasMany and hasOne
        relationships don't create problematic circular dependencies.

        Valid patterns (not flagged):
        - User hasMany Posts, Post belongsTo User (bidirectional hasMany/belongsTo)
        - User hasOne Profile, Profile hasOne User (bidirectional hasOne)
        - User belongsTo User (self-referential belongsTo)

        Invalid patterns (flagged):
        - A belongsTo B, B belongsTo A (circular belongsTo dependency)

        Args:
            schema: The schema to check for circular dependencies

        Returns:
            List of error messages for each circular dependency found
        """
        errors: List[str] = []

        # Build relationship graph (adjacency list)
        # graph[model_name] = list of (target_model, relation_type, relation_name) tuples
        graph: dict[str, List[tuple[str, str, str]]] = {}

        for model_name, model in schema.models.items():
            if model.relations is None:
                continue

            if model_name not in graph:
                graph[model_name] = []

            for relation_name, relation in model.relations.items():
                target_model = relation.model
                # Only add edges to models that exist
                # Only track belongsTo relationships (these create actual dependency problems)
                # hasMany and hasOne relationships don't create problematic circular dependencies
                # Self-referential relationships are valid patterns (can use NULL for parent)
                if target_model in schema.models and relation.type == "belongsTo" and target_model != model_name:
                    graph[model_name].append((target_model, relation.type, relation_name))

        # Track visited nodes and nodes in current path
        visited: Set[str] = set()
        in_path: Set[str] = set()
        cycles_found: List[List[str]] = []

        def dfs(node: str, path: List[str]) -> None:
            """
            Depth-first search to detect cycles.

            Args:
                node: Current node being visited
                path: Path from root to current node
            """
            if node in in_path:
                # Found a cycle - extract the cycle from the path
                cycle_start_idx = path.index(node)
                cycle = path[cycle_start_idx:] + [node]
                # Only add if we haven't found this cycle before
                if cycle not in cycles_found:
                    cycles_found.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            in_path.add(node)
            path.append(node)

            # Visit all neighbors
            if node in graph:
                for target_model, _, _ in graph[node]:
                    dfs(target_model, path.copy())

            in_path.remove(node)

        # Run DFS from each unvisited node
        for model_name in schema.models.keys():
            if model_name not in visited:
                dfs(model_name, [])

        # Build error messages for each cycle found
        for cycle in cycles_found:
            error_msg = self._build_circular_dependency_error(cycle)
            errors.append(error_msg)

        return errors

    def _build_circular_dependency_error(self, cycle: List[str]) -> str:
        """
        Build an error message for a circular dependency.

        Args:
            cycle: List of model names forming the cycle (last element repeats first)

        Returns:
            Formatted error message string
        """
        error_parts = []

        # Build cycle visualization
        cycle_str = " -> ".join(cycle)

        # Main error
        error_parts.append(f"Circular dependency detected in relationships: {cycle_str}")

        # Explanation of why this is problematic
        error_parts.append(
            "This may cause issues with database schema generation and data insertion order."
        )

        # Helpful suggestion
        error_parts.append(
            "Suggestion: Consider using a junction table or removing one relationship."
        )

        return "\n".join(error_parts)

    def _validate_endpoint_paths(self, endpoints: Dict[str, any]) -> List[str]:
        """
        Validate endpoint paths follow kebab-case naming convention.

        Args:
            endpoints: Dictionary of endpoint definitions

        Returns:
            List of warning messages for naming convention violations
        """
        warnings: List[str] = []

        for endpoint_path, endpoint_def in endpoints.items():
            # Skip if it's not a string path
            if not isinstance(endpoint_path, str):
                continue

            # Check if path follows kebab-case convention
            # Endpoints should be like: /user-profiles, /order-items
            if not self._is_kebab_case_path(endpoint_path):
                suggested_path = self._to_kebab_case_path(endpoint_path)
                warning_parts = [
                    f"Endpoint path '{endpoint_path}' does not follow naming convention",
                    "Endpoint paths should use kebab-case",
                    f"Suggested path: '{suggested_path}'"
                ]
                warnings.append("\n".join(warning_parts))

        return warnings

    def _validate_event_names(self, events: Dict[str, any]) -> List[str]:
        """
        Validate event names follow dot.notation convention.

        Args:
            events: Dictionary of event definitions

        Returns:
            List of warning messages for naming convention violations
        """
        warnings: List[str] = []

        for event_name, event_def in events.items():
            # Check if event name follows dot.notation convention
            # Events should be like: order.placed, user.registered
            if not self._is_dot_notation(event_name):
                suggested_name = self._to_dot_notation(event_name)
                warning_parts = [
                    f"Event name '{event_name}' does not follow naming convention",
                    "Event names should use dot.notation",
                    f"Suggested name: '{suggested_name}'"
                ]
                warnings.append("\n".join(warning_parts))

        return warnings

    def _is_kebab_case_path(self, path: str) -> bool:
        """
        Check if an endpoint path follows kebab-case convention.

        Valid paths:
        - /users
        - /user-profiles
        - /api/v1/order-items
        - /users/{id}
        - /users/{id}/orders

        Invalid paths:
        - /userProfiles (camelCase)
        - /user_profiles (snake_case)
        - /UserProfiles (PascalCase)

        Args:
            path: The endpoint path to check

        Returns:
            True if path follows kebab-case, False otherwise
        """
        if not path:
            return False

        # Remove leading slash and parameter placeholders for validation
        path_without_params = re.sub(r'\{[^}]+\}', '', path)
        path_clean = path_without_params.strip('/')

        # Split by slashes to check each segment
        segments = [s for s in path_clean.split('/') if s]

        for segment in segments:
            # Each segment should be kebab-case: lowercase letters, numbers, and hyphens
            # Cannot start or end with hyphen
            # Cannot have consecutive hyphens
            pattern = r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$'
            if not re.match(pattern, segment):
                return False

        return True

    def _to_kebab_case_path(self, path: str) -> str:
        """
        Convert an endpoint path to kebab-case.

        Args:
            path: The endpoint path to convert

        Returns:
            Path converted to kebab-case
        """
        # Preserve parameter placeholders
        placeholders = re.findall(r'\{[^}]+\}', path)
        path_without_params = re.sub(r'\{[^}]+\}', '<<<PLACEHOLDER>>>', path)

        # Split by slashes
        segments = path_without_params.split('/')

        converted_segments = []
        for segment in segments:
            if segment == '<<<PLACEHOLDER>>>':
                # Will be replaced later
                converted_segments.append(segment)
            elif segment:
                # Convert segment to kebab-case
                # First handle camelCase/PascalCase
                s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', segment)
                s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
                # Replace underscores with hyphens
                s3 = s2.replace('_', '-')
                # Convert to lowercase
                converted_segments.append(s3.lower())
            else:
                converted_segments.append(segment)

        result = '/'.join(converted_segments)

        # Restore placeholders
        for placeholder in placeholders:
            result = result.replace('<<<PLACEHOLDER>>>', placeholder, 1)

        return result

    def _is_dot_notation(self, name: str) -> bool:
        """
        Check if an event name follows dot.notation convention.

        Valid event names:
        - order.placed
        - user.registered
        - payment.completed

        Invalid event names:
        - OrderPlaced (PascalCase)
        - order_placed (snake_case)
        - order-placed (kebab-case)

        Args:
            name: The event name to check

        Returns:
            True if name follows dot.notation, False otherwise
        """
        if not name:
            return False

        # Must contain at least one dot
        if '.' not in name:
            return False

        # Split by dots
        parts = name.split('.')

        for part in parts:
            # Each part should be lowercase letters only (no numbers, underscores, etc.)
            if not part or not part.islower() or not part.isalpha():
                return False

        return True

    def _to_dot_notation(self, name: str) -> str:
        """
        Convert an event name to dot.notation.

        Args:
            name: The event name to convert

        Returns:
            Name converted to dot.notation
        """
        # Convert to snake_case first, then replace underscores with dots
        snake = self._to_snake_case(name)
        # Replace underscores with dots
        dot_notation = snake.replace('_', '.')
        return dot_notation


class BreakingChangesDetector:
    """
    Detects breaking changes between two schema versions.

    Breaking changes include:
    - Removing required fields from models
    - Changing field types in incompatible ways
    - Removing models entirely
    - Changing field from optional to required
    - Removing or changing relationships
    """

    # Type changes that lose data (breaking)
    BREAKING_TYPE_CHANGES: Dict[str, Set[str]] = {
        "string": {"int", "float", "bool", "datetime", "uuid"},  # string -> numeric loses data
        "text": {"int", "float", "bool", "datetime", "uuid"},
        "int": {"string", "text", "bool", "datetime", "uuid"},  # int -> non-numeric loses data
        "float": {"string", "text", "int", "bool", "datetime", "uuid"},  # float -> int loses precision
        "bool": {"string", "text", "int", "float", "datetime", "uuid"},
        "datetime": {"string", "text", "int", "float", "bool", "uuid"},
        "uuid": {"int", "float", "bool", "datetime"},  # uuid -> string/text is OK
        "json": {"string", "text", "int", "float", "bool", "datetime", "uuid"},
        "vector": {"string", "text", "int", "float", "bool", "datetime", "uuid", "json"},
    }

    def detect_breaking_changes(self, old_schema: SchnitzelSchema, new_schema: SchnitzelSchema) -> List[str]:
        """
        Detect breaking changes between two schema versions.

        Args:
            old_schema: The previous schema version
            new_schema: The new schema version

        Returns:
            List of breaking change descriptions
        """
        breaking_changes: List[str] = []

        # Check for removed models
        breaking_changes.extend(self._check_removed_models(old_schema, new_schema))

        # Check for field changes in existing models
        for model_name, old_model in old_schema.models.items():
            if model_name in new_schema.models:
                new_model = new_schema.models[model_name]
                breaking_changes.extend(
                    self._check_model_changes(model_name, old_model, new_model)
                )

        return breaking_changes

    def _check_removed_models(self, old_schema: SchnitzelSchema, new_schema: SchnitzelSchema) -> List[str]:
        """
        Check for models that were removed.

        Args:
            old_schema: The previous schema version
            new_schema: The new schema version

        Returns:
            List of breaking change messages for removed models
        """
        breaking_changes: List[str] = []

        old_models = set(old_schema.models.keys())
        new_models = set(new_schema.models.keys())
        removed_models = old_models - new_models

        for model_name in sorted(removed_models):
            breaking_changes.append(
                f"BREAKING: Model '{model_name}' was removed\n"
                f"  Impact: All API endpoints and database tables for this model will be removed\n"
                f"  Migration: Ensure dependent code is updated before deploying"
            )

        return breaking_changes

    def _check_model_changes(self, model_name: str, old_model: Model, new_model: Model) -> List[str]:
        """
        Check for breaking changes in a model.

        Args:
            model_name: Name of the model being checked
            old_model: The old model definition
            new_model: The new model definition

        Returns:
            List of breaking change messages
        """
        breaking_changes: List[str] = []

        # Check for removed required fields
        breaking_changes.extend(
            self._check_removed_required_fields(model_name, old_model, new_model)
        )

        # Check for type changes
        breaking_changes.extend(
            self._check_field_type_changes(model_name, old_model, new_model)
        )

        # Check for required constraint changes
        breaking_changes.extend(
            self._check_required_constraint_changes(model_name, old_model, new_model)
        )

        # Check for removed relationships
        breaking_changes.extend(
            self._check_removed_relationships(model_name, old_model, new_model)
        )

        return breaking_changes

    def _check_removed_required_fields(
        self, model_name: str, old_model: Model, new_model: Model
    ) -> List[str]:
        """
        Check for required fields that were removed.

        Args:
            model_name: Name of the model
            old_model: The old model definition
            new_model: The new model definition

        Returns:
            List of breaking change messages
        """
        breaking_changes: List[str] = []

        old_fields = set(old_model.fields.keys())
        new_fields = set(new_model.fields.keys())
        removed_fields = old_fields - new_fields

        for field_name in sorted(removed_fields):
            old_field = old_model.fields[field_name]
            # Only flag as breaking if field was required or not explicitly optional
            if old_field.required or (not old_field.optional and not old_field.primary):
                breaking_changes.append(
                    f"BREAKING: Required field '{field_name}' removed from model '{model_name}'\n"
                    f"  Field type: {old_field.type}\n"
                    f"  Impact: API endpoints and database queries expecting this field will break\n"
                    f"  Migration: Mark field as optional before removing, or update all consumers"
                )

        return breaking_changes

    def _check_field_type_changes(
        self, model_name: str, old_model: Model, new_model: Model
    ) -> List[str]:
        """
        Check for field type changes that lose data.

        Args:
            model_name: Name of the model
            old_model: The old model definition
            new_model: The new model definition

        Returns:
            List of breaking change messages
        """
        breaking_changes: List[str] = []

        # Check fields that exist in both versions
        common_fields = set(old_model.fields.keys()) & set(new_model.fields.keys())

        for field_name in sorted(common_fields):
            old_field = old_model.fields[field_name]
            new_field = new_model.fields[field_name]

            old_type = old_field.type
            new_type = new_field.type

            # Check if type changed
            if old_type != new_type:
                # Check if this is a breaking type change
                if self._is_breaking_type_change(old_type, new_type):
                    breaking_changes.append(
                        f"BREAKING: Field '{field_name}' in model '{model_name}' changed type from '{old_type}' to '{new_type}'\n"
                        f"  Impact: Data may be lost or corrupted during migration\n"
                        f"  Migration: Create migration script to transform existing data"
                    )

        return breaking_changes

    def _check_required_constraint_changes(
        self, model_name: str, old_model: Model, new_model: Model
    ) -> List[str]:
        """
        Check for fields that changed from optional to required.

        Args:
            model_name: Name of the model
            old_model: The old model definition
            new_model: The new model definition

        Returns:
            List of breaking change messages
        """
        breaking_changes: List[str] = []

        # Check fields that exist in both versions
        common_fields = set(old_model.fields.keys()) & set(new_model.fields.keys())

        for field_name in sorted(common_fields):
            old_field = old_model.fields[field_name]
            new_field = new_model.fields[field_name]

            # Check if field became required
            old_optional = old_field.optional or (not old_field.required and not old_field.primary)
            new_required = new_field.required

            if old_optional and new_required:
                breaking_changes.append(
                    f"BREAKING: Field '{field_name}' in model '{model_name}' changed from optional to required\n"
                    f"  Impact: Existing API calls without this field will fail\n"
                    f"  Migration: Ensure all existing records have a value for this field"
                )

        return breaking_changes

    def _check_removed_relationships(
        self, model_name: str, old_model: Model, new_model: Model
    ) -> List[str]:
        """
        Check for relationships that were removed.

        Args:
            model_name: Name of the model
            old_model: The old model definition
            new_model: The new model definition

        Returns:
            List of breaking change messages
        """
        breaking_changes: List[str] = []

        # Handle cases where relations might be None
        old_relations = old_model.relations or {}
        new_relations = new_model.relations or {}

        old_relation_names = set(old_relations.keys())
        new_relation_names = set(new_relations.keys())
        removed_relations = old_relation_names - new_relation_names

        for relation_name in sorted(removed_relations):
            old_relation = old_relations[relation_name]
            breaking_changes.append(
                f"BREAKING: Relationship '{relation_name}' removed from model '{model_name}'\n"
                f"  Relationship type: {old_relation.type}\n"
                f"  Target model: {old_relation.model}\n"
                f"  Impact: API endpoints using this relationship will break\n"
                f"  Migration: Update queries to use alternative relationships or direct lookups"
            )

        return breaking_changes

    def _is_breaking_type_change(self, old_type: str, new_type: str) -> bool:
        """
        Check if a type change is breaking (loses data).

        Args:
            old_type: The old field type
            new_type: The new field type

        Returns:
            True if the type change is breaking
        """
        # Handle list types
        if old_type.startswith("list<") and old_type.endswith(">"):
            old_inner = old_type[5:-1]
            if new_type.startswith("list<") and new_type.endswith(">"):
                new_inner = new_type[5:-1]
                # Check if inner type change is breaking
                return self._is_breaking_type_change(old_inner, new_inner)
            else:
                # Changing from list to non-list is breaking
                return True

        if new_type.startswith("list<") and new_type.endswith(">"):
            # Changing from non-list to list is breaking
            return True

        # Check if this type change is in the breaking changes map
        if old_type in self.BREAKING_TYPE_CHANGES:
            return new_type in self.BREAKING_TYPE_CHANGES[old_type]

        # Default: if types are different and not in safe changes, consider it breaking
        return old_type != new_type


class UnusedModelDetector:
    """Detects models that are defined but never used in endpoints or relationships."""

    def detect_unused_models(self, schema: SchnitzelSchema) -> List[str]:
        """Detect models that are not referenced by any endpoint or relationship.

        Args:
            schema: The schema to analyze

        Returns:
            List of unused model names
        """
        all_models = set(schema.models.keys())
        used_models: Set[str] = set()

        # Check models used in endpoints
        if schema.endpoints:
            for endpoint_path, methods in schema.endpoints.items():
                if isinstance(methods, dict):
                    for method, config in methods.items():
                        if isinstance(config, dict):
                            # Check request body type
                            if "body" in config:
                                body_type = self._extract_type_name(config["body"])
                                if body_type:
                                    used_models.add(body_type)

                            # Check response types
                            if "response" in config:
                                resp = config["response"]
                                if isinstance(resp, dict):
                                    for status_code, resp_config in resp.items():
                                        if isinstance(resp_config, dict) and "type" in resp_config:
                                            resp_type = self._extract_type_name(resp_config["type"])
                                            if resp_type:
                                                used_models.add(resp_type)
                                        elif isinstance(resp_config, str):
                                            resp_type = self._extract_type_name(resp_config)
                                            if resp_type:
                                                used_models.add(resp_type)

        # Check models used in relationships
        for model_name, model in schema.models.items():
            # The model itself is used if it has relationships pointing to other models
            if model.relations:
                for rel_name, relation in model.relations.items():
                    if relation.model:
                        used_models.add(relation.model)
                        # The model that has the relationship is also "used"
                        used_models.add(model_name)

            # Check if any field references another model (FK)
            for field_name, field in model.fields.items():
                field_type = self._extract_type_name(field.type)
                if field_type and field_type in all_models:
                    used_models.add(field_type)
                    used_models.add(model_name)

        # Find unused models
        unused = all_models - used_models
        return sorted(list(unused))

    def _extract_type_name(self, type_str: str | dict) -> str | None:
        """Extract the base type name from a type string.

        Args:
            type_str: Type string like "User", "list[User]", "list<User>"

        Returns:
            Base type name or None
        """
        if isinstance(type_str, dict):
            return type_str.get("type")

        if not isinstance(type_str, str):
            return None

        # Handle list<Type> or list[Type]
        if type_str.startswith("list<") and type_str.endswith(">"):
            return type_str[5:-1]
        if type_str.startswith("list[") and type_str.endswith("]"):
            return type_str[5:-1]

        # Handle Optional<Type>
        if type_str.startswith("Optional<") and type_str.endswith(">"):
            return type_str[9:-1]

        return type_str


class MissingResponseTypeDetector:
    """Detects endpoints that are missing response type definitions."""

    def detect_missing_response_types(self, schema: SchnitzelSchema) -> List[str]:
        """Detect endpoints that don't have response types defined.

        Args:
            schema: The schema to analyze

        Returns:
            List of endpoint descriptions that are missing response types
        """
        missing = []

        if not schema.endpoints:
            return missing

        for endpoint_path, methods in schema.endpoints.items():
            if not isinstance(methods, dict):
                continue

            for method, config in methods.items():
                if not isinstance(config, dict):
                    continue

                # Skip DELETE endpoints as they often don't need response types
                if method.upper() == "DELETE":
                    continue

                # Check if response is defined
                has_response = False
                if "response" in config:
                    resp = config["response"]
                    if isinstance(resp, dict):
                        # Check if any status code has a type
                        for status_code, resp_config in resp.items():
                            if isinstance(resp_config, dict) and "type" in resp_config:
                                has_response = True
                                break
                            elif isinstance(resp_config, str):
                                has_response = True
                                break
                    elif isinstance(resp, str):
                        has_response = True

                if not has_response:
                    endpoint_desc = f"{method.upper()} {endpoint_path}"
                    missing.append(endpoint_desc)

        return missing

    def detect_undefined_response_types(self, schema: SchnitzelSchema) -> List[str]:
        """Detect endpoints that reference undefined models in response types.

        Args:
            schema: The schema to analyze

        Returns:
            List of errors for undefined response types
        """
        errors = []
        all_models = set(schema.models.keys())

        # Add primitive types
        primitive_types = {"string", "int", "float", "bool", "uuid", "datetime", "json", "void", "null"}

        if not schema.endpoints:
            return errors

        for endpoint_path, methods in schema.endpoints.items():
            if not isinstance(methods, dict):
                continue

            for method, config in methods.items():
                if not isinstance(config, dict):
                    continue

                if "response" not in config:
                    continue

                resp = config["response"]
                if isinstance(resp, dict):
                    for status_code, resp_config in resp.items():
                        resp_type = None
                        if isinstance(resp_config, dict) and "type" in resp_config:
                            resp_type = resp_config["type"]
                        elif isinstance(resp_config, str):
                            resp_type = resp_config

                        if resp_type:
                            # Extract base type
                            base_type = self._extract_base_type(resp_type)
                            if base_type and base_type.lower() not in primitive_types:
                                if base_type not in all_models:
                                    errors.append(
                                        f"{method.upper()} {endpoint_path}: Response type '{base_type}' is not defined"
                                    )

        return errors

    def _extract_base_type(self, type_str: str) -> str | None:
        """Extract base type from type string."""
        if not isinstance(type_str, str):
            return None

        # Handle list<Type> or list[Type]
        if type_str.startswith("list<") and type_str.endswith(">"):
            return type_str[5:-1]
        if type_str.startswith("list[") and type_str.endswith("]"):
            return type_str[5:-1]

        return type_str
