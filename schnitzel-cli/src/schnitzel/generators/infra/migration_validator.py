"""Migration validation module for Schnitzel CLI.

Validates migration files before applying them to ensure:
- SQL syntax is valid
- Referenced tables/columns exist in schema
- Destructive operations are flagged for confirmation
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

from schnitzel.schema.models import SchnitzelSchema, Model


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a migration."""
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_number: Optional[int] = None
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of migration validation."""
    valid: bool
    issues: List[ValidationIssue]

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.severity == 'error']

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == 'warning']


class MigrationValidator:
    """Validates migration files against schema and best practices."""

    # SQL keywords that indicate destructive operations
    DESTRUCTIVE_OPERATIONS = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']

    # Common SQL syntax patterns
    CREATE_TABLE_PATTERN = re.compile(
        r"op\.create_table\s*\(\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )
    DROP_TABLE_PATTERN = re.compile(
        r"op\.drop_table\s*\(\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )
    ADD_COLUMN_PATTERN = re.compile(
        r"op\.add_column\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*sa\.Column\s*\(\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )
    DROP_COLUMN_PATTERN = re.compile(
        r"op\.drop_column\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    def __init__(self, schema: Optional[SchnitzelSchema] = None):
        """Initialize validator with optional schema for cross-validation.

        Args:
            schema: Schema to validate against (optional)
        """
        self.schema = schema
        self._schema_tables: Set[str] = set()
        self._schema_columns: Dict[str, Set[str]] = {}

        if schema:
            self._extract_schema_info()

    def _extract_schema_info(self) -> None:
        """Extract table and column information from schema."""
        if not self.schema:
            return

        for model_name, model in self.schema.models.items():
            table_name = self._pluralize_table_name(model.name)
            self._schema_tables.add(table_name)

            # Extract column names
            columns = set(model.fields.keys())

            # Add foreign key columns from relationships
            if model.relations:
                for rel_name, rel in model.relations.items():
                    if rel.type == "belongsTo":
                        fk_column = f"{self._to_snake_case(rel_name)}_id"
                        columns.add(fk_column)

            self._schema_columns[table_name] = columns

    def validate_migration_file(self, migration_file: Path) -> ValidationResult:
        """Validate a migration file.

        Args:
            migration_file: Path to migration file

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []

        if not migration_file.exists():
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity='error',
                    message=f"Migration file not found: {migration_file}"
                )]
            )

        # Read migration content
        try:
            content = migration_file.read_text(encoding='utf-8')
        except Exception as e:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity='error',
                    message=f"Failed to read migration file: {e}"
                )]
            )

        # Validate Python syntax
        issues.extend(self._validate_python_syntax(content, migration_file))

        # Validate SQL operations
        issues.extend(self._validate_sql_operations(content))

        # Validate against schema if available
        if self.schema:
            issues.extend(self._validate_against_schema(content))

        # Check for destructive operations
        issues.extend(self._check_destructive_operations(content))

        # Check upgrade and downgrade functions exist
        issues.extend(self._validate_migration_structure(content))

        # Check if there are any errors
        has_errors = any(issue.severity == 'error' for issue in issues)

        return ValidationResult(
            valid=not has_errors,
            issues=issues
        )

    def _validate_python_syntax(self, content: str, filepath: Path) -> List[ValidationIssue]:
        """Validate Python syntax of migration file.

        Args:
            content: Migration file content
            filepath: Path to file (for error messages)

        Returns:
            List of validation issues
        """
        issues = []

        try:
            compile(content, str(filepath), 'exec')
        except SyntaxError as e:
            issues.append(ValidationIssue(
                severity='error',
                message=f"Python syntax error: {e.msg}",
                line_number=e.lineno,
                code='PYTHON_SYNTAX_ERROR'
            ))

        return issues

    def _validate_sql_operations(self, content: str) -> List[ValidationIssue]:
        """Validate SQL operations in migration.

        Args:
            content: Migration file content

        Returns:
            List of validation issues
        """
        issues = []

        # Check for invalid Alembic operations
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for raw SQL execute that might have syntax issues
            if 'op.execute(' in line or 'connection.execute(' in line:
                # Extract SQL from execute call
                sql_match = re.search(r"execute\s*\(\s*['\"]([^'\"]+)['\"]", line)
                if sql_match:
                    sql = sql_match.group(1)
                    # Basic SQL syntax checks
                    if not self._is_valid_basic_sql(sql):
                        issues.append(ValidationIssue(
                            severity='warning',
                            message=f"Potentially invalid SQL syntax: {sql[:50]}...",
                            line_number=i,
                            code='INVALID_SQL_SYNTAX'
                        ))

        return issues

    def _validate_against_schema(self, content: str) -> List[ValidationIssue]:
        """Validate migration operations against schema.

        Args:
            content: Migration file content

        Returns:
            List of validation issues
        """
        issues = []

        # Check CREATE TABLE operations
        for match in self.CREATE_TABLE_PATTERN.finditer(content):
            table_name = match.group(1)
            if self.schema and table_name not in self._schema_tables:
                issues.append(ValidationIssue(
                    severity='warning',
                    message=f"Creating table '{table_name}' not found in schema",
                    code='TABLE_NOT_IN_SCHEMA'
                ))

        # Check DROP TABLE operations
        for match in self.DROP_TABLE_PATTERN.finditer(content):
            table_name = match.group(1)
            if self.schema and table_name not in self._schema_tables:
                issues.append(ValidationIssue(
                    severity='info',
                    message=f"Dropping table '{table_name}' not found in schema",
                    code='DROPPING_UNKNOWN_TABLE'
                ))

        # Check ADD COLUMN operations
        for match in self.ADD_COLUMN_PATTERN.finditer(content):
            table_name = match.group(1)
            column_name = match.group(2)

            if self.schema:
                if table_name not in self._schema_tables:
                    issues.append(ValidationIssue(
                        severity='warning',
                        message=f"Adding column to non-existent table '{table_name}'",
                        code='TABLE_NOT_EXISTS'
                    ))
                elif table_name in self._schema_columns:
                    if column_name in self._schema_columns[table_name]:
                        issues.append(ValidationIssue(
                            severity='warning',
                            message=f"Adding column '{column_name}' that already exists in schema",
                            code='COLUMN_ALREADY_EXISTS'
                        ))

        # Check DROP COLUMN operations
        for match in self.DROP_COLUMN_PATTERN.finditer(content):
            table_name = match.group(1)
            column_name = match.group(2)

            if self.schema:
                if table_name in self._schema_columns:
                    if column_name not in self._schema_columns[table_name]:
                        issues.append(ValidationIssue(
                            severity='info',
                            message=f"Dropping column '{column_name}' not found in schema",
                            code='COLUMN_NOT_IN_SCHEMA'
                        ))

        return issues

    def _check_destructive_operations(self, content: str) -> List[ValidationIssue]:
        """Check for destructive operations that need confirmation.

        Args:
            content: Migration file content

        Returns:
            List of validation issues
        """
        issues = []

        # Check for DROP operations
        if 'op.drop_table(' in content:
            issues.append(ValidationIssue(
                severity='warning',
                message="Migration contains DROP TABLE operation - data loss will occur",
                code='DESTRUCTIVE_DROP_TABLE'
            ))

        if 'op.drop_column(' in content:
            issues.append(ValidationIssue(
                severity='warning',
                message="Migration contains DROP COLUMN operation - data loss will occur",
                code='DESTRUCTIVE_DROP_COLUMN'
            ))

        # Check for ALTER operations that might be destructive
        if 'alter_column' in content.lower() and 'type_' in content:
            issues.append(ValidationIssue(
                severity='warning',
                message="Migration contains column type change - may cause data loss",
                code='DESTRUCTIVE_TYPE_CHANGE'
            ))

        return issues

    def _validate_migration_structure(self, content: str) -> List[ValidationIssue]:
        """Validate that migration has required structure.

        Args:
            content: Migration file content

        Returns:
            List of validation issues
        """
        issues = []

        # Check for upgrade function
        if 'def upgrade()' not in content:
            issues.append(ValidationIssue(
                severity='error',
                message="Migration missing 'upgrade()' function",
                code='MISSING_UPGRADE_FUNCTION'
            ))

        # Check for downgrade function
        if 'def downgrade()' not in content:
            issues.append(ValidationIssue(
                severity='error',
                message="Migration missing 'downgrade()' function",
                code='MISSING_DOWNGRADE_FUNCTION'
            ))

        # Check for revision ID
        if 'revision = ' not in content:
            issues.append(ValidationIssue(
                severity='error',
                message="Migration missing revision ID",
                code='MISSING_REVISION'
            ))

        # Check for Alembic import
        if 'from alembic import op' not in content:
            issues.append(ValidationIssue(
                severity='error',
                message="Migration missing 'from alembic import op' import",
                code='MISSING_ALEMBIC_IMPORT'
            ))

        return issues

    def _is_valid_basic_sql(self, sql: str) -> bool:
        """Perform basic SQL syntax validation.

        Args:
            sql: SQL statement to validate

        Returns:
            True if basic syntax appears valid
        """
        # Very basic checks - just look for common syntax errors
        sql = sql.strip()

        if not sql:
            return False

        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            return False

        # Check for balanced quotes
        single_quotes = sql.count("'") - sql.count("\\'")
        double_quotes = sql.count('"') - sql.count('\\"')

        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            return False

        return True

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _pluralize_table_name(self, model_name: str) -> str:
        """Convert model name to pluralized snake_case table name."""
        snake = self._to_snake_case(model_name)

        # Simple pluralization rules
        if snake.endswith("y") and len(snake) > 1 and snake[-2] not in "aeiou":
            return snake[:-1] + "ies"
        elif snake.endswith("s") or snake.endswith("x") or snake.endswith("z"):
            return snake + "es"
        else:
            return snake + "s"


def validate_pending_migrations(
    migrations_dir: Path,
    schema: Optional[SchnitzelSchema] = None
) -> Tuple[bool, Dict[str, ValidationResult]]:
    """Validate all pending migrations in a directory.

    Args:
        migrations_dir: Directory containing migration files
        schema: Schema to validate against (optional)

    Returns:
        Tuple of (all_valid, results_dict)
    """
    validator = MigrationValidator(schema)
    results = {}
    all_valid = True

    if not migrations_dir.exists():
        return False, {}

    # Find all migration files
    migration_files = sorted(migrations_dir.glob("*.py"))

    for migration_file in migration_files:
        # Skip __init__.py and other special files
        if migration_file.name.startswith('__'):
            continue

        result = validator.validate_migration_file(migration_file)
        results[migration_file.name] = result

        if not result.valid:
            all_valid = False

    return all_valid, results
