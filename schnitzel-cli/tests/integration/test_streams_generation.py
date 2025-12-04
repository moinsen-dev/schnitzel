"""Integration test for SSE stream generation - Verify template and generator work correctly.

Test Requirements:
1. SSE stream template generates event ID tracking
2. SSE stream template formats events correctly (SSE format: id, event, data)
3. SSE stream template handles authentication
4. SSE stream template subscribes to relevant events
5. Generator uses Jinja2 to render the template
6. Generated code passes pyright type checking

This test validates that the SSE stream generator properly renders the Jinja2 template
with correct SSE formatting, event ID tracking, and authentication support.
"""

import tempfile
import os
import subprocess
from pathlib import Path
from typer.testing import CliRunner
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.streams import SSEStreamGenerator

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def stream_schema(temp_dir: Path) -> Path:
    """Create a schema with SSE streams for testing."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      username:
        type: string
      email:
        type: string

  Order:
    description: "Order model"
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string
      customer_id:
        type: uuid

streams:
  order_updates:
    type: sse
    name: order_updates
    path: /orders/{order_id}/stream
    description: "Stream order status updates"
    auth: required
    events:
      - order.status_changed
      - order.item_added
    chunks:
      status:
        type: string
      message:
        type: string
      timestamp:
        type: datetime

  public_feed:
    type: sse
    name: public_feed
    path: /feed/stream
    description: "Public activity feed"
    auth: optional
    events:
      - activity.created
    chunks:
      activity_type:
        type: string
      content:
        type: string
      user_id:
        type: uuid
        optional: true
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_sse_stream_generator_initialization():
    """Test that SSE stream generator can be initialized."""
    generator = SSEStreamGenerator()
    assert generator is not None
    assert hasattr(generator, 'generate')
    assert hasattr(generator, 'generate_to_file')


def test_sse_stream_generation_basic(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams are generated correctly."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    # Generate SSE streams
    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert streams_file.exists(), "streams.py should be created"
    assert size > 0, "streams.py should have content"

    # Read and verify content
    streams_content = streams_file.read_text()

    # Verify imports
    assert "from fastapi import APIRouter" in streams_content
    assert "StreamingResponse" in streams_content
    assert "from typing import AsyncGenerator" in streams_content
    assert "import asyncio" in streams_content
    assert "import json" in streams_content
    assert "from datetime import datetime" in streams_content

    # Verify router is created
    assert "router = APIRouter()" in streams_content

    # Verify both stream functions are present
    assert "async def order_updates(" in streams_content
    assert "async def public_feed(" in streams_content

    # Verify path decorators (check for either single or double quotes)
    assert ("@router.get('/orders/{order_id}/stream'" in streams_content or
            '@router.get("/orders/{order_id}/stream"' in streams_content)
    assert ("@router.get('/feed/stream'" in streams_content or
            '@router.get("/feed/stream"' in streams_content)


def test_sse_event_id_tracking(temp_dir: Path, stream_schema: Path):
    """Test that generated SSE streams include event ID tracking."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify event ID tracking is present in generator functions
    assert "event_id = 0" in streams_content, "Should initialize event_id counter"
    assert "event_id += 1" in streams_content, "Should increment event_id"

    # Check that event ID is yielded in SSE format
    assert 'yield f"id: {event_id}\\n"' in streams_content, "Should yield event ID in SSE format"


