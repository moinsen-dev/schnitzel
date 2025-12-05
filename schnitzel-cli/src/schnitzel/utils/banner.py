"""ASCII banner utilities for Schnitzel CLI."""

from rich.console import Console


SCHNITZEL_BANNER = r"""
   ____     __          _ __           __
  / __/____/ /  ____   (_) /____ ___  / /
 _\ \ / __/ _ \/ __ \ / / __/_ // _ \/ /
/___/ \__/_//_/\___/_/_/\__//__/\___/_/
                    |_/
"""


def display_banner(console: Console | None = None) -> None:
    """Display the Schnitzel ASCII art banner.

    Args:
        console: Rich Console instance. If None, creates a new one.
    """
    if console is None:
        console = Console()

    console.print(SCHNITZEL_BANNER, style="bold cyan")
    console.print("Schema-driven full-stack code generator", style="dim")
    console.print()
