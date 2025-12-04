"""Schnitzel CLI - Schema-driven full-stack code generator.

This module serves as a compatibility layer for the CLI entry point.
The actual CLI implementation is in schnitzel.cli package.
"""

# Import the main function from the cli package (with KeyboardInterrupt handling)
from schnitzel.cli import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