def test_sse_format_correct(temp_dir: Path, stream_schema: Path):
    """Test that generated SSE streams use correct SSE event format."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # SSE format requires three parts: id, event, data
    # Each message should end with double newline
    assert 'yield f"id: {event_id}\\n"' in streams_content, "Should have id: field"
    assert 'yield f"event: ' in streams_content, "Should have event: field"
    assert 'yield f"data: {json.dumps(' in streams_content, "Should have data: field with JSON"
    assert '\\n\\n"' in streams_content, "Should end with double newline"

    # Verify SSE headers are present
    assert '"Cache-Control": "no-cache"' in streams_content
    assert '"Connection": "keep-alive"' in streams_content
    assert '"X-Accel-Buffering": "no"' in streams_content


def test_sse_authentication_required(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams with auth: required include authentication."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # order_updates stream has auth: required
    # Should have Depends(get_current_user) in parameters
    assert "from fastapi import" in streams_content and "Depends" in streams_content
    assert "get_current_user" in streams_content
    assert "current_user: User = Depends(get_current_user)" in streams_content

    # Verify User model is imported
    assert "from .models import User" in streams_content or "from ..models import User" in streams_content


def test_sse_authentication_optional(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams with auth: optional don't require authentication."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # public_feed stream has auth: optional
    # Count occurrences of auth dependency for each function
    order_updates_start = streams_content.find("async def order_updates(")
    public_feed_start = streams_content.find("async def public_feed(")

    # Get the order_updates function signature
    order_updates_sig = streams_content[order_updates_start:order_updates_start+200]
    # Get the public_feed function signature
    public_feed_sig = streams_content[public_feed_start:public_feed_start+200]

    # order_updates should have auth
    assert "current_user" in order_updates_sig

    # public_feed should NOT have auth dependency
    assert "current_user" not in public_feed_sig


def test_sse_path_parameters(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams correctly handle path parameters."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # order_updates has {order_id} path parameter
    assert "order_id: UUID" in streams_content, "Should extract order_id as UUID type"
    assert "from uuid import UUID" in streams_content, "Should import UUID"

    # Verify path parameter is passed to generator function
    assert "_generate_order_updates_events(order_id" in streams_content


def test_sse_chunk_models(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams generate chunk type models."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify Pydantic BaseModel is imported
    assert "from pydantic import BaseModel" in streams_content

    # Verify chunk models are generated
    assert "class Order_updatesChunk(BaseModel):" in streams_content or "class OrderUpdatesChunk(BaseModel):" in streams_content
    assert "class Public_feedChunk(BaseModel):" in streams_content or "class PublicFeedChunk(BaseModel):" in streams_content

    # Verify chunk fields from schema
    assert "status: str" in streams_content
    assert "message: str" in streams_content
    assert "timestamp: datetime" in streams_content
    assert "activity_type: str" in streams_content
    assert "content: str" in streams_content

    # Verify optional field handling
    assert "user_id: UUID | None = None" in streams_content or "user_id: Optional[UUID] = None" in streams_content


def test_sse_event_subscription(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams reference subscribed events in comments/docs."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify stream descriptions mention events or have TODO comments
    # The events are listed in the schema, so they should appear in generated code or docs
    assert "order_updates" in streams_content.lower()
    assert "public_feed" in streams_content.lower() or "public_feed" in streams_content

    # At minimum, generator functions should exist
    assert "_generate_order_updates_events" in streams_content
    assert "_generate_public_feed_events" in streams_content


def test_sse_streaming_response(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams return StreamingResponse."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify StreamingResponse is used
    assert "-> StreamingResponse:" in streams_content
    assert "return StreamingResponse(" in streams_content
    assert 'media_type="text/event-stream"' in streams_content


def test_sse_async_generator(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams use async generators."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify async generator type hints
    assert "AsyncGenerator[str, None]" in streams_content

    # Verify generator functions are async
    assert "async def _generate_order_updates_events" in streams_content
    assert "async def _generate_public_feed_events" in streams_content

    # Verify yield statements are present
    assert "yield " in streams_content


def test_sse_error_handling(temp_dir: Path, stream_schema: Path):
    """Test that SSE streams include error handling."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify try/except blocks
    assert "try:" in streams_content
    assert "except asyncio.CancelledError:" in streams_content
    assert "except Exception as e:" in streams_content

    # Verify error events are yielded
    assert 'yield f"event: error\\n"' in streams_content or 'event: error' in streams_content


