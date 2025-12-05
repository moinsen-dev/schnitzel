"""Dart event client generator for Schnitzel schemas.

Generates SSE and WebSocket event subscription clients with automatic reconnection.
"""

from datetime import datetime
from pathlib import Path
from typing import Set
from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, EventConfig, StreamConfig, DART_TYPE_MAP


class DartEventClientGenerator:
    """Generates Dart event clients from Schnitzel schemas."""

    def __init__(self):
        """Initialize the Dart event client generator."""
        self.imports: Set[str] = set()

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case or dot.notation to lowerCamelCase.

        Args:
            name: The name to convert (may be snake_case or dot.notation)

        Returns:
            lowerCamelCase version of the name

        Examples:
            user_id -> userId
            order.placed -> orderPlaced
            user.profile_updated -> userProfileUpdated
        """
        # Replace dots with underscores first
        name = name.replace('.', '_')

        # If no underscores, already camelCase or single word
        if '_' not in name:
            return name

        # Split by underscore and capitalize each part except the first
        parts = name.split('_')
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case or dot.notation to PascalCase.

        Args:
            name: The name to convert

        Returns:
            PascalCase version of the name

        Examples:
            user_id -> UserId
            order.placed -> OrderPlaced
        """
        camel = self._to_camel_case(name)
        return camel[0].upper() + camel[1:] if camel else camel

    def _get_dart_type(self, schema_type: str) -> str:
        """Map schema type to Dart type.

        Args:
            schema_type: Type from schema (e.g., "string", "int", "uuid")

        Returns:
            Dart type string (e.g., "String", "int", "DateTime")
        """
        schema_type_lower = schema_type.lower()

        # Handle list types: list<string> -> List<String>
        if schema_type_lower.startswith("list<") and schema_type_lower.endswith(">"):
            inner_type = schema_type_lower[5:-1].strip()
            inner_dart_type = DART_TYPE_MAP.get(inner_type, inner_type.capitalize())
            return f"List<{inner_dart_type}>"

        # Handle standard types
        return DART_TYPE_MAP.get(schema_type_lower, schema_type)

    def generate(self, schema: SchnitzelSchema) -> str:
        """Generate Dart event client from a schema.

        Args:
            schema: The Schnitzel schema to generate event client from

        Returns:
            Generated Dart code as a string
        """
        self.imports = set()

        # Check if schema has events or streams
        has_events = schema.events and len(schema.events) > 0
        has_sse_streams = False
        has_websocket_streams = False

        if schema.streams:
            for stream in schema.streams.values():
                if stream.type == "sse":
                    has_sse_streams = True
                elif stream.type == "websocket":
                    has_websocket_streams = True

        # If no events or streams, return empty client
        if not has_events and not has_sse_streams and not has_websocket_streams:
            return self._generate_empty_client()

        # Add base imports
        self.imports.add("import 'dart:async';")
        self.imports.add("import 'dart:convert';")

        if has_sse_streams:
            self.imports.add("import 'package:http/http.dart' as http;")

        if has_websocket_streams:
            self.imports.add("import 'package:web_socket_channel/web_socket_channel.dart';")
            self.imports.add("import 'package:web_socket_channel/io.dart';")

        # Generate event type classes for events section
        event_classes = []
        if has_events:
            for event_name, event_config in schema.events.items():
                event_class = self._generate_event_class(event_name, event_config)
                event_classes.append(event_class)

        # Generate SSE client if needed
        sse_client_code = ""
        if has_sse_streams:
            sse_client_code = self._generate_sse_client(schema)

        # Generate WebSocket client if needed
        websocket_client_code = ""
        if has_websocket_streams:
            websocket_client_code = self._generate_websocket_client(schema)

        # Build final code
        imports_code = "\n".join(sorted(self.imports))
        events_code = "\n\n".join(event_classes) if event_classes else ""

        # Combine all sections
        sections = [imports_code]
        if events_code:
            sections.append(events_code)
        if sse_client_code:
            sections.append(sse_client_code)
        if websocket_client_code:
            sections.append(websocket_client_code)

        return "\n\n".join(sections) + "\n"

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate Dart event client and write it to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the client to 'events.dart' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate event client from
            output_dir: Directory where events.dart should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to events.dart file, size in bytes)

        Example:
            >>> generator = DartEventClientGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "packages/shared/lib/generated")
            >>> print(f"Event client written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the event client code
        client_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        # Combine header with generated code
        full_code = header + client_code

        # Calculate file path and size
        client_file = output_path / "events.dart"
        file_size = len(full_code.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return client_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Warn if file already exists
        if client_file.exists():
            print(f"Warning: Overwriting existing file: {client_file}")

        client_file.write_text(full_code, encoding="utf-8")

        return client_file, file_size

    def _generate_empty_client(self) -> str:
        """Generate a minimal event client when no events or streams are defined."""
        self.imports.add("import 'dart:async';")
        imports_code = "\n".join(sorted(self.imports))

        return f"""{imports_code}

/// Empty event client - no events or streams defined in schema
class EventClient {{
  EventClient();
}}
"""

    def _generate_event_class(self, event_name: str, event_config: EventConfig) -> str:
        """Generate a Dart class for an event type.

        Args:
            event_name: Name of the event (e.g., "order.placed")
            event_config: Event configuration from schema

        Returns:
            Dart class definition
        """
        class_name = self._to_pascal_case(event_name) + "Event"

        # Generate fields from payload
        fields = []
        constructor_params = []
        from_json_assignments = []
        to_json_entries = []

        if event_config.payload:
            for field_name, field_type in event_config.payload.items():
                dart_type = self._get_dart_type(field_type)
                dart_field_name = self._to_camel_case(field_name)

                fields.append(f"  final {dart_type} {dart_field_name};")
                constructor_params.append(f"required this.{dart_field_name}")
                from_json_assignments.append(
                    f"      {dart_field_name}: json['{field_name}'] as {dart_type},"
                )
                to_json_entries.append(f"      '{field_name}': {dart_field_name},")

        # Build constructor
        if constructor_params:
            constructor = f"  {class_name}({{\n    {',\n    '.join(constructor_params)},\n  }});"
        else:
            constructor = f"  {class_name}();"

        # Build fromJson factory
        if from_json_assignments:
            from_json = f"""  factory {class_name}.fromJson(Map<String, dynamic> json) {{
    return {class_name}(
{chr(10).join(from_json_assignments)}
    );
  }}"""
        else:
            from_json = f"""  factory {class_name}.fromJson(Map<String, dynamic> json) {{
    return {class_name}();
  }}"""

        # Build toJson method
        if to_json_entries:
            to_json = f"""  Map<String, dynamic> toJson() {{
    return {{
{chr(10).join(to_json_entries)}
    }};
  }}"""
        else:
            to_json = """  Map<String, dynamic> toJson() {
    return {};
  }"""

        # Build class
        fields_section = "\n".join(fields) if fields else ""

        return f"""/// Event: {event_name}
class {class_name} {{
{fields_section}

{constructor}

{from_json}

{to_json}
}}"""

    def _generate_sse_client(self, schema: SchnitzelSchema) -> str:
        """Generate SSE client for SSE streams.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dart SSE client class code
        """
        # Collect SSE streams
        sse_streams = []
        if schema.streams:
            for stream_name, stream_config in schema.streams.items():
                if stream_config.type == "sse":
                    sse_streams.append((stream_name, stream_config))

        if not sse_streams:
            return ""

        # Generate stream methods
        stream_methods = []
        for stream_name, stream_config in sse_streams:
            method = self._generate_sse_stream_method(stream_name, stream_config)
            stream_methods.append(method)

        stream_methods_code = "\n\n".join(stream_methods)

        return f"""/// SSE client for server-sent events
class SSEClient {{
  final String baseUrl;
  final String? authToken;
  final Duration reconnectDelay;

  http.Client? _httpClient;
  final Map<String, StreamController<Map<String, dynamic>>> _controllers = {{}};
  final Map<String, bool> _isConnected = {{}};

  SSEClient({{
    required this.baseUrl,
    this.authToken,
    this.reconnectDelay = const Duration(seconds: 3),
  }}) {{
    _httpClient = http.Client();
  }}

  void dispose() {{
    for (var controller in _controllers.values) {{
      controller.close();
    }}
    _controllers.clear();
    _httpClient?.close();
    _httpClient = null;
  }}

{self._indent(stream_methods_code, 2)}
}}"""

    def _generate_sse_stream_method(
        self, stream_name: str, stream_config: StreamConfig
    ) -> str:
        """Generate a method for subscribing to an SSE stream.

        Args:
            stream_name: Name of the stream (path key from schema)
            stream_config: Stream configuration

        Returns:
            Dart method code
        """
        method_name = self._to_camel_case(stream_config.name)

        # Extract path parameters
        path_params = self._extract_path_params(stream_config.path)

        # Build method parameters (convert to camelCase for Dart)
        params = []
        for param in path_params:
            camel_param = self._to_camel_case(param)
            params.append(f"String {camel_param}")

        params_str = ", ".join(params) if params else ""

        # Convert path to Dart string interpolation
        dart_path = self._convert_path_to_dart(stream_config.path)

        return f"""Stream<Map<String, dynamic>> {method_name}({params_str}) {{
  final streamKey = '{stream_config.name}';

  if (_controllers.containsKey(streamKey)) {{
    return _controllers[streamKey]!.stream;
  }}

  final controller = StreamController<Map<String, dynamic>>.broadcast();
  _controllers[streamKey] = controller;

  Future<void> connect() async {{
    if (_isConnected[streamKey] == true) return;
    _isConnected[streamKey] = true;

    try {{
      final uri = Uri.parse('$baseUrl/{dart_path}');
      final request = http.Request('GET', uri);

      if (authToken != null) {{
        request.headers['Authorization'] = 'Bearer $authToken';
      }}
      request.headers['Accept'] = 'text/event-stream';
      request.headers['Cache-Control'] = 'no-cache';

      final response = await _httpClient!.send(request);

      if (response.statusCode != 200) {{
        throw Exception('SSE connection failed: ${{response.statusCode}}');
      }}

      response.stream
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen(
            (line) {{
              if (line.startsWith('data: ')) {{
                final data = line.substring(6);
                try {{
                  final json = jsonDecode(data) as Map<String, dynamic>;
                  controller.add(json);
                }} catch (e) {{
                  // Skip malformed JSON
                }}
              }}
            }},
            onError: (error) {{
              _isConnected[streamKey] = false;
              // Reconnect after delay
              Future.delayed(reconnectDelay, () => connect());
            }},
            onDone: () {{
              _isConnected[streamKey] = false;
              // Reconnect after delay
              Future.delayed(reconnectDelay, () => connect());
            }},
            cancelOnError: false,
          );
    }} catch (e) {{
      _isConnected[streamKey] = false;
      // Reconnect after delay
      Future.delayed(reconnectDelay, () => connect());
    }}
  }}

  connect();
  return controller.stream;
}}"""

    def _generate_websocket_client(self, schema: SchnitzelSchema) -> str:
        """Generate WebSocket client for WebSocket streams.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dart WebSocket client class code
        """
        # Collect WebSocket streams
        ws_streams = []
        if schema.streams:
            for stream_name, stream_config in schema.streams.items():
                if stream_config.type == "websocket":
                    ws_streams.append((stream_name, stream_config))

        if not ws_streams:
            return ""

        # Generate connection methods
        connection_methods = []
        for stream_name, stream_config in ws_streams:
            method = self._generate_websocket_connection_method(stream_name, stream_config)
            connection_methods.append(method)

        connection_methods_code = "\n\n".join(connection_methods)

        return f"""/// WebSocket client for bidirectional communication
class WebSocketClient {{
  final String baseUrl;
  final String? authToken;
  final Duration reconnectDelay;
  final Duration heartbeatInterval;

  final Map<String, WebSocketChannel?> _channels = {{}};
  final Map<String, StreamController<Map<String, dynamic>>> _controllers = {{}};
  final Map<String, Timer?> _heartbeatTimers = {{}};
  final Map<String, bool> _isConnected = {{}};
  final Map<String, int> _reconnectAttempts = {{}};

  WebSocketClient({{
    required this.baseUrl,
    this.authToken,
    this.reconnectDelay = const Duration(seconds: 3),
    this.heartbeatInterval = const Duration(seconds: 30),
  }});

  void dispose() {{
    for (var channel in _channels.values) {{
      channel?.sink.close();
    }}
    _channels.clear();

    for (var controller in _controllers.values) {{
      controller.close();
    }}
    _controllers.clear();

    for (var timer in _heartbeatTimers.values) {{
      timer?.cancel();
    }}
    _heartbeatTimers.clear();
  }}

  void send(String streamKey, Map<String, dynamic> message) {{
    final channel = _channels[streamKey];
    if (channel != null && _isConnected[streamKey] == true) {{
      channel.sink.add(jsonEncode(message));
    }}
  }}

{self._indent(connection_methods_code, 2)}
}}"""

    def _generate_websocket_connection_method(
        self, stream_name: str, stream_config: StreamConfig
    ) -> str:
        """Generate a method for connecting to a WebSocket stream.

        Args:
            stream_name: Name of the stream (path key from schema)
            stream_config: Stream configuration

        Returns:
            Dart method code
        """
        method_name = self._to_camel_case(stream_config.name)

        # Extract path parameters
        path_params = self._extract_path_params(stream_config.path)

        # Build method parameters (convert to camelCase for Dart)
        params = []
        for param in path_params:
            camel_param = self._to_camel_case(param)
            params.append(f"String {camel_param}")

        params_str = ", ".join(params) if params else ""

        # Convert path to Dart string interpolation and handle ws:// protocol
        dart_path = self._convert_path_to_dart(stream_config.path)

        return f"""Stream<Map<String, dynamic>> {method_name}({params_str}) {{
  final streamKey = '{stream_config.name}';

  if (_controllers.containsKey(streamKey)) {{
    return _controllers[streamKey]!.stream;
  }}

  final controller = StreamController<Map<String, dynamic>>.broadcast();
  _controllers[streamKey] = controller;

  Future<void> connect() async {{
    if (_isConnected[streamKey] == true) return;

    try {{
      // Convert http(s):// to ws(s)://
      final wsUrl = baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
      var uri = Uri.parse('$wsUrl/{dart_path}');

      // Add auth token as query parameter if provided
      if (authToken != null) {{
        uri = uri.replace(queryParameters: {{
          ...uri.queryParameters,
          'token': authToken!,
        }});
      }}

      final channel = IOWebSocketChannel.connect(uri);
      _channels[streamKey] = channel;
      _isConnected[streamKey] = true;
      _reconnectAttempts[streamKey] = 0;

      // Start heartbeat
      _heartbeatTimers[streamKey]?.cancel();
      _heartbeatTimers[streamKey] = Timer.periodic(heartbeatInterval, (timer) {{
        if (_isConnected[streamKey] == true) {{
          channel.sink.add(jsonEncode({{'type': 'ping'}}));
        }}
      }});

      channel.stream.listen(
        (message) {{
          try {{
            final json = jsonDecode(message) as Map<String, dynamic>;
            controller.add(json);
          }} catch (e) {{
            // Skip malformed JSON
          }}
        }},
        onError: (error) {{
          _isConnected[streamKey] = false;
          _heartbeatTimers[streamKey]?.cancel();
          // Exponential backoff
          final attempts = _reconnectAttempts[streamKey] ?? 0;
          final delay = reconnectDelay * (1 << attempts.clamp(0, 5));
          _reconnectAttempts[streamKey] = attempts + 1;
          Future.delayed(delay, () => connect());
        }},
        onDone: () {{
          _isConnected[streamKey] = false;
          _heartbeatTimers[streamKey]?.cancel();
          // Exponential backoff
          final attempts = _reconnectAttempts[streamKey] ?? 0;
          final delay = reconnectDelay * (1 << attempts.clamp(0, 5));
          _reconnectAttempts[streamKey] = attempts + 1;
          Future.delayed(delay, () => connect());
        }},
        cancelOnError: false,
      );
    }} catch (e) {{
      _isConnected[streamKey] = false;
      // Exponential backoff
      final attempts = _reconnectAttempts[streamKey] ?? 0;
      final delay = reconnectDelay * (1 << attempts.clamp(0, 5));
      _reconnectAttempts[streamKey] = attempts + 1;
      Future.delayed(delay, () => connect());
    }}
  }}

  connect();
  return controller.stream;
}}"""

    def _extract_path_params(self, path: str) -> list[str]:
        """Extract path parameters from a route path.

        Args:
            path: Route path (e.g., "/orders/{order_id}/stream")

        Returns:
            List of parameter names

        Example:
            >>> _extract_path_params("/orders/{order_id}/stream")
            ["order_id"]
        """
        import re

        # Find all {param} patterns
        pattern = r"\{(\w+)\}"
        matches = re.findall(pattern, path)
        return matches

    def _convert_path_to_dart(self, path: str) -> str:
        """Convert path with {param} to Dart string interpolation with $param.

        Converts absolute paths to relative paths for use with baseUrl.
        Converts parameter names to camelCase for Dart naming conventions.

        Args:
            path: Route path (e.g., "/orders/{order_id}/stream")

        Returns:
            Dart path with string interpolation (e.g., "orders/$orderId/stream")

        Example:
            >>> _convert_path_to_dart("/orders/{order_id}/stream")
            "orders/$orderId/stream"
        """
        import re

        # Replace {param} with $camelCaseParam for Dart string interpolation
        def replace_param(match):
            param_name = match.group(1)
            camel_name = self._to_camel_case(param_name)
            return f"${camel_name}"

        pattern = r"\{(\w+)\}"
        dart_path = re.sub(pattern, replace_param, path)

        # Remove leading slash to make path relative (for use with baseUrl)
        if dart_path.startswith('/'):
            dart_path = dart_path[1:]

        return dart_path

    def _indent(self, text: str, spaces: int) -> str:
        """Indent all lines of text by the given number of spaces.

        Args:
            text: Text to indent
            spaces: Number of spaces to indent

        Returns:
            Indented text
        """
        indent_str = " " * spaces
        lines = text.split("\n")
        return "\n".join(f"{indent_str}{line}" if line.strip() else "" for line in lines)
