# Module 02 Real-time & Events - Implementation Summary

## Overview
Successfully implemented features F65-F102 for WebSocket handlers, event generators, stream generators, and job generators with comprehensive validation and error handling.

## Features Implemented

### WebSocket Handler Features (F65-F67, F102, F117)

#### F65: Message Acknowledgments
- **Location**: `/src/schnitzel/templates/python/websocket.py.j2`
- **Implementation**:
  - Added `message_id` field to `WebSocketMessage` model
  - Created new `AckMessage` model with `message_id`, `status`, and `timestamp`
  - Automatically sends acknowledgment after successfully processing messages when `message_id` is present
  - Sends error acknowledgment with `status="error"` on validation failures
- **Usage**: Clients can include `message_id` in their messages to receive confirmation of processing

#### F66: Request-Response Pattern
- **Location**: `/src/schnitzel/templates/python/websocket.py.j2`
- **Implementation**:
  - Added `correlation_id` field to `WebSocketMessage` model
  - Preserves `correlation_id` in response messages for request-response matching
  - Clients can track responses to specific requests using correlation IDs
- **Usage**: Send messages with `correlation_id` and match responses by the same ID

#### F67: Malformed JSON Handling
- **Location**: `/src/schnitzel/templates/python/websocket.py.j2`
- **Implementation**:
  - Enhanced `json.JSONDecodeError` exception handler
  - Sends helpful error message to client with format guidance
  - Connection remains open after JSON errors (uses `continue` instead of closing)
  - Subsequent valid messages are processed normally
- **Behavior**: Graceful error recovery without disconnecting clients

#### F117: Max Connections Per User
- **Location**: `/src/schnitzel/templates/python/websocket.py.j2`
- **Implementation**:
  - Added `max_connections_per_user` parameter to `ConnectionManager.__init__()`
  - Added `_user_connections` dict to track connections by user ID
  - Enhanced `connect()` method to accept `user_id` parameter
  - Automatically closes oldest connection when limit is exceeded
  - Properly cleans up user tracking in `disconnect()` method
- **Configuration**: Set via `manager = ConnectionManager(max_connections_per_user=5)`
- **Default**: `None` (unlimited connections)

### Event Generator Validation (F97, F101)

#### F97: Channel Name Validation
- **Location**: `/src/schnitzel/generators/python/events.py`
- **Implementation**:
  - Validates channel names against allowed list: `websocket`, `redis`, `redis-pubsub`, `sse`, `push`
  - Raises `ValueError` with helpful message listing valid channels
  - Validation occurs during event parsing in `_parse_event()` method
- **Error Example**: `"Event 'order.placed': Invalid channel 'kafka'. Valid channels are: websocket, redis, redis-pubsub, sse, push"`

#### F101: Payload Type Validation
- **Location**: `/src/schnitzel/generators/python/events.py`
- **Implementation**:
  - Validates all payload field types are known types from `PYTHON_TYPE_MAP`
  - Supports list types (e.g., `list<string>`)
  - Raises `ValueError` with helpful message listing valid types
  - Validation occurs during event parsing in `_parse_event()` method
- **Valid Types**: `string`, `str`, `text`, `uuid`, `int`, `integer`, `float`, `double`, `decimal`, `bool`, `boolean`, `datetime`, `date`, `json`, `vector`, `bytes`

### Stream Generator Validation (F98)

#### F98: Stream Type Validation
- **Location**: `/src/schnitzel/generators/python/streams.py`
- **Implementation**:
  - Validates stream type is either `sse` or `websocket`
  - Raises `ValueError` with helpful message listing valid types
  - Validation occurs during stream parsing in `_parse_stream()` method
- **Error Example**: `"Stream 'chat': Invalid stream type 'mqtt'. Valid types are: sse, websocket"`

### Job Generator Validation (F99, F100)

#### F99: Cron Expression Validation
- **Location**: `/src/schnitzel/generators/python/jobs.py`
- **Implementation**:
  - Validates cron expression has 5 or 6 space-separated fields
  - Checks each field contains only valid characters: digits, `*`, `-`, `,`, `/`
  - Provides helpful error messages with format examples
  - Validation occurs during job parsing in `_parse_job_definition()` method
