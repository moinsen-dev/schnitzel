"""Integration tests for Dart Event Client generation.

Test Requirements:
1. Creates event classes with fromJson/toJson
2. Creates SSE client with auto-reconnection
3. Creates WebSocket client with exponential backoff
4. Creates StreamControllers for BLoC integration
5. Handles type-safe event deserialization

This test validates the Dart event client generator creates production-ready
event handling code with proper reconnection logic and type safety.
"""

import tempfile
import os
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart.events import DartEventClientGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_dart_events_event_class_generation(temp_dir: Path) -> None:
    """Test that event classes are generated with fromJson/toJson (requirement 1)."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }
      status: { type: string }

events:
  order.placed:
    description: "New order placed"
    payload:
      order_id: uuid
      customer_id: uuid
      total: decimal
    channels:
      - websocket
      - redis

  inventory.low:
    description: "Inventory below threshold"
    payload:
      product_id: uuid
      current_stock: integer
      threshold: integer
    channels:
      - redis
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify event class generation
    assert "class OrderPlacedEvent" in dart_code
    assert "class InventoryLowEvent" in dart_code

    # Verify fields are generated
    assert "final String orderId;" in dart_code
    assert "final String customerId;" in dart_code
    assert "final double total;" in dart_code
    assert "final String productId;" in dart_code
    assert "final int currentStock;" in dart_code
    assert "final int threshold;" in dart_code

    # Verify fromJson factory
    assert "factory OrderPlacedEvent.fromJson(Map<String, dynamic> json)" in dart_code
    assert "orderId: json['order_id'] as String" in dart_code
    assert "customerId: json['customer_id'] as String" in dart_code
    assert "total: json['total'] as double" in dart_code

    # Verify toJson method
    assert "Map<String, dynamic> toJson()" in dart_code
    assert "'order_id': orderId" in dart_code
    assert "'customer_id': customerId" in dart_code
    assert "'total': total" in dart_code

    # Verify description comments
    assert "/// Event: order.placed" in dart_code or "Event: order.placed" in dart_code
    assert "/// Event: inventory.low" in dart_code or "Event: inventory.low" in dart_code


def test_dart_events_sse_client_generation(temp_dir: Path) -> None:
    """Test that SSE client is generated with auto-reconnection (requirement 2)."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }

streams:
  /orders/{id}/track:
    name: trackOrder
    description: "Real-time order status updates"
    type: sse
    auth: required
    events:
      - order.status_changed
      - order.location_updated
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify SSE client class
    assert "class SSEClient" in dart_code
    assert "SSE client for server-sent events" in dart_code

    # Verify required imports
    assert "import 'package:http/http.dart' as http;" in dart_code
    assert "import 'dart:async';" in dart_code
    assert "import 'dart:convert';" in dart_code

    # Verify client constructor with reconnection configuration
    assert "final Duration reconnectDelay;" in dart_code
    assert "reconnectDelay = const Duration(seconds: 3)" in dart_code

    # Verify stream method generation
    assert "Stream<Map<String, dynamic>> trackOrder(String id)" in dart_code

    # Verify StreamController usage
    assert "StreamController<Map<String, dynamic>>" in dart_code
    assert "controller = StreamController<Map<String, dynamic>>.broadcast();" in dart_code

    # Verify reconnection logic
    assert "Future.delayed(reconnectDelay, () => connect());" in dart_code
    assert "_isConnected[streamKey] = false;" in dart_code

    # Verify SSE-specific headers
    assert "request.headers['Accept'] = 'text/event-stream';" in dart_code
    assert "request.headers['Cache-Control'] = 'no-cache';" in dart_code

    # Verify authentication
    assert "if (authToken != null)" in dart_code
    assert "request.headers['Authorization'] = 'Bearer $authToken';" in dart_code

    # Verify SSE data parsing
    assert "if (line.startsWith('data: '))" in dart_code
    assert "final data = line.substring(6);" in dart_code
    assert "jsonDecode(data)" in dart_code

    # Verify dispose method for cleanup
    assert "void dispose()" in dart_code
    assert "controller.close();" in dart_code


