"""Security validation for Schnitzel schemas.

This module provides security-focused validation to detect potential
vulnerabilities in schema definitions according to Schnitzel's
zero-tolerance security policy.
"""

from typing import Any, Dict, List, Set

from .models import SchnitzelSchema


class SecurityValidationResult:
    """Result of security validation."""

    def __init__(self) -> None:
        """Initialize security validation result."""
        self.violations: List[str] = []
        self.warnings: List[str] = []

    @property
    def has_violations(self) -> bool:
        """Check if there are any security violations."""
        return len(self.violations) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any security warnings."""
        return len(self.warnings) > 0


class SecurityValidator:
    """
    Validates Schnitzel schemas for security issues.

    Performs security-focused validation including:
    - Password fields should not be exposed in API responses
    - Sensitive fields (email, phone) should have appropriate auth requirements
    - Delete endpoints should require authentication
    - Admin-only endpoints should have role restrictions
    """

    # Field names that commonly contain passwords
    PASSWORD_FIELD_PATTERNS: Set[str] = {
        "password",
        "passwd",
        "pwd",
        "password_hash",
        "hashed_password",
        "password_digest",
    }

    # Field names/formats that are considered sensitive
    SENSITIVE_FIELD_PATTERNS: Set[str] = {
        "email",
        "phone",
        "ssn",
        "social_security",
        "credit_card",
        "card_number",
        "api_key",
        "secret",
        "token",
        "private_key",
    }

    # Sensitive formats
    SENSITIVE_FORMATS: Set[str] = {
        "email",
        "phone",
    }

    def __init__(self) -> None:
        """Initialize the security validator."""
        pass

    def validate(self, schema: SchnitzelSchema) -> SecurityValidationResult:
        """
        Validate a Schnitzel schema for security issues.

        Args:
            schema: The schema to validate

        Returns:
            SecurityValidationResult with any security violations found
        """
        result = SecurityValidationResult()

        # Check for password fields in models
        self._check_password_fields(schema, result)

        # Check endpoints for security issues
        if schema.endpoints:
            self._check_endpoint_security(schema, result)

        return result

    def _check_password_fields(
        self, schema: SchnitzelSchema, result: SecurityValidationResult
    ) -> None:
        """
        Check for password fields that might be exposed in API responses.

        Password fields should never be returned in API responses, even if hashed.
        This check warns developers about potential password exposure.

        Args:
            schema: The schema to check
            result: The result object to add violations to
        """
        for model_name, model in schema.models.items():
            for field_name, field in model.fields.items():
                field_lower = field_name.lower()

                # Check if field name suggests it contains a password
                if any(pattern in field_lower for pattern in self.PASSWORD_FIELD_PATTERNS):
                    violation_parts = [
                        f"Security: Password field '{field_name}' in model '{model_name}' may be exposed in API responses",
                        f"  Risk: Password fields should never be returned in API responses",
                        f"  Recommendation: Exclude this field from API responses using response schemas",
                        f"  Note: Even hashed passwords should not be exposed to clients",
                    ]
                    result.violations.append("\n".join(violation_parts))

    def _check_endpoint_security(
        self, schema: SchnitzelSchema, result: SecurityValidationResult
    ) -> None:
        """
        Check endpoints for security issues.

        Validates:
        - DELETE endpoints require authentication
        - Endpoints with sensitive data have auth requirements
        - Admin-only endpoints have proper role restrictions
        - POST/PUT/PATCH endpoints have auth for mutations

        Args:
            schema: The schema to check
            result: The result object to add violations to
        """
        for endpoint_path, endpoint_def in schema.endpoints.items():
            if not isinstance(endpoint_def, dict):
                continue

            # Check each HTTP method
            for method, method_def in endpoint_def.items():
                # Skip non-method keys (like 'params')
                if method.lower() in ["params", "description"]:
                    continue

                if not isinstance(method_def, dict):
                    continue

                # Check DELETE endpoints require auth
                if method.upper() == "DELETE":
                    self._check_delete_endpoint_auth(
                        endpoint_path, method_def, result
                    )

                # Check mutation endpoints (POST, PUT, PATCH, DELETE) have auth
                if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
                    self._check_mutation_endpoint_auth(
                        endpoint_path, method.upper(), method_def, result
                    )

                # Check endpoints with role requirements have auth
                self._check_role_based_endpoints(
                    endpoint_path, method.upper(), method_def, result
                )

                # Check endpoints returning sensitive data have auth
                self._check_sensitive_data_endpoints(
                    endpoint_path, method.upper(), method_def, schema, result
                )

    def _check_delete_endpoint_auth(
        self,
        endpoint_path: str,
        method_def: Dict[str, Any],
        result: SecurityValidationResult,
    ) -> None:
        """
        Check that DELETE endpoints require authentication.

        Args:
            endpoint_path: The endpoint path
            method_def: The method definition
            result: The result object to add violations to
        """
        auth = method_def.get("auth")

        if not auth or auth == "optional":
            violation_parts = [
                f"Security: DELETE endpoint '{endpoint_path}' does not require authentication",
                f"  Risk: Unauthenticated users could delete data",
                f"  Recommendation: Add 'auth: required' to this endpoint",
                f"  Example:",
                f"    DELETE:",
                f"      auth: required",
            ]
            result.violations.append("\n".join(violation_parts))

    def _check_mutation_endpoint_auth(
        self,
        endpoint_path: str,
        method: str,
        method_def: Dict[str, Any],
        result: SecurityValidationResult,
    ) -> None:
        """
        Check that mutation endpoints have authentication.

        Args:
            endpoint_path: The endpoint path
            method: The HTTP method
            method_def: The method definition
            result: The result object to add violations to
        """
        auth = method_def.get("auth")

        if not auth or auth == "optional":
            warning_parts = [
                f"Security: {method} endpoint '{endpoint_path}' does not require authentication",
                f"  Risk: Unauthenticated users could modify data",
                f"  Recommendation: Add 'auth: required' unless this is intentionally public",
                f"  Example:",
                f"    {method}:",
                f"      auth: required",
            ]
            result.warnings.append("\n".join(warning_parts))

    def _check_role_based_endpoints(
        self,
        endpoint_path: str,
        method: str,
        method_def: Dict[str, Any],
        result: SecurityValidationResult,
    ) -> None:
        """
        Check that endpoints with role requirements also have auth.

        Args:
            endpoint_path: The endpoint path
            method: The HTTP method
            method_def: The method definition
            result: The result object to add violations to
        """
        roles = method_def.get("roles")
        auth = method_def.get("auth")

        if roles and (not auth or auth != "required"):
            violation_parts = [
                f"Security: {method} endpoint '{endpoint_path}' has role restrictions but no authentication",
                f"  Roles required: {roles}",
                f"  Risk: Role checks are ineffective without authentication",
                f"  Recommendation: Add 'auth: required' to this endpoint",
                f"  Example:",
                f"    {method}:",
                f"      auth: required",
                f"      roles: {roles}",
            ]
            result.violations.append("\n".join(violation_parts))

        # Check if admin role is used (common pattern)
        if roles and isinstance(roles, list):
            if "admin" in roles and len(roles) == 1:
                # Admin-only endpoint - this is correct, just validate it has auth
                if not auth or auth != "required":
                    violation_parts = [
                        f"Security: Admin-only {method} endpoint '{endpoint_path}' does not require authentication",
                        f"  Risk: Critical security vulnerability - admin operations without auth",
                        f"  Recommendation: Add 'auth: required' to this endpoint",
                    ]
                    result.violations.append("\n".join(violation_parts))

    def _check_sensitive_data_endpoints(
        self,
        endpoint_path: str,
        method: str,
        method_def: Dict[str, Any],
        schema: SchnitzelSchema,
        result: SecurityValidationResult,
    ) -> None:
        """
        Check that endpoints returning sensitive data have authentication.

        Args:
            endpoint_path: The endpoint path
            method: The HTTP method
            method_def: The method definition
            schema: The schema to check models
            result: The result object to add violations to
        """
        # Only check GET endpoints for sensitive data exposure
        if method != "GET":
            return

        auth = method_def.get("auth")
        response = method_def.get("response", {})

        # Check if response includes sensitive data
        for status_code, response_def in response.items():
            if not isinstance(response_def, dict):
                continue

            response_type = response_def.get("type")
            if not response_type:
                continue

            # Extract model name from response type
            # Handle cases like: User, PaginatedResponse<User>, List<User>
            model_name = self._extract_model_name(response_type)
            if not model_name or model_name not in schema.models:
                continue

            # Check if model has sensitive fields
            model = schema.models[model_name]
            sensitive_fields = []

            for field_name, field in model.fields.items():
                field_lower = field_name.lower()

                # Check field name patterns
                if any(
                    pattern in field_lower
                    for pattern in self.SENSITIVE_FIELD_PATTERNS
                ):
                    sensitive_fields.append(field_name)

                # Check field format
                if field.format and field.format in self.SENSITIVE_FORMATS:
                    if field_name not in sensitive_fields:
                        sensitive_fields.append(field_name)

            # If sensitive fields found and no auth, warn
            if sensitive_fields and (not auth or auth != "required"):
                warning_parts = [
                    f"Security: {method} endpoint '{endpoint_path}' returns sensitive data without authentication",
                    f"  Model: {model_name}",
                    f"  Sensitive fields: {', '.join(sensitive_fields)}",
                    f"  Recommendation: Add 'auth: required' to protect sensitive data",
                    f"  Example:",
                    f"    {method}:",
                    f"      auth: required",
                ]
                result.warnings.append("\n".join(warning_parts))

    def _extract_model_name(self, response_type: str) -> str | None:
        """
        Extract model name from response type string.

        Handles:
        - User
        - PaginatedResponse<User>
        - List<User>
        - User[]

        Args:
            response_type: The response type string

        Returns:
            The model name or None if not found
        """
        if not response_type:
            return None

        # Remove whitespace
        response_type = response_type.strip()

        # Check for generic types: Type<Model> or Type[Model]
        if "<" in response_type:
            # Extract content between < and >
            start = response_type.index("<")
            end = response_type.rindex(">")
            inner = response_type[start + 1 : end].strip()
            return inner

        if "[" in response_type:
            # Extract content between [ and ]
            start = response_type.index("[")
            end = response_type.rindex("]")
            inner = response_type[start + 1 : end].strip()
            return inner

        # Direct model name
        return response_type