- **Valid Format**: `'minute hour day month weekday'` or `'second minute hour day month weekday'`
- **Example**: `'0 9 * * *'` (daily at 9 AM) or `'*/5 * * * *'` (every 5 minutes)

#### F100: Timeout Format Validation
- **Location**: `/src/schnitzel/generators/python/jobs.py`
- **Implementation**:
  - Validates timeout is positive integer or string with valid unit
  - Supports units: `s` (seconds), `m` (minutes), `h` (hours), `d` (days)
  - Raises `ValueError` with helpful message and format examples
  - Validation occurs during job parsing in `_parse_job_definition()` method
- **Valid Formats**: `300` (integer seconds), `"30s"`, `"5m"`, `"1h"`, `"2d"`

#### F102: Message Type Uniqueness
- **Location**: `/src/schnitzel/generators/python/websocket.py`
- **Implementation**:
  - Validates all message types are unique within a WebSocket stream
  - Detects and reports duplicate message types
  - Raises `ValueError` listing duplicate types
  - Validation occurs during stream parsing in `_parse_stream()` method
- **Error Example**: `"Stream 'chat': Duplicate message types found: message, typing. Each message type must be unique within a stream."`

## New Files Created

### Validation Utilities Module
**File**: `/src/schnitzel/generators/validation_utils.py`

**Purpose**: Central validation utilities for all generators

**Functions**:
- `validate_channel_name(channel: str)` - Validate event channel names
- `validate_channels(channels: List[str])` - Validate list of channels
- `validate_stream_type(stream_type: str)` - Validate stream type
- `validate_cron_expression(cron_expr: str)` - Validate cron format
- `validate_timeout_format(timeout: str)` - Validate timeout format
- `validate_payload_type(field_type: str)` - Validate payload field type
- `validate_payload_types(payload: dict)` - Validate all payload types
- `validate_message_type_uniqueness(messages: List[dict])` - Check for duplicate message types

**Constants**:
- `VALID_CHANNELS` - List of allowed channel types
- `VALID_STREAM_TYPES` - List of allowed stream types
- `VALID_PAYLOAD_TYPES` - List of allowed payload field types

## Files Modified

### 1. WebSocket Template
**File**: `/src/schnitzel/templates/python/websocket.py.j2`

**Changes**:
- Added `message_id` and `correlation_id` fields to `WebSocketMessage` model
- Created new `AckMessage` model for acknowledgments
- Enhanced `ConnectionManager.__init__()` with `max_connections_per_user` parameter
- Added `_user_connections` tracking dict
- Updated `connect()` method to enforce connection limits per user
- Updated `disconnect()` method to clean up user connection tracking
- Added message acknowledgment logic after processing messages
- Enhanced JSON error handling to keep connection open
- Added correlation_id preservation in responses

### 2. Events Generator
**File**: `/src/schnitzel/generators/python/events.py`

**Changes**:
- Added import: `from schnitzel.generators.validation_utils import validate_channels, validate_payload_types`
- Updated `_parse_event()` docstring to indicate raises `ValueError`
- Added channel validation with try-except wrapper
- Added payload type validation with try-except wrapper
- Both validations provide context (event name) in error messages

### 3. Streams Generator
**File**: `/src/schnitzel/generators/python/streams.py`

**Changes**:
- Added import: `from schnitzel.generators.validation_utils import validate_stream_type`
- Updated `_parse_stream()` docstring to indicate raises `ValueError`
- Added stream type validation with try-except wrapper
- Validation provides context (stream name) in error messages

### 4. Jobs Generator
**File**: `/src/schnitzel/generators/python/jobs.py`

**Changes**:
- Added import: `from schnitzel.generators.validation_utils import validate_cron_expression, validate_timeout_format`
- Updated `_parse_job_definition()` docstring to indicate raises `ValueError`
- Added cron expression validation (only if schedule is provided)
- Added timeout format validation
- Both validations provide context (job name) in error messages

### 5. WebSocket Generator
**File**: `/src/schnitzel/generators/python/websocket.py`

