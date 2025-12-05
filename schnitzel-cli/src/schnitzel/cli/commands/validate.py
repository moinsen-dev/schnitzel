"""Validate command for Schnitzel CLI - schema validation and syntax checking."""

import json
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from schnitzel.schema import (
    SchemaParser,
    SchemaValidator,
    ValidationResult,
    SchnitzelSchema,
    BreakingChangesDetector,
    SecurityValidator,
    SecurityValidationResult,
)
from schnitzel.schema.exceptions import (
    SchemaError,
    YAMLParseError,
    ValidationError,
    VersionError,
)
from schnitzel.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)

OutputFormat = Literal["rich", "json", "plain"]


def _is_quiet_mode() -> bool:
    """Check if quiet mode is enabled via CLI.

    Returns:
        bool: True if quiet mode is enabled
    """
    from schnitzel.cli import is_quiet_mode

    return is_quiet_mode()


def validate_command(
    schema: Path = typer.Argument(
        ...,
        help="Path to the Schnitzel schema YAML file",
        exists=True,
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail on warnings and naming convention violations",
    ),
    breaking: bool = typer.Option(
        False,
        "--breaking",
        help="Check for breaking API changes by comparing with previous schema version",
    ),
    compare_with: Path = typer.Option(
        None,
        "--compare-with",
        help="Path to previous schema version for breaking change detection (required with --breaking)",
        exists=True,
    ),
    format: OutputFormat = typer.Option(
        "rich",
        "--format",
        help="Output format: rich (default, colored terminal), json (machine-readable), or plain (simple text)",
    ),
    security: bool = typer.Option(
        False,
        "--security",
        help="Check for security vulnerabilities in the schema",
    ),
) -> None:
    """Validate a Schnitzel schema file for correctness.

    This command validates:
    - YAML syntax correctness
    - Schema structure and required fields
    - Field types and constraints
    - Relationship definitions
    - Naming conventions (PascalCase for models, snake_case for fields)
    - Circular dependency detection
    - Security vulnerabilities (with --security flag)

    Examples:
        schnitzel validate schema.schnitzel.yaml
        schnitzel validate schema.yaml --strict
        schnitzel validate schema.yaml --breaking
        schnitzel validate schema.yaml --security
    """
    quiet = _is_quiet_mode()

    try:
        # Step 1: Parse and validate schema syntax
        # Only show progress message in Rich format (not json/plain for clean machine-readable output)
        if not quiet and format == "rich":
            console.print(f"[blue]Validating schema:[/blue] {schema.name}")

        parser = SchemaParser()
        schema_obj = parser.parse(schema)

        # Step 2: Validate schema structure and semantics
        validator = SchemaValidator()
        validation_result: ValidationResult = validator.validate(schema_obj)

        # Step 3: Check validation result
        if not validation_result.valid:
            if not quiet:
                if format == "json":
                    report = _format_json_report(validation_result, schema_obj, strict, None)
                    print(report)
                elif format == "plain":
                    report = _format_plain_report(validation_result, schema_obj, strict, None)
                    print(report)
                else:
                    console.print("[red]✗ Schema validation failed:[/red]\n")
                    for error in validation_result.errors:
                        console.print(f"[red]  • {error}[/red]\n")
            else:
                console.print("FAILED")
            raise typer.Exit(code=1)

        # Step 4: Check for N+1 query issues (always run this check)
        n_plus_1_warnings = validator.detect_n_plus_1_issues(schema_obj)

        # Step 5: Check for warnings
        has_warnings = bool(validation_result.warnings) or bool(n_plus_1_warnings)

        # If strict mode and warnings exist, fail
        if strict and has_warnings:
            if not quiet:
                if format == "json":
                    report = _format_json_report(validation_result, schema_obj, strict, None)
                    print(report)
                elif format == "plain":
                    report = _format_plain_report(validation_result, schema_obj, strict, None)
                    print(report)
                else:
                    console.print("[red]✗ Schema validation failed (strict mode):[/red]\n")
                    for warning in validation_result.warnings:
                        console.print(f"[red]  • {warning}[/red]\n")
            else:
                console.print("FAILED")
            raise typer.Exit(code=1)

        # Step 5: Run security validation if requested
        security_result = None
        if security:
            security_validator = SecurityValidator()
            security_result = security_validator.validate(schema_obj)

            # If security violations found, fail
            if security_result.has_violations:
                if not quiet:
                    console.print(f"\n[red]✗ Security validation failed ({len(security_result.violations)} violation(s)):[/red]\n")
                    for violation in security_result.violations:
                        console.print(f"[red]{violation}[/red]\n")
                else:
                    console.print(f"SECURITY_FAILED ({len(security_result.violations)} violations)")
                raise typer.Exit(code=1)

            # Display security warnings
            if security_result.has_warnings and not quiet:
                console.print(f"\n[yellow]⚠ Security warnings ({len(security_result.warnings)}):[/yellow]\n")
                for warning in security_result.warnings:
                    console.print(f"[yellow]{warning}[/yellow]\n")

        # Step 6: Display success message and summary
        if not quiet:
            if format == "json":
                # JSON output
                report = _format_json_report(validation_result, schema_obj, strict, security_result)
                print(report)
            elif format == "plain":
                # Plain text output
                report = _format_plain_report(validation_result, schema_obj, strict, security_result)
                print(report)
            else:
                # Rich formatted output (default)
                console.print("[green]✓ Schema is valid![/green]\n")

                # Display schema summary
                _display_schema_summary(schema_obj, validation_result)

                # Display warnings if any
                if validation_result.warnings:
                    console.print("\n[yellow]⚠ Naming Convention Warnings:[/yellow]\n")
                    for warning in validation_result.warnings:
                        console.print(f"[yellow]  • {warning}[/yellow]\n")

                # Display N+1 query warnings
                if n_plus_1_warnings:
                    console.print("\n[yellow]⚠ Potential N+1 Query Issues:[/yellow]\n")
                    for warning in n_plus_1_warnings:
                        console.print(f"{warning}\n")

                # Display strict mode hint if there are any warnings
                if has_warnings:
                    console.print("[dim]Use --strict to treat warnings as errors[/dim]")

                # Display security status if checked
                if security and security_result and not security_result.has_violations and not security_result.has_warnings:
                    console.print("\n[green]✓ No security issues found[/green]")

                # Display helpful hints
                if not breaking:
                    console.print(
                        "\n[dim]Tip: Use --breaking to check for breaking API changes[/dim]"
                    )
                if not security:
                    console.print(
                        "[dim]Tip: Use --security to check for security vulnerabilities[/dim]"
                    )
        else:
            # In quiet mode, show warning count if present
            if security_result and security_result.has_warnings:
                console.print(f"OK ({len(validation_result.warnings)} warnings, {len(security_result.warnings)} security warnings)")
            elif has_warnings:
                console.print(f"OK ({len(validation_result.warnings)} warnings)")
            else:
                console.print("OK")

        # Handle --breaking flag for breaking change detection
        if breaking:
            if not compare_with:
                if not quiet:
                    console.print(
                        "\n[red]✗ Breaking change detection requires --compare-with option[/red]"
                    )
                    console.print("[dim]Usage: schnitzel validate schema.yaml --breaking --compare-with old_schema.yaml[/dim]")
                else:
                    console.print("MISSING_COMPARE_WITH")
                raise typer.Exit(code=1)

            # Parse the old schema for comparison
            try:
                old_schema_obj = parser.parse(compare_with)

                # Detect breaking changes
                detector = BreakingChangesDetector()
                breaking_changes = detector.detect_breaking_changes(old_schema_obj, schema_obj)

                if breaking_changes:
                    if not quiet:
                        console.print(f"\n[red]✗ Detected {len(breaking_changes)} breaking change(s):[/red]\n")
                        for change in breaking_changes:
                            console.print(f"[red]{change}[/red]\n")
                    else:
                        console.print(f"BREAKING_CHANGES ({len(breaking_changes)})")
                    raise typer.Exit(code=1)
                else:
                    if not quiet:
                        console.print("\n[green]✓ No breaking changes detected[/green]")
                        console.print("[dim]The schema is backward compatible with the previous version[/dim]")
                    else:
                        console.print("NO_BREAKING_CHANGES")

            except (YAMLParseError, ValidationError, VersionError, SchemaError) as e:
                if not quiet:
                    console.print(f"\n[red]✗ Failed to parse comparison schema:[/red]\n")
                    console.print(f"  {e}")
                else:
                    console.print("COMPARE_SCHEMA_ERROR")
                raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise Exit exceptions (from validation failures)
        raise

    except YAMLParseError as e:
        # YAML syntax error
        if not quiet:
            console.print("[red]✗ YAML syntax error:[/red]\n")
            _display_yaml_error(e)
        else:
            console.print("YAML_ERROR")
        raise typer.Exit(code=1)

    except VersionError as e:
        # Schema version error
        if not quiet:
            console.print(f"[red]✗ Schema version error:[/red]\n")
            console.print(f"  {e}\n")
            if e.supported_versions:
                console.print(
                    f"  Supported versions: {', '.join(e.supported_versions)}"
                )
        else:
            console.print("VERSION_ERROR")
        raise typer.Exit(code=1)

    except ValidationError as e:
        # Schema validation error
        if not quiet:
            console.print("[red]✗ Schema validation failed:[/red]\n")
            console.print(str(e))
        else:
            console.print("VALIDATION_ERROR")
        raise typer.Exit(code=1)

    except SchemaError as e:
        # Generic schema error
        if not quiet:
            console.print(f"[red]✗ Schema error:[/red]\n")
            console.print(f"  {e}")
        else:
            console.print("SCHEMA_ERROR")
        raise typer.Exit(code=1)

    except Exception as e:
        # Unexpected error
        if not quiet:
            console.print(f"[red]✗ Unexpected error:[/red]\n")
            console.print(f"  {e}")
            logger.exception("Unexpected error during validation")
        else:
            console.print("ERROR")
        raise typer.Exit(code=1)


