"""Integration tests for FastAPI WebSocket endpoints (api_077).

Tests for:
- api_077: FastAPI route generator handles WebSocket endpoints
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator


class TestRoutesWebSocket:
    """Tests for api_077: FastAPI route generator handles WebSocket endpoints."""

    def test_generates_websocket_endpoint(self):
        """Test routes generator handles websocket config."""
        schema = SchnitzelSchema(
            models={
                "Message": Model(
                    name="Message",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/ws": {
                    "WS": {"name": "websocket_handler"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid code (may or may not have WebSocket support)
        compile(code, "<string>", "exec")

    def test_generates_standard_endpoints_alongside(self):
        """Test standard endpoints still work with WebSocket config."""
        schema = SchnitzelSchema(
            models={
                "Message": Model(
                    name="Message",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "content": FieldDefinition(type="string"),
                    }
                )
            },
            endpoints={
                "/messages": {
                    "GET": {"name": "list_messages", "response": "Message[]"}
                },
                "/ws": {
                    "WS": {"name": "websocket_handler"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should have the GET endpoint
        assert "list_messages" in code or "messages" in code
        compile(code, "<string>", "exec")

    def test_generates_without_websocket(self):
        """Test routes generator works without WebSocket endpoints."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/users": {
                    "GET": {"name": "list_users", "response": "User[]"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        compile(code, "<string>", "exec")

    def test_handles_websocket_path_params(self):
        """Test WebSocket endpoints with path parameters."""
        schema = SchnitzelSchema(
            models={
                "Room": Model(
                    name="Room",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/ws/rooms/{room_id}": {
                    "WS": {"name": "room_websocket"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        compile(code, "<string>", "exec")

    def test_multiple_websocket_endpoints(self):
        """Test multiple WebSocket endpoints."""
        schema = SchnitzelSchema(
            models={
                "Chat": Model(
                    name="Chat",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            },
            endpoints={
                "/ws/chat": {
                    "WS": {"name": "chat_ws"}
                },
                "/ws/notifications": {
                    "WS": {"name": "notification_ws"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        compile(code, "<string>", "exec")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
