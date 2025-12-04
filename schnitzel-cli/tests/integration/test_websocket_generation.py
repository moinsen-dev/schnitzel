"""Integration tests for WebSocket Handler Generator.

Tests that the WebSocket generator correctly uses the Jinja2 template and produces
valid code with all required features.
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, StreamConfig, MessageConfig
from schnitzel.generators.python.websocket import WebSocketHandlerGenerator


class TestWebSocketGeneration:
    """Tests for WebSocket handler generation with Jinja2 template."""

    def test_generates_connection_manager_class(self):
        """Test that ConnectionManager class is generated."""
        schema = SchnitzelSchema(
            streams={
                "chat": StreamConfig(
                    name="chat",
                    type="websocket",
                    path="/ws/chat",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify ConnectionManager class exists
        assert "class ConnectionManager:" in code
        assert "def __init__(self):" in code
        assert "async def connect(" in code
        assert "def disconnect(" in code
        assert "async def broadcast(" in code
        assert "async def send_personal_message(" in code

        # Verify connection tracking
        assert "self.active_connections" in code
        assert "Dict[str, List[WebSocket]]" in code

    def test_generates_endpoint_with_message_routing(self):
        """Test that WebSocket endpoint includes message routing by type."""
        schema = SchnitzelSchema(
            streams={
                "chat": StreamConfig(
                    name="chat",
                    type="websocket",
                    path="/ws/chat/{room_id}",
                    auth="required",
                    messages=[
                        MessageConfig(
                            type="message",
                            payload={"content": "string", "sender_id": "uuid"}
                        ),
                        MessageConfig(
                            type="typing",
                            payload={"is_typing": "boolean"}
                        )
                    ]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify message routing
        assert 'message_type = message_data.get("type")' in code
        assert 'if message_type == "message":' in code
        assert 'elif message_type == "typing":' in code
        assert "# Route message based on type" in code

    def test_implements_heartbeat_mechanism(self):
        """Test that heartbeat mechanism is implemented with 30 second default."""
        schema = SchnitzelSchema(
            streams={
                "live": StreamConfig(
                    name="live",
                    type="websocket",
                    path="/ws/live",
                    auth="optional",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify heartbeat implementation
        assert "HeartbeatMessage" in code
        assert "async def _send_heartbeat(" in code
        assert "interval: int = 30" in code or "await asyncio.sleep(30)" in code or "30 seconds" in code.lower()
        assert "heartbeat" in code.lower()

    def test_handles_authentication_via_query_params(self):
        """Test that authentication is handled via query parameters."""
        schema = SchnitzelSchema(
            streams={
                "secure": StreamConfig(
                    name="secure",
                    type="websocket",
                    path="/ws/secure",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify auth handling - now supports both query param AND first message auth
        assert "token: Optional[str] = Query(" in code
        assert "Authentication token" in code
        assert "Authentication:" in code
        # Verify first-message auth support is documented
        assert "first message" in code.lower() or "first-message" in code.lower()

    def test_supports_first_message_authentication(self):
        """Test that first-message authentication is supported."""
        schema = SchnitzelSchema(
            streams={
                "secure": StreamConfig(
                    name="secure",
                    type="websocket",
                    path="/ws/secure",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify first-message auth support
        assert "AuthMessage" in code
        assert "class AuthMessage(BaseModel):" in code
        assert 'type: str = "auth"' in code
        assert "token: str" in code  # AuthMessage should have token field
        # Verify first message handling logic
        assert "if not authenticated:" in code
        assert "auth_data = await websocket.receive_text()" in code
        assert 'auth_message_data.get("type") != "auth"' in code
        assert "AuthMessage(**auth_message_data)" in code

    def test_supports_optional_authentication(self):
        """Test that optional authentication is supported."""
        schema = SchnitzelSchema(
            streams={
                "public": StreamConfig(
                    name="public",
                    type="websocket",
                    path="/ws/public",
                    auth="optional",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify optional auth
        assert "Optional[str] = Query(None" in code or "token: Optional[str]" in code

    def test_supports_room_channel_subscription(self):
        """Test that room/channel subscription is supported."""
        schema = SchnitzelSchema(
            streams={
                "chat": StreamConfig(
                    name="chat",
                    type="websocket",
                    path="/ws/chat/{room_id}",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify room support
        assert "room_id" in code
        assert "await manager.connect(websocket, room" in code
        assert 'room = f"chat_{room_id}"' in code or "room =" in code

    def test_handles_connection_errors_gracefully(self):
        """Test that WebSocketDisconnect is handled."""
        schema = SchnitzelSchema(
            streams={
                "notifications": StreamConfig(
                    name="notifications",
                    type="websocket",
                    path="/ws/notifications",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify error handling
        assert "except WebSocketDisconnect:" in code
        assert "manager.disconnect(websocket" in code
        assert "from fastapi import" in code and "WebSocketDisconnect" in code

    def test_validates_message_payload_schemas(self):
        """Test that Pydantic validation is used for message payloads."""
        schema = SchnitzelSchema(
            streams={
                "orders": StreamConfig(
                    name="orders",
                    type="websocket",
                    path="/ws/orders",
                    auth="required",
                    messages=[
                        MessageConfig(
                            type="place_order",
                            payload={
                                "product_id": "uuid",
                                "quantity": "integer",
                                "price": "decimal"
                            }
                        )
                    ]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify Pydantic validation
        assert "from pydantic import BaseModel" in code
        assert "ValidationError" in code
        assert "Payload" in code
        assert "class " in code and "Payload(BaseModel):" in code

    def test_generates_message_payload_models(self):
        """Test that payload models are generated for each message type."""
        schema = SchnitzelSchema(
            streams={
                "game": StreamConfig(
                    name="game",
                    type="websocket",
                    path="/ws/game/{game_id}",
                    auth="required",
                    messages=[
                        MessageConfig(
                            type="move",
                            payload={"x": "integer", "y": "integer"}
                        ),
                        MessageConfig(
                            type="chat",
                            payload={"message": "string"}
                        )
                    ]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify payload models
        assert "MovePayload" in code or "GameMovePayload" in code
        assert "ChatPayload" in code or "GameChatPayload" in code
        assert "x: int" in code
        assert "y: int" in code
        assert "message: str" in code

    def test_generated_code_compiles(self):
        """Test that generated code compiles successfully."""
        schema = SchnitzelSchema(
            streams={
                "feed": StreamConfig(
                    name="feed",
                    type="websocket",
                    path="/ws/feed/{user_id}",
                    auth="required",
                    messages=[
                        MessageConfig(
                            type="subscribe",
                            payload={"topics": "string"}
                        )
                    ]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify code compiles
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated WebSocket code has syntax errors: {e}")

    def test_empty_schema_generates_minimal_code(self):
        """Test that empty schema generates minimal valid code."""
        schema = SchnitzelSchema(streams={})

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify minimal code
        assert "from fastapi import APIRouter" in code
        assert "router = APIRouter()" in code
        assert code.count('\n') < 20  # Should be very short

    def test_non_websocket_streams_ignored(self):
        """Test that non-WebSocket streams are ignored."""
        schema = SchnitzelSchema(
            streams={
                "sse_stream": StreamConfig(
                    name="sse_stream",
                    type="sse",  # Not websocket
                    path="/stream/events",
                    auth="required"
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Should generate empty websocket file
        assert "from fastapi import APIRouter" in code
        assert "router = APIRouter()" in code
        assert "sse_stream" not in code.lower()

    def test_multiple_websocket_endpoints(self):
        """Test generating multiple WebSocket endpoints."""
        schema = SchnitzelSchema(
            streams={
                "chat": StreamConfig(
                    name="chat",
                    type="websocket",
                    path="/ws/chat",
                    auth="required",
                    messages=[]
                ),
                "notifications": StreamConfig(
                    name="notifications",
                    type="websocket",
                    path="/ws/notifications",
                    auth="optional",
                    messages=[]
                ),
                "feed": StreamConfig(
                    name="feed",
                    type="websocket",
                    path="/ws/feed/{user_id}",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify all endpoints
        assert '@router.websocket("/ws/chat")' in code
        assert '@router.websocket("/ws/notifications")' in code
        assert '@router.websocket("/ws/feed/{user_id}")' in code

    def test_path_parameters_with_uuid_type(self):
        """Test that path parameters with _id suffix get UUID type."""
        schema = SchnitzelSchema(
            streams={
                "room": StreamConfig(
                    name="room",
                    type="websocket",
                    path="/ws/rooms/{room_id}/users/{user_id}",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify UUID types for _id params
        assert "room_id: UUID" in code
        assert "user_id: UUID" in code
        assert "from uuid import UUID" in code

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        schema = SchnitzelSchema(
            streams={
                "test": StreamConfig(
                    name="test",
                    type="websocket",
                    path="/ws/test",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify logger
        assert "import logging" in code
        assert "logger = logging.getLogger(__name__)" in code
        assert "logger.info" in code or "logger.error" in code

    def test_json_error_handling(self):
        """Test that JSON parsing errors are handled."""
        schema = SchnitzelSchema(
            streams={
                "api": StreamConfig(
                    name="api",
                    type="websocket",
                    path="/ws/api",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify JSON error handling
        assert "json.loads(" in code
        assert "except json.JSONDecodeError:" in code or "JSONDecodeError" in code
        assert "Invalid JSON" in code

    @pytest.mark.skipif(
        subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
        reason="pyright not installed"
    )
    def test_generated_code_passes_type_checking(self):
        """Test that generated code passes pyright type checking."""
        schema = SchnitzelSchema(
            streams={
                "chat": StreamConfig(
                    name="chat",
                    type="websocket",
                    path="/ws/chat/{room_id}",
                    auth="required",
                    messages=[
                        MessageConfig(
                            type="message",
                            payload={"content": "string", "user_id": "uuid"}
                        )
                    ]
                )
            }
        )

        generator = WebSocketHandlerGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            ws_file, _ = generator.generate_to_file(schema, output_dir)

            # Create pyrightconfig.json
            pyright_config = output_dir / "pyrightconfig.json"
            pyright_config.write_text('{"reportMissingModuleSource": false, "reportMissingImports": false}')

            # Run pyright
            result = subprocess.run(
                ["pyright", str(ws_file)],
                capture_output=True,
                text=True,
                cwd=output_dir
            )

            # Verify no type errors (allow missing import warnings)
            assert result.returncode == 0 or "reportMissingImports" in result.stdout, \
                f"pyright should pass. Output: {result.stdout}\n{result.stderr}"

    def test_generate_to_file_creates_file(self):
        """Test that generate_to_file creates the output file."""
        schema = SchnitzelSchema(
            streams={
                "test": StreamConfig(
                    name="test",
                    type="websocket",
                    path="/ws/test",
                    auth="required",
                    messages=[]
                )
            }
        )

        generator = WebSocketHandlerGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            ws_file, file_size = generator.generate_to_file(schema, output_dir)

            # Verify file created
            assert ws_file.exists()
            assert file_size > 0
            assert ws_file.name == "websocket.py"

            # Verify header
            content = ws_file.read_text()
            assert "# Generated by Schnitzel Framework" in content
            assert "# DO NOT EDIT" in content

    def test_complex_message_payloads(self):
        """Test generation with complex message payloads."""
        schema = SchnitzelSchema(
            streams={
                "trading": StreamConfig(
                    name="trading",
                    type="websocket",
                    path="/ws/trading/{symbol}",
                    auth="required",
                    messages=[
                        MessageConfig(
                            type="order",
                            payload={
                                "symbol": "string",
                                "quantity": "integer",
                                "price": "decimal",
                                "order_type": "string",
                                "stop_loss": "decimal"
                            }
                        )
                    ]
                )
            }
        )

        generator = WebSocketHandlerGenerator()
        code = generator.generate(schema)

        # Verify all payload fields
        assert "symbol: str" in code
        assert "quantity: int" in code
        assert "price: " in code
        assert "order_type: str" in code
        assert "stop_loss: " in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
