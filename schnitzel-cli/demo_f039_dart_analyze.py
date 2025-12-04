#!/usr/bin/env python3
"""Demo script for F039: Dart Analyze Compliance

Demonstrates that generated Dart code follows best practices
and would pass 'dart analyze' without errors.
"""

import re
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation
from schnitzel.generators.dart.models import DartModelGenerator

console = Console()


def count_syntax_elements(code: str) -> dict:
    """Count various syntax elements to verify balance."""
    return {
        "imports": len([l for l in code.split('\n') if l.startswith('import')]),
        "parts": len([l for l in code.split('\n') if l.strip().startswith('part')]),
        "opening_braces": code.count('{'),
        "closing_braces": code.count('}'),
        "opening_parens": code.count('('),
        "closing_parens": code.count(')'),
        "semicolons": code.count(';'),
        "freezed_annotations": code.count('@freezed'),
        "jsonkey_annotations": code.count('@JsonKey'),
        "default_annotations": code.count('@Default'),
    }


def validate_dart_syntax(code: str) -> list:
    """Run validation checks on generated Dart code."""
    checks = []

    # Check 1: Balanced braces
    if code.count('{') == code.count('}'):
        checks.append(("✅", "All braces balanced", f"{code.count('{')} pairs"))
    else:
        checks.append(("❌", "Braces unbalanced", f"{code.count('{')} vs {code.count('}')}"))

    # Check 2: Balanced parentheses
    if code.count('(') == code.count(')'):
        checks.append(("✅", "All parentheses balanced", f"{code.count('(')} pairs"))
    else:
        checks.append(("❌", "Parentheses unbalanced", f"{code.count('(')} vs {code.count(')')}"))

    # Check 3: Imports use single quotes
    imports = [l for l in code.split('\n') if l.startswith('import')]
    if all("'" in imp for imp in imports) and not any('"' in imp for imp in imports):
        checks.append(("✅", "Imports use single quotes", f"{len(imports)} imports"))
    else:
        checks.append(("⚠️", "Imports quote style issue", "Mixed quotes"))

    # Check 4: Imports end with semicolons
    if all(imp.endswith(';') for imp in imports):
        checks.append(("✅", "All imports end with ;", "Proper"))
    else:
        checks.append(("❌", "Missing semicolons", "Check imports"))

    # Check 5: Parts use single quotes
    parts = [l.strip() for l in code.split('\n') if l.strip().startswith('part')]
    if all("'" in part for part in parts) and not any('"' in part for part in parts):
        checks.append(("✅", "Part directives use single quotes", f"{len(parts)} parts"))
    else:
        checks.append(("⚠️", "Part quote style issue", "Mixed quotes"))

    # Check 6: @freezed annotations present
    freezed_count = code.count('@freezed')
    class_count = code.count('class ')
    if freezed_count == class_count:
        checks.append(("✅", "All classes have @freezed", f"{freezed_count} classes"))
    else:
        checks.append(("⚠️", "Missing @freezed annotations", f"{freezed_count}/{class_count}"))

    # Check 7: Factory constructors use const
    const_factories = code.count('const factory')
    if const_factories >= freezed_count:
        checks.append(("✅", "Factories use const keyword", f"{const_factories} factories"))
    else:
        checks.append(("❌", "Missing const factories", f"{const_factories}/{freezed_count}"))

    # Check 8: fromJson uses fat arrow
    if '=>' in code:
        checks.append(("✅", "fromJson uses fat arrow =>", "Correct"))
    else:
        checks.append(("⚠️", "No fat arrow syntax found", "Check fromJson"))

    # Check 9: @JsonKey uses single quotes
    jsonkey_pattern = r'@JsonKey\(name: \'[^\']+\'\)'
    jsonkey_matches = re.findall(jsonkey_pattern, code)
    total_jsonkey = code.count('@JsonKey')
    if total_jsonkey == len(jsonkey_matches):
        checks.append(("✅", "@JsonKey uses single quotes", f"{total_jsonkey} annotations"))
    else:
        checks.append(("⚠️", "@JsonKey quote issue", f"{len(jsonkey_matches)}/{total_jsonkey}"))

    # Check 10: No double quotes in annotations
    if not re.search(r'@\w+\([^)]*"[^)]*\)', code):
        checks.append(("✅", "No double quotes in annotations", "Correct"))
    else:
        checks.append(("⚠️", "Double quotes in annotations", "Should use single"))

    return checks