def test_dart_events_websocket_client_generation(temp_dir: Path) -> None:
    """Test that WebSocket client is generated with exponential backoff (requirement 3)."""
    schema_content = """schnitzel: "1.0"

models:
  Match:
    fields:
      id: { type: uuid, primary: true }

streams:
  /matches/{match_id}/live:
    name: matchLiveStream
    description: "Real-time match state updates"
    type: websocket
    auth: required
    messages:
      - type: match_update
        payload:
          match_id: uuid
          status: string
      - type: player_action
        payload:
          player_id: uuid
          action: string
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify WebSocket client class
    assert "class WebSocketClient" in dart_code
    assert "WebSocket client for bidirectional communication" in dart_code

    # Verify required imports
    assert "import 'package:web_socket_channel/web_socket_channel.dart';" in dart_code
    assert "import 'package:web_socket_channel/io.dart';" in dart_code

    # Verify client constructor with reconnection and heartbeat
    assert "final Duration reconnectDelay;" in dart_code
    assert "final Duration heartbeatInterval;" in dart_code
    assert "reconnectDelay = const Duration(seconds: 3)" in dart_code
    assert "heartbeatInterval = const Duration(seconds: 30)" in dart_code

    # Verify exponential backoff implementation
    assert "_reconnectAttempts" in dart_code
    assert "final attempts = _reconnectAttempts[streamKey] ?? 0;" in dart_code
    assert "final delay = reconnectDelay * (1 << attempts.clamp(0, 5));" in dart_code
    assert "_reconnectAttempts[streamKey] = attempts + 1;" in dart_code

    # Verify stream method generation
    assert "Stream<Map<String, dynamic>> matchLiveStream(String matchId)" in dart_code

    # Verify WebSocket connection setup
    assert "IOWebSocketChannel.connect(uri)" in dart_code
    assert "final wsUrl = baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');" in dart_code

    # Verify heartbeat mechanism
    assert "Timer.periodic(heartbeatInterval" in dart_code
    assert "channel.sink.add(jsonEncode({'type': 'ping'}));" in dart_code
    assert "_heartbeatTimers[streamKey]?.cancel();" in dart_code

    # Verify authentication via query parameter
    assert "uri = uri.replace(queryParameters:" in dart_code
    assert "'token': authToken!" in dart_code

    # Verify send method for bidirectional communication
    assert "void send(String streamKey, Map<String, dynamic> message)" in dart_code
    assert "channel.sink.add(jsonEncode(message));" in dart_code

    # Verify dispose method with cleanup
    assert "void dispose()" in dart_code
    assert "channel?.sink.close();" in dart_code
    assert "timer?.cancel();" in dart_code

    # Verify reconnection on error and done
    assert "onError: (error)" in dart_code
    assert "onDone: ()" in dart_code
    assert "cancelOnError: false" in dart_code


def test_dart_events_stream_controllers_for_bloc(temp_dir: Path) -> None:
    """Test that StreamControllers are created for BLoC integration (requirement 4)."""
    schema_content = """schnitzel: "1.0"

models:
  Chat:
    fields:
      id: { type: uuid, primary: true }

events:
  message.received:
    payload:
      message_id: uuid
      content: string
    channels:
      - websocket

streams:
  /chat/{room_id}/stream:
    name: chatStream
    description: "Chat message stream"
    type: sse
    auth: required
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify StreamController declaration
    assert "StreamController<Map<String, dynamic>>" in dart_code

    # Verify broadcast controllers (multiple listeners for BLoC)
    assert ".broadcast()" in dart_code

    # Verify controller map for managing multiple streams
    assert "_controllers" in dart_code
    assert "Map<String, StreamController<Map<String, dynamic>>> _controllers" in dart_code

    # Verify stream reuse (returns existing stream if already subscribed)
    assert "if (_controllers.containsKey(streamKey))" in dart_code
    assert "return _controllers[streamKey]!.stream;" in dart_code

    # Verify controller registration
    assert "_controllers[streamKey] = controller;" in dart_code

    # Verify cleanup in dispose
    assert "for (var controller in _controllers.values)" in dart_code
    assert "_controllers.clear();" in dart_code

    # Verify data is added to controller
    assert "controller.add(json);" in dart_code