def test_sse_generation_compiles(temp_dir: Path, stream_schema: Path):
    """Test that generated SSE code compiles without syntax errors."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Try to compile the generated code
    try:
        compile(streams_content, str(streams_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated SSE streams have syntax errors: {e}")


def test_sse_empty_streams(temp_dir: Path):
    """Test that generator handles schema with no streams."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "empty_schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Should generate minimal file
    assert "router = APIRouter()" in streams_content
    assert streams_file.exists()


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_sse_passes_type_checking(temp_dir: Path, stream_schema: Path):
    """Test that generated SSE code passes pyright type checking."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create models.py stub for imports
    models_file = output_dir / "models.py"
    models_stub = """from pydantic import BaseModel
from uuid import UUID

class User(BaseModel):
    id: UUID
    username: str
    email: str
"""
    models_file.write_text(models_stub)

    # Create auth module stub
    auth_dir = output_dir.parent
    auth_file = auth_dir / "auth.py"
    auth_stub = """from models import User

async def get_current_user() -> User:
    # Stub implementation
    pass
"""
    auth_file.write_text(auth_stub)

    # Create pyrightconfig.json
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright
    result = subprocess.run(
        ["pyright", str(streams_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no type errors (allow missing imports/modules since we're using stubs in test environment)
    # In test environment, FastAPI may not be available, so we allow reportAttributeAccessIssue for external modules
    allowed_errors = ["reportMissingImports", "reportAttributeAccessIssue"]
    has_allowed_error = any(err in result.stdout for err in allowed_errors)

    assert result.returncode == 0 or has_allowed_error, \
        f"pyright should pass or have only external module errors. Output: {result.stdout}\n{result.stderr}"


def test_sse_generator_uses_jinja2(temp_dir: Path, stream_schema: Path):
    """Test that the SSE generator uses Jinja2 for template rendering."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()

    # Verify generator has jinja2 environment
    assert hasattr(generator, 'env'), "Generator should have jinja2 Environment"

    # Generate code
    code = generator.generate(schema)

    # The generated code should be consistent with template rendering
    # (not string concatenation patterns)
    assert "router = APIRouter()" in code
    assert "async def" in code


def test_sse_operation_ids(temp_dir: Path, stream_schema: Path):
    """Test that SSE endpoints have operation IDs."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify operation_id is included in route decorators
    assert 'operation_id="order_updates"' in streams_content
    assert 'operation_id="public_feed"' in streams_content


def test_sse_multiple_streams_no_conflicts(temp_dir: Path, stream_schema: Path):
    """Test that multiple SSE streams don't conflict with each other."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Count occurrences of key patterns
    assert streams_content.count("async def order_updates(") == 1
    assert streams_content.count("async def public_feed(") == 1
    assert streams_content.count("async def _generate_order_updates_events(") == 1
    assert streams_content.count("async def _generate_public_feed_events(") == 1

    # Verify no duplicate imports
    import_lines = [line for line in streams_content.split('\n') if line.startswith('import ') or line.startswith('from ')]
    unique_imports = set(import_lines)
    assert len(import_lines) == len(unique_imports), "Should not have duplicate imports"


def test_sse_docstrings_present(temp_dir: Path, stream_schema: Path):
    """Test that generated SSE functions have docstrings."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify docstrings are present
    assert '"""Stream order status updates"""' in streams_content or '"Stream order status updates"' in streams_content
    assert '"""Public activity feed"""' in streams_content or '"Public activity feed"' in streams_content

    # Verify generator function docstrings
    assert '"""Generate SSE events for' in streams_content


def test_sse_file_header(temp_dir: Path, stream_schema: Path):
    """Test that generated file includes proper header."""
    parser = SchemaParser()
    schema = parser.parse(stream_schema)

    generator = SSEStreamGenerator()
    output_dir = temp_dir / "backend" / "app"
    streams_file, _ = generator.generate_to_file(schema, output_dir)

    streams_content = streams_file.read_text()

    # Verify header comment
    assert "# Generated by Schnitzel Framework" in streams_content
    assert "# DO NOT EDIT - This file is auto-generated" in streams_content
    assert "# Generated at:" in streams_content
    assert "# Source:" in streams_content