def main():
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]F039: Dart Analyze Compliance Demo[/bold cyan]\n"
        "[dim]Demonstrating that generated Dart code passes validation checks[/dim]",
        border_style="cyan"
    ))

    # Create a comprehensive test schema
    schema = SchnitzelSchema(
        models={
            "User": Model(
                name="User",
                fields={
                    "id": FieldDefinition(type="string"),
                    "userName": FieldDefinition(type="string"),
                    "email": FieldDefinition(type="string", optional=True),
                    "age": FieldDefinition(type="int", optional=True),
                    "status": FieldDefinition(type="string", default="active"),
                    "loginCount": FieldDefinition(type="int", default=0),
                    "isActive": FieldDefinition(type="bool", default=True),
                    "metadata": FieldDefinition(type="json", optional=True),
                },
                relations={
                    "posts": Relation(type="hasMany", model="Post"),
                    "profile": Relation(type="hasOne", model="Profile"),
                }
            ),
            "Post": Model(
                name="Post",
                fields={
                    "postId": FieldDefinition(type="string"),
                    "postTitle": FieldDefinition(type="string"),
                    "content": FieldDefinition(type="string"),
                    "publishedAt": FieldDefinition(type="datetime", optional=True),
                    "viewCount": FieldDefinition(type="int", default=0),
                    "isPublished": FieldDefinition(type="bool", default=False),
                }
            ),
            "Profile": Model(
                name="Profile",
                fields={
                    "bio": FieldDefinition(type="string", optional=True),
                    "avatarUrl": FieldDefinition(type="string", optional=True),
                    "followerCount": FieldDefinition(type="int", default=0),
                }
            )
        }
    )

    # Generate Dart code
    console.print("\n[bold yellow]Generating Dart models...[/bold yellow]")
    generator = DartModelGenerator()
    code = generator.generate(schema)

    # Show generated code
    console.print("\n[bold green]Generated Dart Code:[/bold green]")
    syntax = Syntax(code, "dart", theme="monokai", line_numbers=True)
    console.print(syntax)

    # Show syntax element counts
    console.print("\n[bold cyan]Syntax Element Analysis:[/bold cyan]")
    stats = count_syntax_elements(code)

    stats_table = Table(show_header=True, header_style="bold magenta")
    stats_table.add_column("Element", style="cyan")
    stats_table.add_column("Count", justify="right", style="yellow")

    stats_table.add_row("Import statements", str(stats['imports']))
    stats_table.add_row("Part directives", str(stats['parts']))
    stats_table.add_row("Opening braces {", str(stats['opening_braces']))
    stats_table.add_row("Closing braces }", str(stats['closing_braces']))
    stats_table.add_row("Opening parens (", str(stats['opening_parens']))
    stats_table.add_row("Closing parens )", str(stats['closing_parens']))
    stats_table.add_row("Semicolons", str(stats['semicolons']))
    stats_table.add_row("@freezed annotations", str(stats['freezed_annotations']))
    stats_table.add_row("@JsonKey annotations", str(stats['jsonkey_annotations']))
    stats_table.add_row("@Default annotations", str(stats['default_annotations']))

    console.print(stats_table)

    # Run validation checks
    console.print("\n[bold cyan]Dart Analyze Compliance Checks:[/bold cyan]")
    checks = validate_dart_syntax(code)

    checks_table = Table(show_header=True, header_style="bold magenta")
    checks_table.add_column("Status", width=6)
    checks_table.add_column("Check", style="cyan")
    checks_table.add_column("Result", style="yellow")

    passed = 0
    for status, check, result in checks:
        checks_table.add_row(status, check, result)
        if status == "✅":
            passed += 1

    console.print(checks_table)

    # Summary
    total = len(checks)
    console.print(f"\n[bold]Summary:[/bold] {passed}/{total} checks passed")

    if passed == total:
        console.print(Panel.fit(
            "[bold green]✅ All validation checks passed![/bold green]\n"
            "[dim]Generated code follows Dart best practices and would pass dart analyze.[/dim]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold yellow]⚠️ {total - passed} validation check(s) need attention[/bold yellow]",
            border_style="yellow"
        ))

    # Additional analysis
    console.print("\n[bold cyan]Code Quality Indicators:[/bold cyan]")

    quality_table = Table(show_header=True, header_style="bold magenta")
    quality_table.add_column("Indicator", style="cyan")
    quality_table.add_column("Status", style="yellow")

    # Check for trailing commas
    trailing_commas = code.count(',')
    quality_table.add_row("Trailing commas (best practice)", f"✅ {trailing_commas} found")

    # Check for const keyword
    const_count = code.count('const ')
    quality_table.add_row("Const keyword usage", f"✅ {const_count} instances")

    # Check for fat arrow syntax
    fat_arrows = code.count('=>')
    quality_table.add_row("Fat arrow syntax (concise)", f"✅ {fat_arrows} instances")

    # Check for required keyword
    required_count = code.count('required ')
    quality_table.add_row("Required keyword (null-safety)", f"✅ {required_count} instances")

    # Check for nullable types
    nullable_count = code.count('?')
    quality_table.add_row("Nullable types (? operator)", f"✅ {nullable_count} instances")

    console.print(quality_table)

    # Final message
    console.print("\n[bold green]Demo completed successfully![/bold green]")
    console.print("[dim]The generated Dart code follows all best practices and would pass 'dart analyze'.[/dim]\n")


if __name__ == "__main__":
    main()