def test_dart_events_type_safe_deserialization(temp_dir: Path) -> None:
    """Test that event deserialization is type-safe (requirement 5)."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id: { type: uuid, primary: true }

events:
  product.created:
    payload:
      id: uuid
      name: string
      price: decimal
      quantity: integer
      is_active: bool
      tags: list<string>
    channels:
      - websocket
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify type mappings
    assert "final String id;" in dart_code
    assert "final String name;" in dart_code
    assert "final double price;" in dart_code
    assert "final int quantity;" in dart_code
    assert "final bool isActive;" in dart_code
    assert "final List<String> tags;" in dart_code

    # Verify type-safe fromJson with explicit casts
    assert "id: json['id'] as String" in dart_code
    assert "name: json['name'] as String" in dart_code
    assert "price: json['price'] as double" in dart_code
    assert "quantity: json['quantity'] as int" in dart_code
    assert "isActive: json['is_active'] as bool" in dart_code
    assert "tags: json['tags'] as List<String>" in dart_code

    # Verify camelCase conversion for Dart naming conventions
    assert "isActive" in dart_code  # Converted from is_active
    assert "'is_active': isActive" in dart_code  # Maps back to JSON key


def test_dart_events_empty_schema(temp_dir: Path) -> None:
    """Test that empty client is generated when no events or streams are defined."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id: { type: uuid, primary: true }
      name: { type: string }
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify empty client is generated
    assert "class EventClient" in dart_code
    assert "Empty event client - no events or streams defined in schema" in dart_code
    assert "EventClient();" in dart_code

    # Verify no SSE or WebSocket imports
    assert "package:http/http.dart" not in dart_code
    assert "package:web_socket_channel" not in dart_code


def test_dart_events_generate_to_file(temp_dir: Path) -> None:
    """Test that generate_to_file creates file with proper header."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }

events:
  order.placed:
    payload:
      order_id: uuid
    channels:
      - websocket
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    output_dir = temp_dir / "lib" / "generated"

    file_path, file_size = generator.generate_to_file(
        schema,
        output_dir,
        schema_source="schema.yaml"
    )

    # Verify file was created
    assert file_path.exists()
    assert file_path.name == "events.dart"
    assert file_size > 0

    # Verify header comment
    content = file_path.read_text()
    assert "Generated by Schnitzel Framework" in content
    assert "DO NOT EDIT - This file is auto-generated" in content
    assert "Source: schema.yaml" in content

    # Verify event class is in file
    assert "class OrderPlacedEvent" in content


def test_dart_events_dry_run_mode(temp_dir: Path) -> None:
    """Test that dry_run mode returns file info without writing."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id: { type: uuid, primary: true }

events:
  user.created:
    payload:
      user_id: uuid
    channels:
      - redis
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    output_dir = temp_dir / "lib" / "generated"

    file_path, file_size = generator.generate_to_file(
        schema,
        output_dir,
        dry_run=True
    )

    # Verify file info is returned
    assert file_path.name == "events.dart"
    assert file_size > 0

    # Verify file was NOT created
    assert not file_path.exists()
    assert not output_dir.exists()


def test_dart_events_path_parameters(temp_dir: Path) -> None:
    """Test that path parameters are correctly extracted and used."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }

streams:
  /orders/{order_id}/items/{item_id}/track:
    name: trackOrderItem
    description: "Track specific order item"
    type: sse
    auth: required
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify method signature includes all path parameters
    assert "Stream<Map<String, dynamic>> trackOrderItem(String orderId, String itemId)" in dart_code

    # Verify path is converted to Dart string interpolation
    assert "orders/$orderId/items/$itemId/track" in dart_code


def test_dart_events_connection_state_management(temp_dir: Path) -> None:
    """Test that connection state is properly managed."""
    schema_content = """schnitzel: "1.0"

models:
  Match:
    fields:
      id: { type: uuid, primary: true }

streams:
  /matches/{id}/live:
    name: matchStream
    type: websocket
    auth: required
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify connection state tracking
    assert "_isConnected" in dart_code
    assert "Map<String, bool> _isConnected" in dart_code

    # Verify connection state checks before operations
    assert "if (_isConnected[streamKey] == true)" in dart_code

    # Verify connection state updates
    assert "_isConnected[streamKey] = true;" in dart_code
    assert "_isConnected[streamKey] = false;" in dart_code

    # Verify prevents duplicate connections
    assert "if (_isConnected[streamKey] == true) return;" in dart_code


def test_dart_events_mixed_streams(temp_dir: Path) -> None:
    """Test that both SSE and WebSocket clients are generated when both are present."""
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id: { type: uuid, primary: true }

streams:
  /orders/{id}/track:
    name: trackOrder
    type: sse
    auth: required

  /chat/{room_id}:
    name: chatRoom
    type: websocket
    auth: required
"""

    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DartEventClientGenerator()
    dart_code = generator.generate(schema)

    # Verify both clients are generated
    assert "class SSEClient" in dart_code
    assert "class WebSocketClient" in dart_code

    # Verify both imports are included
    assert "import 'package:http/http.dart' as http;" in dart_code
    assert "import 'package:web_socket_channel/web_socket_channel.dart';" in dart_code

    # Verify both stream methods
    assert "Stream<Map<String, dynamic>> trackOrder(String id)" in dart_code
    assert "Stream<Map<String, dynamic>> chatRoom(String roomId)" in dart_code
