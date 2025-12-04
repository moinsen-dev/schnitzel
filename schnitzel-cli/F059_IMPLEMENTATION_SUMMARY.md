# F059 Implementation Summary

**Feature**: Generate command handles generation errors gracefully

## Implementation Details

### Files Modified

1. **src/schnitzel/cli/commands/generate.py**
   - Added `_cleanup_files()` function to remove partially generated files on error
   - Updated `_generate_python()` to return file info dict and include error handling documentation
   - Updated `_generate_dart()` to return file info dict and include error handling documentation
   - Updated `_generate_docker()` to return file info dict and include error handling documentation
   - Wrapped file generation loop in try/except blocks to catch:
     - `PermissionError`: When write permission is denied
     - `IOError`/`OSError`: When I/O operations fail (disk full, etc.)
   - Added file tracking to enable cleanup on partial failure
   - Error messages show file paths and user-friendly descriptions
   - All error handlers call `_cleanup_files()` before exiting with code 1

### Key Features

1. **Error Handling**:
   - Catches `PermissionError` for permission issues
   - Catches `IOError` and `OSError` for file system errors
   - Shows user-friendly error messages with file paths
   - Returns exit code 1 on all errors

2. **Cleanup on Failure**:
   - Tracks all successfully generated files
   - If error occurs during multi-file generation, cleans up all partial files
   - Cleanup function handles errors gracefully (doesn't fail if cleanup fails)

3. **User-Friendly Error Messages**:
   - No raw Python tracebacks shown to users
   - Clear indication of which file failed
   - Helpful suggestions (e.g., "check disk space", "check permissions")
   - Consistent formatting with existing error messages

### Tests Created

**File**: tests/integration/test_cli_generate_errors_f059.py

All 7 tests passing:

1. ✅ `test_generate_handles_permission_error` - Verifies permission error handling
2. ✅ `test_generate_shows_error_file_path` - Ensures error messages include file paths
3. ✅ `test_generate_returns_exit_code_1_on_io_error` - Confirms proper exit codes
4. ✅ `test_generate_error_message_is_user_friendly` - No stack traces shown
5. ✅ `test_generate_cleans_up_on_partial_failure` - Partial files are removed on error
6. ✅ `test_generate_multiple_files_cleanup_on_second_failure` - Multi-file cleanup works
7. ✅ `test_generate_os_error_handling` - Generic OS errors handled properly

### Example Error Output

#### Permission Error:
```
✗ Permission denied:
  Cannot write to: /path/to/backend/app/models.py
  Please check file permissions and try again
Cleaned up partial file: /path/to/backend/app/models.py
```

#### I/O Error:
```
✗ I/O error during file generation:
  File: /path/to/backend/app/models.py
  Error: No space left on device
  Please check disk space and file system status
Cleaned up partial file: /path/to/backend/app/models.py
```

## Testing

Run the F059 tests:
```bash
uv run pytest tests/integration/test_cli_generate_errors_f059.py -v
```

All tests pass ✅

## Architecture Notes

### Error Handling Flow

1. **Generation Loop** - Wrapped in try/except
2. **File Tracking** - Each successful generation appends file info to `generated_files` list
3. **Error Occurs** - Exception caught by specific handler
4. **Cleanup** - `_cleanup_files()` removes all tracked files
5. **User Feedback** - Clear error message with file path
6. **Exit** - Returns exit code 1

### Design Decisions

1. **Return File Info**: Generator functions now return dict with file info instead of None
   - Enables tracking for cleanup
   - Provides size/type info for future features (dry-run mode uses this)

2. **Specific Exception Order**: PermissionError → IOError/OSError → Generic
   - Most specific first for precise error messages
   - Combined IOError and OSError (IOError is alias for OSError in Python 3)

3. **Cleanup on Error Only**: Don't delete successful files if user cancels
   - Only cleanup when actual I/O error occurs
   - Preserves partial work for debugging if needed

4. **Non-Failing Cleanup**: Cleanup errors are logged but don't cause additional failures
   - User already has main error, don't confuse with cleanup errors
   - Warning shown if cleanup fails

## Integration with Existing Code

- Maintains backward compatibility with existing tests
- Works with progress bars and dry-run mode
- Doesn't interfere with watch mode or other features
- Follows existing error handling patterns in the codebase

## Requirements Met

✅ 1. Catch and handle file write errors (permission denied, disk full, etc.)
✅ 2. Display user-friendly error messages
✅ 3. Return appropriate exit codes (1 for errors)
✅ 4. Don't leave partial files on error (cleanup on failure)
✅ 5. Show which file failed if error during multi-file generation

All requirements successfully implemented and tested.