def _display_schema_summary(schema: SchnitzelSchema, validation_result: ValidationResult) -> None:
    """Display a summary of the validated schema.

    Args:
        schema: The validated SchnitzelSchema object
        validation_result: The validation result with tracked fields
    """
    # Create summary table
    table = Table(title="Schema Summary", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Details", style="dim")

    # Count models
    model_count = len(schema.models)
    table.add_row("Models", str(model_count), ", ".join(schema.models.keys()) if model_count <= 5 else f"{', '.join(list(schema.models.keys())[:5])}, ...")

    # Count total fields
    total_fields = sum(len(model.fields) for model in schema.models.values())
    table.add_row("Total Fields", str(total_fields), "")

    # Count relationships
    total_relations = sum(
        len(model.relations) if model.relations else 0
        for model in schema.models.values()
    )
    if total_relations > 0:
        table.add_row("Relationships", str(total_relations), "")

    # Count unique fields
    total_unique = sum(len(fields) for fields in validation_result.unique_fields.values())
    if total_unique > 0:
        table.add_row("Unique Fields", str(total_unique), "")

    # Count endpoints
    if schema.endpoints:
        endpoint_count = len(schema.endpoints)
        table.add_row("Endpoints", str(endpoint_count), "")

    # Show naming convention status
    warning_count = len(validation_result.warnings)
    if warning_count == 0:
        table.add_row("Naming Conventions", "✓", "[green]All conventions followed[/green]")
    else:
        table.add_row("Naming Conventions", f"{warning_count}", f"[yellow]{warning_count} warnings[/yellow]")

    console.print(table)

    # Show model details
    if schema.models:
        console.print("\n[bold cyan]Models:[/bold cyan]")
        for model_name, model in schema.models.items():
            field_count = len(model.fields)
            relation_count = len(model.relations) if model.relations else 0

            details = [f"{field_count} fields"]
            if relation_count > 0:
                details.append(f"{relation_count} relations")

            # Add unique field indicator
            if model_name in validation_result.unique_fields:
                unique_fields = validation_result.unique_fields[model_name]
                if unique_fields:
                    details.append(f"{len(unique_fields)} unique")

            console.print(f"  • [cyan]{model_name}[/cyan] ({', '.join(details)})")


def _display_yaml_error(error: YAMLParseError) -> None:
    """Display a detailed YAML parsing error.

    Args:
        error: The YAMLParseError to display
    """
    # Build error message parts
    error_parts = []

    if error.filename:
        error_parts.append(f"[bold]File:[/bold] {error.filename}")

    if error.line is not None:
        location = f"Line {error.line}"
        if error.column is not None:
            location += f", Column {error.column}"
        error_parts.append(f"[bold]Location:[/bold] {location}")

    error_parts.append(f"[bold]Error:[/bold] {error.message}")

    if error.line_content:
        error_parts.append(f"\n[bold]Content:[/bold]\n  {error.line_content}")

        # Add pointer to error location if column is available
        if error.column is not None:
            pointer = " " * (error.column + 1) + "^"
            error_parts.append(f"  [red]{pointer}[/red]")

    # Display as panel
    error_message = "\n".join(error_parts)
    console.print(
        Panel(
            error_message,
            title="YAML Syntax Error",
            border_style="red",
            expand=False,
        )
    )

    # Add helpful hints
    console.print("\n[yellow]Hints:[/yellow]")
    console.print("  • Check for missing colons, quotes, or indentation errors")
    console.print("  • Ensure all YAML keys are properly formatted")
    console.print("  • Verify that field names don't contain duplicate keys")


def _format_validation_report(
    validation_result: ValidationResult,
    schema_obj: SchnitzelSchema,
    format_type: OutputFormat,
    strict: bool = False,
) -> str:
    """Format validation report in the specified format.

    Args:
        validation_result: The validation result
        schema_obj: The validated schema object
        format_type: Output format (rich, json, or plain)
        strict: Whether strict mode is enabled

    Returns:
        Formatted report as string
    """
    if format_type == "json":
        return _format_json_report(validation_result, schema_obj, strict)
    elif format_type == "plain":
        return _format_plain_report(validation_result, schema_obj, strict)
    else:  # rich
        return _format_rich_report(validation_result, schema_obj, strict)


def _format_json_report(
    validation_result: ValidationResult,
    schema_obj: SchnitzelSchema,
    strict: bool = False,
    security_result: SecurityValidationResult | None = None,
) -> str:
    """Format validation report as JSON.

    Args:
        validation_result: The validation result
        schema_obj: The validated schema object
        strict: Whether strict mode is enabled

    Returns:
        JSON formatted report
    """
    # Count statistics
    model_count = len(schema_obj.models)
    total_fields = sum(len(model.fields) for model in schema_obj.models.values())
    total_relations = sum(
        len(model.relations) if model.relations else 0
        for model in schema_obj.models.values()
    )
    total_unique = sum(len(fields) for fields in validation_result.unique_fields.values())

    # In strict mode, warnings count as failures
    is_valid = validation_result.valid
    if strict and validation_result.warnings:
        is_valid = False

    report = {
        "valid": is_valid,
        "strict_mode": strict,
        "summary": {
            "models": model_count,
            "total_fields": total_fields,
            "relationships": total_relations,
            "unique_fields": total_unique,
        },
        "errors": validation_result.errors,
        "warnings": validation_result.warnings,
        "models": [],
    }

    # Add model details
    for model_name, model in schema_obj.models.items():
        field_count = len(model.fields)
        relation_count = len(model.relations) if model.relations else 0
        unique_fields = validation_result.unique_fields.get(model_name, [])

        model_info = {
            "name": model_name,
            "field_count": field_count,
            "relation_count": relation_count,
            "unique_field_count": len(unique_fields),
            "unique_fields": unique_fields,
        }
        report["models"].append(model_info)

    return json.dumps(report, indent=2, ensure_ascii=False)


def _format_plain_report(
    validation_result: ValidationResult,
    schema_obj: SchnitzelSchema,
    strict: bool = False,
    security_result: SecurityValidationResult | None = None,
) -> str:
    """Format validation report as plain text.

    Args:
        validation_result: The validation result
        schema_obj: The validated schema object
        strict: Whether strict mode is enabled

    Returns:
        Plain text formatted report
    """
    lines = []

    # Header
    if validation_result.valid and (not strict or not validation_result.warnings):
        lines.append("VALIDATION PASSED")
    else:
        lines.append("VALIDATION FAILED")

    lines.append("=" * 60)
    lines.append("")

    # Summary section
    lines.append("SUMMARY")
    lines.append("-" * 60)

    model_count = len(schema_obj.models)
    total_fields = sum(len(model.fields) for model in schema_obj.models.values())
    total_relations = sum(
        len(model.relations) if model.relations else 0
        for model in schema_obj.models.values()
    )
    total_unique = sum(len(fields) for fields in validation_result.unique_fields.values())

    lines.append(f"Models:        {model_count}")
    lines.append(f"Total Fields:  {total_fields}")
    if total_relations > 0:
        lines.append(f"Relationships: {total_relations}")
    if total_unique > 0:
        lines.append(f"Unique Fields: {total_unique}")
    lines.append(f"Errors:        {len(validation_result.errors)}")
    lines.append(f"Warnings:      {len(validation_result.warnings)}")
    lines.append("")

    # Errors section
    if validation_result.errors:
        lines.append("ERRORS")
        lines.append("-" * 60)
        for i, error in enumerate(validation_result.errors, 1):
            lines.append(f"{i}. {error}")
            lines.append("")

    # Warnings section
    if validation_result.warnings:
        lines.append("WARNINGS")
        lines.append("-" * 60)
        for i, warning in enumerate(validation_result.warnings, 1):
            lines.append(f"{i}. {warning}")
            lines.append("")

    # Models section
    if validation_result.valid:
        lines.append("MODELS")
        lines.append("-" * 60)
        for model_name, model in schema_obj.models.items():
            field_count = len(model.fields)
            relation_count = len(model.relations) if model.relations else 0

            details = [f"{field_count} fields"]
            if relation_count > 0:
                details.append(f"{relation_count} relations")

            if model_name in validation_result.unique_fields:
                unique_fields = validation_result.unique_fields[model_name]
                if unique_fields:
                    details.append(f"{len(unique_fields)} unique")

            lines.append(f"  {model_name}: {', '.join(details)}")

    return "\n".join(lines)


def _format_rich_report(
    validation_result: ValidationResult,
    schema_obj: SchnitzelSchema,
    strict: bool = False,
) -> str:
    """Format validation report with Rich formatting (returns empty string for console output).

    This function uses console.print() directly for Rich formatting.

    Args:
        validation_result: The validation result
        schema_obj: The validated schema object
        strict: Whether strict mode is enabled

    Returns:
        Empty string (output is printed to console directly)
    """
    # Rich formatting is handled inline in validate_command
    # This function is a placeholder for consistency
    return ""
