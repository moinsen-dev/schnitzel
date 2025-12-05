# Port Conflict Handling in Schnitzel CLI

## Overview

The Schnitzel CLI now gracefully detects and handles port conflicts when starting the serve command. This feature ensures that users receive helpful error messages and suggestions when the default port (8000) or a specified port is already in use.

## Features

### 1. Pre-Flight Port Check

Before starting the uvicorn server, the CLI checks if the specified port is available. This prevents the server from attempting to start and failing with a cryptic error message.

### 2. Helpful Error Messages

When a port conflict is detected, the CLI provides:

- Clear indication that a port is already in use
- Suggested alternative ports that are available
- Platform-specific commands to diagnose which process is using the port
- Instructions on how to start the server on a different port

### 3. Runtime Error Handling

If a port conflict occurs at runtime (race condition), the CLI catches the error and provides the same helpful messaging.

## Example Output

### Port Conflict Detected

```
Error: Port conflict detected

Port 8000 is already in use

Suggested alternatives:
  - Use port 8001: schnitzel serve start --port 8001
  - Other available ports: 8002, 8003

To check what's using port 8000:
  - On macOS/Linux: lsof -i :8000
  - On Windows: netstat -ano | findstr :8000
```

### Using Alternative Port

```bash
# Start on a different port
schnitzel serve start --port 8001

# Or let the system choose a random available port
schnitzel serve start --port 0
```

## Implementation Details

### Port Utilities (`schnitzel/utils/port.py`)

The implementation includes three main utility functions:

1. **`is_port_available(port, host)`**: Checks if a port is available for binding
2. **`find_available_port(start_port, host, max_attempts)`**: Finds the next available port
3. **`get_port_conflict_message(port, host, suggest_alternative)`**: Generates helpful error messages

### Integration with Serve Command

The `_start_uvicorn` function in `schnitzel/cli/commands/serve.py` now:

1. Checks port availability before starting uvicorn
2. Returns early with error code 1 if port is unavailable
3. Catches runtime OSError exceptions related to port binding
4. Displays helpful error messages in both cases

## Testing

The feature includes comprehensive tests:

- **Unit tests**: `tests/integration/test_port_conflict_handling.py`
  - Port availability detection
  - Finding alternative ports
  - Error message generation

- **Integration tests**: `tests/integration/test_serve_port_conflict.py`
  - Serve command integration
  - Pre-flight port checking
  - Runtime error handling
  - Message quality verification

Run the tests:

```bash
# All port conflict tests
uv run pytest tests/integration/test_port_conflict_handling.py -v
uv run pytest tests/integration/test_serve_port_conflict.py -v

# Specific test
uv run pytest tests/integration/test_port_conflict_handling.py::TestPortAvailability::test_is_port_available_in_use -v
```

## Usage Examples

### Default Port (8000)

```bash
# Start with default port
schnitzel serve start

# If port 8000 is busy, you'll see:
# Error: Port conflict detected
# Port 8000 is already in use
# Suggested alternatives: ...
```

### Custom Port

```bash
# Specify a custom port
schnitzel serve start --port 9000

# If port 9000 is busy, you'll get similar helpful messages
```

### Diagnosing Port Conflicts

```bash
# On macOS/Linux - find what's using port 8000
lsof -i :8000

# On Windows
netstat -ano | findstr :8000

# Kill the process (macOS/Linux)
kill -9 <PID>
```

## Benefits

1. **Better User Experience**: Clear, actionable error messages instead of cryptic stack traces
2. **Time Savings**: Users can quickly identify and resolve port conflicts
3. **Reduced Frustration**: Helpful suggestions guide users to solutions
4. **Production Ready**: Robust error handling prevents unexpected failures

## Technical Notes

### Port Range Validation

The utilities validate that ports are within the valid range (1-65535) and handle edge cases gracefully.

### Host Binding

The port check respects the host parameter:
- `0.0.0.0` (default): Bind to all interfaces
- `127.0.0.1`: Bind to localhost only
- Specific IP: Bind to that IP address

### Race Conditions

While the pre-flight check catches most conflicts, there's a small window for race conditions between the check and actual binding. The implementation handles this by catching runtime OSError exceptions.

## Future Enhancements

Potential improvements:

1. Auto-retry with alternative port (with user confirmation)
2. Port conflict resolution wizard
3. Integration with Docker port mapping conflicts
4. Historical port usage tracking

## Related Files

- `schnitzel-cli/src/schnitzel/utils/port.py` - Port utilities
- `schnitzel-cli/src/schnitzel/cli/commands/serve.py` - Serve command integration
- `schnitzel-cli/tests/integration/test_port_conflict_handling.py` - Unit tests
- `schnitzel-cli/tests/integration/test_serve_port_conflict.py` - Integration tests