**Changes**:
- Added import: `from schnitzel.generators.validation_utils import validate_message_type_uniqueness`
- Updated `_parse_stream()` docstring to indicate raises `ValueError`
- Added message type uniqueness validation
- Validation provides context (stream name) in error messages

## Error Handling Philosophy

All validation errors follow a consistent pattern:

1. **Early Detection**: Validation happens during code generation, not runtime
2. **Helpful Messages**: Errors include what went wrong and what's valid
3. **Context Preservation**: Error messages include entity name (event, stream, job)
4. **Graceful Failure**: WebSocket errors don't disconnect clients unnecessarily

## Example Error Messages

```
Event 'order.placed': Invalid channel 'kafka'. Valid channels are: websocket, redis, redis-pubsub, sse, push

Event 'payment.failed': Invalid type for field 'amount': Invalid payload field type 'money'. Valid types are: bool, boolean, bytes, date, datetime, ...

Stream 'notifications': Invalid stream type 'mqtt'. Valid types are: sse, websocket

Job 'sync_embeddings': Invalid cron expression 'every 5 minutes'. Expected 5 or 6 fields (found 3). Format: 'minute hour day month weekday'

Job 'cleanup_old_data': Invalid timeout unit 'w' in '2w'. Valid units are: s (seconds), m (minutes), h (hours), d (days)

Stream 'chat': Duplicate message types found: message, typing. Each message type must be unique within a stream.
```

## Testing Recommendations

### Unit Tests Needed
1. Test validation functions with valid and invalid inputs
2. Test WebSocket acknowledgment flow
3. Test request-response correlation_id matching
4. Test malformed JSON handling (connection stays open)
5. Test max connections enforcement
6. Test each generator's validation integration

### Integration Tests Needed
1. End-to-end WebSocket message flow with acks
2. End-to-end request-response pattern
3. Connection limit enforcement with multiple users
4. Schema validation with invalid configurations

## Usage Examples

### WebSocket with Acknowledgments and Correlation
```yaml
streams:
  chat:
    type: websocket
    path: /ws/chat/{room_id}
    messages:
      - type: message
        payload:
          content: string
          sender_id: uuid
```

Client sends:
```json
{
  "type": "message",
  "message_id": "msg-123",
  "correlation_id": "req-456",
  "data": {
    "content": "Hello!",
    "sender_id": "uuid-789"
  }
}
```

Client receives ack:
```json
{
  "type": "ack",
  "message_id": "msg-123",
  "status": "success",
  "timestamp": "2025-12-04T10:30:00Z"
}
```

Client receives response:
```json
{
  "type": "message",
  "correlation_id": "req-456",
  "data": { ... }
}
```

### Event with Validated Channels and Payload
```yaml
events:
  order.placed:
    channels:
      - websocket
      - redis-pubsub
    payload:
      order_id: uuid
      amount: decimal
      items: list<string>
```

### Job with Validated Cron and Timeout
```yaml
jobs:
  sync_embeddings:
    schedule: "0 */6 * * *"  # Every 6 hours
    workflow: SyncEmbeddingsWorkflow
    timeout: 30m
```

## Configuration

### Max Connections Per User
Update the generated `websocket.py` file:

```python
# Default (unlimited)
manager = ConnectionManager(max_connections_per_user=None)

# Limit to 5 connections per user
manager = ConnectionManager(max_connections_per_user=5)
```

Or configure via environment/settings:
```python
from app.config import settings
manager = ConnectionManager(max_connections_per_user=settings.WS_MAX_CONNECTIONS_PER_USER)
```

## Backward Compatibility

All changes are backward compatible:
- `message_id` and `correlation_id` are optional fields
- `max_connections_per_user` defaults to `None` (unlimited)
- Existing schemas without validation violations continue to work
- New validation only affects schemas with invalid configurations

## Next Steps

1. Add integration tests for all new features
2. Consider adding croniter library for more robust cron validation
3. Document WebSocket client patterns for acknowledgments and correlation
4. Add metrics for connection limits and rejected connections
5. Consider adding rate limiting per user alongside connection limits
