"""Validation utilities for Schnitzel generators.

Provides common validation functions for generators to ensure schema correctness
and provide helpful error messages.
"""

import re
from typing import List


# Valid channel types for events
VALID_CHANNELS = ["websocket", "redis", "redis-pubsub", "sse", "push"]

# Valid stream types
VALID_STREAM_TYPES = ["sse", "websocket"]

# Valid payload field types (from PYTHON_TYPE_MAP)
VALID_PAYLOAD_TYPES = [
    "string", "str", "text",
    "uuid",
    "int", "integer",
    "float", "double", "decimal",
    "bool", "boolean",
    "datetime", "date",
    "json",
    "vector",
    "bytes",
]


def validate_channel_name(channel: str) -> None:
    """Validate that a channel name is valid.

    Args:
        channel: The channel name to validate

    Raises:
        ValueError: If channel name is not valid
    """
    if channel not in VALID_CHANNELS:
        raise ValueError(
            f"Invalid channel '{channel}'. Valid channels are: {', '.join(VALID_CHANNELS)}"
        )


def validate_channels(channels: List[str]) -> None:
    """Validate that all channel names in a list are valid.

    Args:
        channels: List of channel names to validate

    Raises:
        ValueError: If any channel name is not valid
    """
    for channel in channels:
        validate_channel_name(channel)


def validate_stream_type(stream_type: str) -> None:
    """Validate that a stream type is valid.

    Args:
        stream_type: The stream type to validate

    Raises:
        ValueError: If stream type is not valid
    """
    if stream_type not in VALID_STREAM_TYPES:
        raise ValueError(
            f"Invalid stream type '{stream_type}'. Valid types are: {', '.join(VALID_STREAM_TYPES)}"
        )


def validate_cron_expression(cron_expr: str) -> None:
    """Validate that a cron expression is in valid format.

    This is a basic validation that checks the format has 5 or 6 fields
    (standard cron or with seconds). For full validation, croniter would be ideal
    but we want to avoid external dependencies.

    Args:
        cron_expr: The cron expression to validate

    Raises:
        ValueError: If cron expression format is invalid
    """
    if not cron_expr or not cron_expr.strip():
        raise ValueError("Cron expression cannot be empty")

    # Basic format validation: should have 5 or 6 space-separated fields
    parts = cron_expr.strip().split()

    if len(parts) not in [5, 6]:
        raise ValueError(
            f"Invalid cron expression '{cron_expr}'. "
            f"Expected 5 or 6 fields (found {len(parts)}). "
            f"Format: 'minute hour day month weekday' or 'second minute hour day month weekday'. "
            f"Example: '0 9 * * *' (daily at 9 AM) or '*/5 * * * *' (every 5 minutes)"
        )

    # Validate each field contains valid characters
    valid_chars = re.compile(r'^[\d\*\-,/]+$')
    for i, part in enumerate(parts):
        if not valid_chars.match(part):
            raise ValueError(
                f"Invalid cron expression '{cron_expr}'. "
                f"Field {i+1} ('{part}') contains invalid characters. "
                f"Only digits, *, -, , and / are allowed."
            )


def validate_timeout_format(timeout: str) -> None:
    """Validate that a timeout format is valid.

    Valid formats: integer seconds, or string with unit (30s, 5m, 1h, 2d)

    Args:
        timeout: The timeout value to validate

    Raises:
        ValueError: If timeout format is invalid
    """
    if isinstance(timeout, int):
        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")
        return

    if not isinstance(timeout, str):
        raise ValueError(
            f"Timeout must be string or int, got {type(timeout).__name__}"
        )

    timeout = timeout.strip()

    # Check if it's a plain integer string
    if timeout.isdigit():
        value = int(timeout)
        if value <= 0:
            raise ValueError(f"Timeout must be positive, got {value}")
        return

    # Check format: number + unit
    if len(timeout) < 2:
        raise ValueError(
            f"Invalid timeout format '{timeout}'. "
            f"Use format like '30s', '5m', '1h', '2d', or plain seconds as integer"
        )

    unit = timeout[-1].lower()
    number_part = timeout[:-1]

    # Validate unit
    if unit not in ['s', 'm', 'h', 'd']:
        raise ValueError(
            f"Invalid timeout unit '{unit}' in '{timeout}'. "
            f"Valid units are: s (seconds), m (minutes), h (hours), d (days). "
            f"Example: '30m', '1h', '2d'"
        )

    # Validate number part
    try:
        value = int(number_part)
        if value <= 0:
            raise ValueError(f"Timeout must be positive, got {value}{unit}")
    except ValueError:
        raise ValueError(
            f"Invalid timeout format '{timeout}'. "
            f"Number part '{number_part}' is not a valid integer"
        )


def validate_payload_type(field_type: str) -> None:
    """Validate that a payload field type is a known type.

    Args:
        field_type: The field type to validate

    Raises:
        ValueError: If field type is not recognized
    """
    # Extract base type from list types (e.g., "list<string>" -> "string")
    base_type = field_type.lower().strip()

    if base_type.startswith("list<") and base_type.endswith(">"):
        inner_type = base_type[5:-1].strip()
        validate_payload_type(inner_type)
        return

    if base_type not in VALID_PAYLOAD_TYPES:
        raise ValueError(
            f"Invalid payload field type '{field_type}'. "
            f"Valid types are: {', '.join(sorted(VALID_PAYLOAD_TYPES))}, "
            f"or list<type> for arrays"
        )


def validate_payload_types(payload: dict) -> None:
    """Validate all field types in a payload definition.

    Args:
        payload: Dictionary mapping field names to types

    Raises:
        ValueError: If any field type is not recognized
    """
    for field_name, field_def in payload.items():
        # Handle both string types and dict definitions
        if isinstance(field_def, dict):
            field_type = field_def.get("type", "string")
        elif isinstance(field_def, str):
            field_type = field_def
        else:
            continue

        try:
            validate_payload_type(field_type)
        except ValueError as e:
            raise ValueError(f"Invalid type for field '{field_name}': {e}") from e


def validate_message_type_uniqueness(messages: List[dict]) -> None:
    """Validate that message types are unique within a stream.

    Args:
        messages: List of message definitions

    Raises:
        ValueError: If duplicate message types are found
    """
    seen_types = set()
    duplicates = []

    for msg in messages:
        # Handle both MessageConfig objects and dicts
        msg_type = msg.type if hasattr(msg, 'type') else msg.get('type')

        if msg_type in seen_types:
            duplicates.append(msg_type)
        else:
            seen_types.add(msg_type)

    if duplicates:
        raise ValueError(
            f"Duplicate message types found: {', '.join(duplicates)}. "
            f"Each message type must be unique within a stream."
        )
