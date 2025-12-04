"""Logging utilities for Schnitzel CLI.

This module provides centralized logging configuration with support for verbose mode.
"""

import logging
import sys
from typing import Optional

# Global verbose flag
_verbose: bool = False

# Logger cache
_loggers: dict[str, logging.Logger] = {}


def set_verbose(verbose: bool) -> None:
    """Set the global verbose logging flag.

    When verbose is True, loggers will output DEBUG level messages.
    When verbose is False, loggers will output INFO level messages.

    Args:
        verbose: Whether to enable verbose logging
    """
    global _verbose
    _verbose = verbose

    # Update all existing loggers
    level = logging.DEBUG if verbose else logging.INFO
    for logger in _loggers.values():
        logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the specified name.

    The logger will respect the global verbose flag setting.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    # Set level based on verbose flag
    level = logging.DEBUG if _verbose else logging.INFO
    logger.setLevel(level)

    # Create console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)

        # Simple format for verbose mode
        formatter = logging.Formatter(
            fmt='[%(levelname)s] %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    # Cache the logger
    _loggers[name] = logger

    return logger


def is_verbose() -> bool:
    """Check if verbose mode is enabled.

    Returns:
        bool: True if verbose mode is enabled, False otherwise
    """
    return _verbose
