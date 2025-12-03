"""
Exceptions for schema parsing and validation.
"""


class SchemaError(Exception):
    """Base exception for all schema-related errors."""
    pass


class YAMLParseError(SchemaError):
    """Raised when YAML syntax is invalid."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        line_content: str | None = None,
        filename: str | None = None,
    ):
        """Initialize YAML parse error with detailed location information.

        Args:
            message: Human-readable error description
            line: Line number where the error occurred (1-indexed)
            column: Column number where the error occurred (1-indexed)
            line_content: The actual content of the problematic line
            filename: Name of the file being parsed
        """
        self.line = line
        self.column = column
        self.line_content = line_content
        self.filename = filename

        # Build formatted error message
        error_parts = []

        if filename:
            error_parts.append(f"{filename}:")

        error_parts.append("Invalid YAML syntax")

        if line is not None and column is not None:
            error_parts.append(f"at line {line}, column {column}")
        elif line is not None:
            error_parts.append(f"at line {line}")

        formatted_message = " ".join(error_parts)
        formatted_message += f"\n  Reason: {message}"

        if line_content:
            formatted_message += f'\n  Line content: "{line_content}"'

        super().__init__(formatted_message)


class ImportError(SchemaError):
    """Raised when an import cannot be resolved."""

    def __init__(self, message: str, missing_file: str | None = None, importing_file: str | None = None):
        self.missing_file = missing_file
        self.importing_file = importing_file
        if missing_file and importing_file:
            super().__init__(
                f"Import error in {importing_file}: {message}\n"
                f"  Missing file: {missing_file}\n"
                f"  Tip: Check that the file path is correct and the file exists."
            )
        else:
            super().__init__(message)


class CircularImportError(SchemaError):
    """Raised when a circular import is detected."""

    def __init__(self, import_chain: list[str]):
        self.import_chain = import_chain
        chain_str = " � ".join(import_chain)
        super().__init__(
            f"Circular import detected\n"
            f"  Import chain: {chain_str}\n"
            f"\n"
            f"  Tip: Remove one of the imports to break the cycle."
        )


class ValidationError(SchemaError):
    """Raised when schema validation fails."""
    pass
