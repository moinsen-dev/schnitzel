"""Dart API client generator for Schnitzel schemas.

Generates Dio-based HTTP client with type-safe method signatures for each API endpoint.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set
from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, DART_TYPE_MAP


class DartApiClientGenerator:
    """Generates Dart API client from Schnitzel schemas."""

    def __init__(self):
        """Initialize the Dart API client generator."""
        self.imports: Set[str] = set()
        self.model_imports: Set[str] = set()

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to lowerCamelCase.

        Args:
            name: The field name to convert (may be snake_case)

        Returns:
            lowerCamelCase version of the name

        Examples:
            user_id -> userId
            created_at -> createdAt
            get_user -> getUser
        """
        # If no underscores, already camelCase or single word
        if '_' not in name:
            return name

        # Split by underscore and capitalize each part except the first
        parts = name.split('_')
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])

    def generate(
        self,
        schema: SchnitzelSchema,
        include_auth_interceptor: bool = True,
        include_retry_interceptor: bool = True,
        include_log_interceptor: bool = True,
        include_cache_interceptor: bool = True,
        default_timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay_ms: int = 1000,
        retryable_status_codes: list[int] | None = None,
        cache_max_age_seconds: int = 300,
    ) -> str:
        """
        Generate Dart API client from a schema.

        Args:
            schema: The Schnitzel schema to generate API client from
            include_auth_interceptor: Whether to include auth token interceptor (default: True)
            include_retry_interceptor: Whether to include retry interceptor (default: True)
            include_log_interceptor: Whether to include request/response logging (default: True)
            include_cache_interceptor: Whether to include offline cache interceptor (default: True)
            default_timeout_seconds: Default timeout in seconds for all requests (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay_ms: Base delay between retries in milliseconds (default: 1000)
            retryable_status_codes: HTTP status codes that trigger retries (default: [500, 502, 503, 504])
            cache_max_age_seconds: Maximum age in seconds for cached responses (default: 300)

        Returns:
            Generated Dart code as a string
        """
        self.imports = set()
        self.model_imports = set()
        self.default_timeout_seconds = default_timeout_seconds

        # Set default retryable status codes if not provided
        if retryable_status_codes is None:
            retryable_status_codes = [500, 502, 503, 504]

        # Check if we have any CRUD models
        crud_models = self._get_crud_models(schema)
        has_crud_models = bool(crud_models)

        # Check if schema has endpoints or CRUD models
        if not schema.endpoints and not has_crud_models:
            return self._generate_empty_client(
                include_auth_interceptor,
                include_retry_interceptor,
                include_cache_interceptor,
                default_timeout_seconds,
                max_retries,
                retry_delay_ms,
                retryable_status_codes,
                cache_max_age_seconds,
            )

        # Parse endpoints and generate methods
        client_methods = []

        # Generate methods from explicit endpoint definitions
        if schema.endpoints:
            for path, methods in schema.endpoints.items():
                # Get shared parameters for this path
                shared_params = methods.get("params", {}) if isinstance(methods, dict) else {}

                # Generate methods for each HTTP method
                for method_name, endpoint_def in methods.items():
                    if method_name == "params":
                        continue  # Skip shared params

                    if isinstance(endpoint_def, dict):
                        method_code = self._generate_client_method(
                            path, method_name, endpoint_def, shared_params
                        )
                        if method_code:
                            client_methods.append(method_code)

        # Generate CRUD methods from models with crud: true
        for model_name, model in crud_models.items():
            crud_methods = self._generate_crud_methods(model_name, model)
            client_methods.extend(crud_methods)

        # Add base imports
        self.imports.add("import 'package:dio/dio.dart';")

        # Add model imports if any
        if self.model_imports:
            self.imports.add("import '../models/models.dart';")

        # Add cache interceptor import if requested
        if include_cache_interceptor:
            self.imports.add("import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';")

        # Build final code
        imports_code = "\n".join(sorted(self.imports))
        methods_code = "\n\n".join(client_methods)

        # Generate ApiException class
        exception_class = self._generate_api_exception_class()

        # Generate retry interceptor if requested
        retry_interceptor_code = ""
        if include_retry_interceptor:
            retry_interceptor_code = self._generate_retry_interceptor(
                max_retries, retry_delay_ms, retryable_status_codes
            ) + "\n\n"

        # Generate auth interceptor if requested
        auth_interceptor_code = ""
        if include_auth_interceptor:
            auth_interceptor_code = self._generate_auth_interceptor() + "\n\n"

        # Generate cache interceptor if requested
        cache_interceptor_code = ""
        if include_cache_interceptor:
            cache_interceptor_code = self._generate_cache_interceptor(
                cache_max_age_seconds
            ) + "\n\n"

        # Build interceptor setup code (in constructor body)
        interceptor_setup = []
        if include_log_interceptor:
            interceptor_setup.append(
                "    _dio.interceptors.add(LogInterceptor(\n"
                "      requestBody: enableLogging,\n"
                "      responseBody: enableLogging,\n"
                "      requestHeader: enableLogging,\n"
                "      responseHeader: false,\n"
                "      error: true,\n"
                "      logPrint: (object) => print('[API] $object'),\n"
                "    ));"
            )
        if include_retry_interceptor:
            status_codes_str = ", ".join(str(code) for code in retryable_status_codes)
            interceptor_setup.append(
                f"    _dio.interceptors.add(RetryInterceptor(\n"
                f"      maxRetries: {max_retries},\n"
                f"      retryDelayMs: {retry_delay_ms},\n"
                f"      retryableStatusCodes: [{status_codes_str}],\n"
                f"    ));"
            )
        if include_auth_interceptor:
            interceptor_setup.append(
                "    if (token != null) {\n"
                "      _dio.interceptors.add(AuthInterceptor(token));\n"
                "    }"
            )
        if include_cache_interceptor:
            interceptor_setup.append(
                "    if (cacheStore != null) {\n"
                f"      _dio.interceptors.add(DioCacheInterceptor(\n"
                f"        options: CacheOptions(\n"
                f"          store: cacheStore,\n"
                f"          maxStale: const Duration(seconds: {cache_max_age_seconds}),\n"
                f"          policy: CachePolicy.request,\n"
                f"          priority: CachePriority.normal,\n"
                f"          hitCacheOnErrorCodes: [500, 502, 503, 504],\n"
                f"          hitCacheOnNetworkFailure: true,\n"
                f"        ),\n"
                f"      ));\n"
                f"    }}"
            )

        # Build the ApiClient class with optional interceptor setup
        interceptor_setup_code = "\n".join(interceptor_setup) if interceptor_setup else ""
        token_param = ", String? token" if include_auth_interceptor else ""

        # Add enableLogging parameter if log interceptor is included
        logging_param = "      bool enableLogging = false,\n" if include_log_interceptor else ""

        # Add cacheStore parameter if cache interceptor is included
        cache_param = "      CacheStore? cacheStore,\n" if include_cache_interceptor else ""

        if interceptor_setup:
            class_code = f"""class ApiClient {{
  final Dio _dio;
  final Map<String, String> _defaultHeaders;
  final Duration? connectTimeout;
  final Duration? receiveTimeout;
  final Duration? sendTimeout;

  ApiClient(
    this._dio,
    {{
{("      String? token," if include_auth_interceptor else "")}{logging_param}{cache_param}      Map<String, String>? defaultHeaders,
      this.connectTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.receiveTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.sendTimeout = const Duration(seconds: {default_timeout_seconds}),
    }}
  ) : _defaultHeaders = defaultHeaders ?? {{}} {{
{interceptor_setup_code}
  }}

{self._indent(methods_code, 2)}
}}"""
        else:
            class_code = f"""class ApiClient {{
  final Dio _dio;
  final Map<String, String> _defaultHeaders;
  final Duration? connectTimeout;
  final Duration? receiveTimeout;
  final Duration? sendTimeout;

  ApiClient(
    this._dio,
    {{
      Map<String, String>? defaultHeaders,
      this.connectTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.receiveTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.sendTimeout = const Duration(seconds: {default_timeout_seconds}),
    }}
  ) : _defaultHeaders = defaultHeaders ?? {{}};

{self._indent(methods_code, 2)}
}}"""

        return f"{imports_code}\n\n{exception_class}\n\n{retry_interceptor_code}{auth_interceptor_code}{cache_interceptor_code}{class_code}\n"

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """
        Generate Dart API client and write it to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the client to 'api_client.dart' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate API client from
            output_dir: Directory where api_client.dart should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to api_client.dart file, size in bytes)

        Example:
            >>> generator = DartApiClientGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "packages/shared/lib/generated")
            >>> print(f"API client written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the API client code
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
        client_file = output_path / "api_client.dart"
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

    def _generate_empty_client(
        self,
        include_auth_interceptor: bool = True,
        include_retry_interceptor: bool = True,
        include_cache_interceptor: bool = True,
        default_timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay_ms: int = 1000,
        retryable_status_codes: list[int] | None = None,
        cache_max_age_seconds: int = 300,
    ) -> str:
        """Generate a minimal API client when no endpoints are defined."""
        self.imports.add("import 'package:dio/dio.dart';")

        # Add cache interceptor import if requested
        if include_cache_interceptor:
            self.imports.add("import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';")

        imports_code = "\n".join(sorted(self.imports))
        exception_class = self._generate_api_exception_class()

        if retryable_status_codes is None:
            retryable_status_codes = [500, 502, 503, 504]

        # Generate retry interceptor if requested
        retry_interceptor_code = ""
        if include_retry_interceptor:
            retry_interceptor_code = self._generate_retry_interceptor(
                max_retries, retry_delay_ms, retryable_status_codes
            ) + "\n\n"

        # Generate auth interceptor if requested
        auth_interceptor_code = ""
        if include_auth_interceptor:
            auth_interceptor_code = self._generate_auth_interceptor() + "\n\n"

        # Generate cache interceptor if requested
        cache_interceptor_code = ""
        if include_cache_interceptor:
            cache_interceptor_code = self._generate_cache_interceptor(
                cache_max_age_seconds
            ) + "\n\n"

        # Build interceptor setup code
        interceptor_setup = []
        if include_retry_interceptor:
            status_codes_str = ", ".join(str(code) for code in retryable_status_codes)
            interceptor_setup.append(
                f"    _dio.interceptors.add(RetryInterceptor(\n"
                f"      maxRetries: {max_retries},\n"
                f"      retryDelayMs: {retry_delay_ms},\n"
                f"      retryableStatusCodes: [{status_codes_str}],\n"
                f"    ));"
            )
        if include_auth_interceptor:
            interceptor_setup.append(
                "    if (token != null) {\n"
                "      _dio.interceptors.add(AuthInterceptor(token));\n"
                "    }"
            )
        if include_cache_interceptor:
            interceptor_setup.append(
                "    if (cacheStore != null) {\n"
                f"      _dio.interceptors.add(DioCacheInterceptor(\n"
                f"        options: CacheOptions(\n"
                f"          store: cacheStore,\n"
                f"          maxStale: const Duration(seconds: {cache_max_age_seconds}),\n"
                f"          policy: CachePolicy.request,\n"
                f"          priority: CachePriority.normal,\n"
                f"          hitCacheOnErrorCodes: [500, 502, 503, 504],\n"
                f"          hitCacheOnNetworkFailure: true,\n"
                f"        ),\n"
                f"      ));\n"
                f"    }}"
            )

        interceptor_setup_code = "\n".join(interceptor_setup) if interceptor_setup else ""

        cache_param = "      CacheStore? cacheStore,\n" if include_cache_interceptor else ""

        if interceptor_setup:
            return f"""{imports_code}

{exception_class}

{retry_interceptor_code}{auth_interceptor_code}{cache_interceptor_code}class ApiClient {{
  final Dio _dio;
  final Map<String, String> _defaultHeaders;
  final Duration? connectTimeout;
  final Duration? receiveTimeout;
  final Duration? sendTimeout;

  ApiClient(
    this._dio,
    {{
{("      String? token," if include_auth_interceptor else "")}{cache_param}      Map<String, String>? defaultHeaders,
      this.connectTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.receiveTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.sendTimeout = const Duration(seconds: {default_timeout_seconds}),
    }}
  ) : _defaultHeaders = defaultHeaders ?? {{}} {{
{interceptor_setup_code}
  }}
}}
"""
        else:
            return f"""{imports_code}

{exception_class}

class ApiClient {{
  final Dio _dio;
  final Map<String, String> _defaultHeaders;
  final Duration? connectTimeout;
  final Duration? receiveTimeout;
  final Duration? sendTimeout;

  ApiClient(
    this._dio,
    {{
      Map<String, String>? defaultHeaders,
      this.connectTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.receiveTimeout = const Duration(seconds: {default_timeout_seconds}),
      this.sendTimeout = const Duration(seconds: {default_timeout_seconds}),
    }}
  ) : _defaultHeaders = defaultHeaders ?? {{}};
}}
"""

    def _generate_api_exception_class(self) -> str:
        """Generate the ApiException class for typed error handling.

        Returns:
            Dart code for ApiException class
        """
        return """class ApiException implements Exception {
  final int statusCode;
  final String message;
  final dynamic body;

  ApiException({
    required this.statusCode,
    required this.message,
    this.body,
  });

  @override
  String toString() => 'ApiException(statusCode: $statusCode, message: $message)';
}"""

    def _generate_auth_interceptor(self) -> str:
        """Generate the AuthInterceptor class for adding Bearer tokens to requests.

        Returns:
            Dart code for AuthInterceptor class
        """
        return """class AuthInterceptor extends Interceptor {
  final String token;

  AuthInterceptor(this.token);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Authorization'] = 'Bearer $token';
    super.onRequest(options, handler);
  }
}"""

    def _generate_retry_interceptor(
        self,
        max_retries: int = 3,
        retry_delay_ms: int = 1000,
        retryable_status_codes: list[int] | None = None,
    ) -> str:
        """Generate the RetryInterceptor class for automatic retry with exponential backoff.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay_ms: Base delay between retries in milliseconds (default: 1000)
            retryable_status_codes: HTTP status codes that trigger retries (default: [500, 502, 503, 504])

        Returns:
            Dart code for RetryInterceptor class
        """
        if retryable_status_codes is None:
            retryable_status_codes = [500, 502, 503, 504]

        status_codes_str = ", ".join(str(code) for code in retryable_status_codes)

        return f"""class RetryInterceptor extends Interceptor {{
  final int maxRetries;
  final int retryDelayMs;
  final List<int> retryableStatusCodes;

  RetryInterceptor({{
    this.maxRetries = {max_retries},
    this.retryDelayMs = {retry_delay_ms},
    this.retryableStatusCodes = const [{status_codes_str}],
  }});

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {{
    // Only retry on specific conditions
    if (!_shouldRetry(err)) {{
      return handler.next(err);
    }}

    // Get retry count from request extra data
    final retryCount = err.requestOptions.extra['retryCount'] as int? ?? 0;

    if (retryCount >= maxRetries) {{
      return handler.next(err);
    }}

    // Calculate exponential backoff delay
    final delayMs = retryDelayMs * (1 << retryCount); // 2^retryCount

    // Wait before retrying
    await Future.delayed(Duration(milliseconds: delayMs));

    // Clone request options and increment retry count
    final newOptions = err.requestOptions.copyWith(
      extra: {{
        ...err.requestOptions.extra,
        'retryCount': retryCount + 1,
      }},
    );

    // Retry the request
    try {{
      final dio = Dio();
      dio.options = err.requestOptions.copyWith() as BaseOptions;
      final response = await dio.fetch(newOptions);
      return handler.resolve(response);
    }} on DioException catch (e) {{
      return handler.next(e);
    }}
  }}

  bool _shouldRetry(DioException err) {{
    // Only retry idempotent requests (GET, HEAD, PUT, DELETE, OPTIONS, TRACE)
    final method = err.requestOptions.method.toUpperCase();
    final isIdempotent = ['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'].contains(method);

    if (!isIdempotent) {{
      return false;
    }}

    // Check if it's a network error (no response from server)
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError) {{
      return true;
    }}

    // Check if status code is retryable (5xx errors)
    final statusCode = err.response?.statusCode;
    if (statusCode != null && retryableStatusCodes.contains(statusCode)) {{
      return true;
    }}

    return false;
  }}
}}"""

    def _generate_cache_interceptor(
        self,
        cache_max_age_seconds: int = 300,
    ) -> str:
        """Generate documentation for cache interceptor using dio_cache_interceptor.

        The actual interceptor is added via DioCacheInterceptor from dio_cache_interceptor package.
        This method generates documentation explaining how to use caching.

        Args:
            cache_max_age_seconds: Maximum age in seconds for cached responses (default: 300)

        Returns:
            Dart documentation comment explaining cache setup
        """
        return f"""// Cache Interceptor Configuration
// To enable response caching, pass a CacheStore instance to the ApiClient constructor.
// Example with MemCacheStore (in-memory caching):
//
//   final cacheStore = MemCacheStore();
//   final apiClient = ApiClient(
//     dio,
//     cacheStore: cacheStore,
//   );
//
// The cache uses the following configuration:
//   - maxStale: {cache_max_age_seconds} seconds (how long responses are cached)
//   - policy: CachePolicy.request (respects HTTP cache headers)
//   - priority: CachePriority.normal
//   - hitCacheOnErrorCodes: [500, 502, 503, 504] (use cache on server errors)
//   - hitCacheOnNetworkFailure: true (use cache when offline)
//
// For persistent caching, use HiveCacheStore:
//   - Add hive_flutter dependency to pubspec.yaml
//   - Initialize: await Hive.initFlutter();
//   - Create store: final cacheStore = HiveCacheStore(await HiveStore.open());"""

    def _generate_client_method(
        self,
        path: str,
        method: str,
        endpoint_def: Dict[str, Any],
        shared_params: Dict[str, Any],
    ) -> str:
        """Generate a single API client method.

        Args:
            path: API path (e.g., "/users/{id}")
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint_def: Endpoint definition from schema
            shared_params: Shared parameters for this path

        Returns:
            Generated method code as string
        """
        method_lower = method.lower()
        method_name = endpoint_def.get("name", f"{method_lower}_{path.replace('/', '_').replace('{', '').replace('}', '')}")
        method_name = self._to_camel_case(method_name)

        # Extract path parameters from the path
        path_params = self._extract_path_params(path)

        # Build function parameters
        params = []
        named_params = []

        # Add path parameters (always required positional)
        for param_name in path_params:
            # Get type from shared_params if available, default to String
            param_type = "String"
            if shared_params and param_name in shared_params:
                param_def = shared_params[param_name]
                param_type = self._get_dart_type(param_def.get("type", "string"))
            params.append(f"{param_type} {param_name}")

        # Add query parameters (collect for both signature and queryParameters map)
        query_params = []
        if "query" in endpoint_def:
            for query_name, query_def in endpoint_def["query"].items():
                query_type = self._get_dart_type(query_def.get("type", "string"))
                optional = query_def.get("optional", False)
                default = query_def.get("default")
                description = query_def.get("description", "")

                # Track query params for later use in queryParameters map
                query_params.append({
                    "name": query_name,
                    "type": query_type,
                    "optional": optional,
                    "default": default,
                    "description": description
                })

                # Build parameter signature with default values
                if default is not None:
                    # Format default value based on type
                    if isinstance(default, bool):
                        default_str = str(default).lower()
                    elif isinstance(default, str):
                        default_str = f"'{default}'"
                    else:
                        default_str = str(default)
                    params.append(f"{query_type} {query_name} = {default_str}")
                elif optional:
                    params.append(f"{query_type}? {query_name}")
                else:
                    params.append(f"{query_type} {query_name}")

        # Add request body for POST/PUT/PATCH
        body_param = None
        has_body = False
        if method_lower in ["post", "put", "patch"]:
            if "body" in endpoint_def:
                has_body = True
                body_type = endpoint_def["body"]
                if isinstance(body_type, str):
                    # Reference to a model
                    body_param = body_type
                    params.append(f"{body_type} body")
                    # Track model import
                    self.model_imports.add(body_type)
                elif isinstance(body_type, dict):
                    # Inline body definition - use Map for now
                    params.append("Map<String, dynamic> body")

        # Determine return type
        return_type = "void"
        response_model = None
        is_list_response = False
        if "response" in endpoint_def:
            responses = endpoint_def["response"]

            # Handle simple string response format (e.g., "User" or "User[]")
            if isinstance(responses, str):
                response_type = responses
                # Check for list notation
                if response_type.endswith("[]"):
                    is_list_response = True
                    response_model = response_type[:-2]
                    return_type = f"List<{response_model}>"
                    self.model_imports.add(response_model)
                elif response_type.lower() != "void":
                    response_model = response_type
                    return_type = response_model
                    self.model_imports.add(response_model)
            elif isinstance(responses, dict):
                # Look for successful response (200, 201, etc.)
                for status_code in [200, 201, 202, 204]:
                    if status_code in responses:
                        response_def = responses[status_code]
                        if isinstance(response_def, dict) and "type" in response_def:
                            response_type = response_def["type"]

                            # Check if it's a list response: list<ModelName> or List<ModelName> or List[ModelName]
                            if isinstance(response_type, str):
                                import re
                                # Match list<Type>, List<Type>, or List[Type]
                                list_match = re.match(r'^[Ll]ist[<\[](.+?)[>\]]$', response_type)
                                if list_match:
                                    is_list_response = True
                                    # Extract the model name from list<ModelName>
                                    response_model = list_match.group(1).strip()
                                    return_type = f"List<{response_model}>"
                                    # Track model import
                                    self.model_imports.add(response_model)
                                elif response_type.lower() != "void":
                                    # Only set response_model if it's not void
                                    response_model = response_type
                                    return_type = response_model
                                    # Track model import
                                    self.model_imports.add(response_model)
                        break

        # Build function signature
        # If we have query params with defaults or optional params, use named parameters
        has_optional_params = any(qp.get("default") is not None or qp.get("optional") for qp in query_params)

        if has_optional_params and query_params:
            # Separate path params (required positional) from query params (named optional)
            positional_params = params[:len(path_params)]  # Path params come first
            named_params = params[len(path_params):]  # Query params and optional params (including body)

            # Mark body param as required if it's in named params and doesn't have a default
            if body_param and named_params:
                # Find and update the body parameter to be required
                for i, param in enumerate(named_params):
                    if 'body' in param and '=' not in param:
                        named_params[i] = f"required {param}"

            # Add headers, timeout, and cancellation parameters (always optional)
            named_params.append("Map<String, String>? headers")
            named_params.append("Duration? requestTimeout")
            named_params.append("CancelToken? cancelToken")

            # Add progress callbacks for methods with body (uploads)
            if has_body:
                named_params.append("void Function(int, int)? onSendProgress")

            if positional_params and named_params:
                params_str = ", ".join(positional_params) + ", {" + ", ".join(named_params) + "}"
            elif named_params:
                params_str = "{" + ", ".join(named_params) + "}"
            else:
                params_str = ", ".join(params) if params else ""
        else:
            # No optional params - add headers, timeout, and cancellation as optional named parameters
            progress_param = ", void Function(int, int)? onSendProgress" if has_body else ""
            if params:
                params_str = ", ".join(params) + f", {{Map<String, String>? headers, Duration? requestTimeout, CancelToken? cancelToken{progress_param}}}"
            else:
                params_str = f"{{Map<String, String>? headers, Duration? requestTimeout, CancelToken? cancelToken{progress_param}}}"

        function_signature = f"Future<{return_type}> {method_name}({params_str}) async {{"

        # Generate function body
        # Build the path with parameter interpolation
        dart_path = self._convert_path_to_dart(path)

        # Build queryParameters map if we have query params
        query_params_code = None
        if query_params:
            query_entries = []
            for qp in query_params:
                query_entries.append(f"'{qp['name']}': {qp['name']}")
            query_params_code = "queryParameters: {\n    " + ",\n    ".join(query_entries) + ",\n  }"

        # Build headers merging code
        headers_merge_code = "final mergedHeaders = {..._defaultHeaders, ...?headers};"

        # Build options with headers and timeouts
        options_parts = ["headers: mergedHeaders"]
        options_parts.append("sendTimeout: requestTimeout ?? sendTimeout")
        options_parts.append("receiveTimeout: requestTimeout ?? receiveTimeout")
        options_code = "options: Options(" + ", ".join(options_parts) + ")"

        # Add onSendProgress if this is a request with body
        progress_code = ""
        if has_body:
            progress_code = ", onSendProgress: onSendProgress"

        # Add cancelToken parameter
        cancel_token_code = ", cancelToken: cancelToken"

        # Build the HTTP call with options
        http_method = method_lower
        if http_method == "get":
            if query_params_code:
                call_code = f"final response = await _dio.get('{dart_path}', {query_params_code}, {options_code}{cancel_token_code});"
            else:
                call_code = f"final response = await _dio.get('{dart_path}', {options_code}{cancel_token_code});"
        elif http_method == "post":
            if body_param:
                if query_params_code:
                    call_code = f"final response = await _dio.post('{dart_path}', data: body.toJson(), {query_params_code}, {options_code}{progress_code}{cancel_token_code});"
                else:
                    call_code = f"final response = await _dio.post('{dart_path}', data: body.toJson(), {options_code}{progress_code}{cancel_token_code});"
            else:
                if query_params_code:
                    call_code = f"final response = await _dio.post('{dart_path}', {query_params_code}, {options_code}{progress_code}{cancel_token_code});"
                else:
                    call_code = f"final response = await _dio.post('{dart_path}', {options_code}{progress_code}{cancel_token_code});"
        elif http_method == "put":
            if body_param:
                if query_params_code:
                    call_code = f"final response = await _dio.put('{dart_path}', data: body.toJson(), {query_params_code}, {options_code}{progress_code}{cancel_token_code});"
                else:
                    call_code = f"final response = await _dio.put('{dart_path}', data: body.toJson(), {options_code}{progress_code}{cancel_token_code});"
            else:
                if query_params_code:
                    call_code = f"final response = await _dio.put('{dart_path}', {query_params_code}, {options_code}{progress_code}{cancel_token_code});"
                else:
                    call_code = f"final response = await _dio.put('{dart_path}', {options_code}{progress_code}{cancel_token_code});"
        elif http_method == "patch":
            if body_param:
                if query_params_code:
                    call_code = f"final response = await _dio.patch('{dart_path}', data: body.toJson(), {query_params_code}, {options_code}{progress_code}{cancel_token_code});"
                else:
                    call_code = f"final response = await _dio.patch('{dart_path}', data: body.toJson(), {options_code}{progress_code}{cancel_token_code});"
            else:
                if query_params_code:
                    call_code = f"final response = await _dio.patch('{dart_path}', {query_params_code}, {options_code}{progress_code}{cancel_token_code});"
                else:
                    call_code = f"final response = await _dio.patch('{dart_path}', {options_code}{progress_code}{cancel_token_code});"
        elif http_method == "delete":
            if query_params_code:
                call_code = f"final response = await _dio.delete('{dart_path}', {query_params_code}, {options_code}{cancel_token_code});"
            else:
                call_code = f"final response = await _dio.delete('{dart_path}', {options_code}{cancel_token_code});"
        else:
            # Merge options for custom methods
            merged_options = f"Options(method: '{method.upper()}', headers: mergedHeaders, sendTimeout: requestTimeout ?? sendTimeout, receiveTimeout: requestTimeout ?? receiveTimeout)"
            if query_params_code:
                call_code = f"final response = await _dio.request('{dart_path}', options: {merged_options}, {query_params_code}{cancel_token_code});"
            else:
                call_code = f"final response = await _dio.request('{dart_path}', options: {merged_options}{cancel_token_code});"

        # Add response deserialization if there's a response model
        if response_model:
            if is_list_response:
                # For list responses, map each item using fromJson
                return_code = f"return (response.data as List).map((e) => {response_model}.fromJson(e)).toList();"
            else:
                # For single object responses
                return_code = f"return {response_model}.fromJson(response.data);"
        else:
            return_code = ""

        # Build method body with error handling
        body_lines = ["try {"]
        body_lines.append(f"  {headers_merge_code}")
        body_lines.append(f"  {call_code}")
        if return_code:
            body_lines.append(f"  {return_code}")
        body_lines.append("} on DioException catch (e) {")
        body_lines.append("  throw ApiException(")
        body_lines.append("    statusCode: e.response?.statusCode ?? 0,")
        body_lines.append("    message: e.message ?? 'Unknown error',")
        body_lines.append("    body: e.response?.data,")
        body_lines.append("  );")
        body_lines.append("}")

        function_body = "\n".join(f"  {line}" for line in body_lines)

        # Build documentation comment with endpoint description and parameter docs
        doc_lines = []
        description = endpoint_def.get("description", "")

        if description:
            doc_lines.append(f"/// {description}")
            doc_lines.append("///")

        # Add parameter documentation
        param_docs_added = False

        # Document path parameters
        for param_name in path_params:
            param_desc = None
            if shared_params and param_name in shared_params:
                param_def = shared_params[param_name]
                if isinstance(param_def, dict):
                    param_desc = param_def.get("description", "")

            if param_desc:
                doc_lines.append(f"/// * [{param_name}] - {param_desc}")
                param_docs_added = True
            elif description:  # Only add minimal param doc if we have a main description
                doc_lines.append(f"/// * [{param_name}] - Path parameter")
                param_docs_added = True

        # Document query parameters
        for qp in query_params:
            param_desc = qp.get("description", "")
            if param_desc:
                optional_marker = " (optional)" if qp.get("optional", False) else ""
                default_marker = f" (default: {qp.get('default')})" if qp.get("default") is not None else ""
                doc_lines.append(f"/// * [{qp['name']}] - {param_desc}{optional_marker}{default_marker}")
                param_docs_added = True
            elif description:  # Only add minimal param doc if we have a main description
                optional_marker = " (optional)" if qp.get("optional", False) else ""
                doc_lines.append(f"/// * [{qp['name']}] - Query parameter{optional_marker}")
                param_docs_added = True

        # Document body parameter
        if body_param and description:
            doc_lines.append(f"/// * [body] - Request body ({body_param})")
            param_docs_added = True

        # Build final docstring
        docstring = "\n".join(doc_lines) if doc_lines else ""

        # Combine all parts
        lines = []
        if docstring:
            lines.append(docstring)
        lines.append(function_signature)
        lines.append(function_body)
        lines.append("}")

        return "\n".join(lines)

    def _extract_path_params(self, path: str) -> List[str]:
        """Extract path parameters from a route path.

        Args:
            path: Route path (e.g., "/users/{id}")

        Returns:
            List of parameter names

        Example:
            >>> _extract_path_params("/users/{id}")
            ["id"]
        """
        import re

        # Find all {param} patterns
        pattern = r"\{(\w+)\}"
        matches = re.findall(pattern, path)
        return matches

    def _convert_path_to_dart(self, path: str) -> str:
        """Convert path with {param} to Dart string interpolation with $param.

        Converts absolute paths to relative paths for use with Dio's baseUrl.
        This ensures that the base URL can be configured on the Dio instance
        rather than hardcoded in each method call.

        Args:
            path: Route path (e.g., "/users/{id}")

        Returns:
            Dart path with string interpolation (e.g., "users/$id")
            Note: Leading slash is removed to make path relative

        Example:
            >>> _convert_path_to_dart("/users/{id}")
            "users/$id"
        """
        import re

        # Replace {param} with $param for Dart string interpolation
        pattern = r"\{(\w+)\}"
        dart_path = re.sub(pattern, r"$\1", path)

        # Remove leading slash to make path relative (for use with Dio baseUrl)
        if dart_path.startswith('/'):
            dart_path = dart_path[1:]

        return dart_path

    def _get_dart_type(self, schema_type: str) -> str:
        """
        Map schema type to Dart type.

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

    def _get_crud_models(self, schema: SchnitzelSchema) -> Dict[str, Any]:
        """Get models that have crud enabled.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dictionary of model name to model definition for models with crud enabled
        """
        crud_models = {}
        if schema.models:
            for model_name, model in schema.models.items():
                if model.crud:
                    crud_models[model_name] = model
        return crud_models

    def _generate_crud_methods(self, model_name: str, model: Any) -> List[str]:
        """Generate CRUD API methods for a model.

        Args:
            model_name: Name of the model (e.g., "User")
            model: Model definition

        Returns:
            List of generated method code strings
        """
        methods = []

        # Determine which CRUD operations to generate
        if model.crud is True:
            operations = ["list", "get", "create", "update", "delete"]
        elif isinstance(model.crud, list):
            operations = model.crud
        else:
            return methods

        # Generate plural resource name (User -> users)
        resource_name = self._pluralize(self._to_snake_case(model_name))

        # Find primary key field
        pk_field = "id"
        pk_type = "String"  # UUIDs are strings in Dart
        for field_name, field_def in model.fields.items():
            if field_def.primary:
                pk_field = field_name
                pk_type = self._get_dart_type(field_def.type)
                break

        # Add model import
        self.model_imports.add(model_name)

        # Generate each CRUD operation
        if "list" in operations:
            methods.append(self._generate_dart_list_method(model_name, resource_name))

        if "get" in operations:
            methods.append(self._generate_dart_get_method(model_name, resource_name, pk_field, pk_type))

        if "create" in operations:
            methods.append(self._generate_dart_create_method(model_name, resource_name))

        if "update" in operations:
            methods.append(self._generate_dart_update_method(model_name, resource_name, pk_field, pk_type))

        if "delete" in operations:
            methods.append(self._generate_dart_delete_method(model_name, resource_name, pk_field, pk_type))

        return methods

    def _generate_dart_list_method(self, model_name: str, resource_name: str) -> str:
        """Generate list method for Dart API client."""
        method_name = f"list{model_name}s"
        if model_name.endswith('s'):
            method_name = f"list{model_name}es"

        return f'''/// List all {resource_name} with pagination.
///
/// * [page] - Page number (default: 1)
/// * [limit] - Items per page (default: 20, max: 100)
Future<List<{model_name}>> {self._to_camel_case(method_name)}({{
  int page = 1,
  int limit = 20,
  Map<String, String>? headers,
  Duration? requestTimeout,
  CancelToken? cancelToken,
}}) async {{
  try {{
    final mergedHeaders = {{..._defaultHeaders, ...?headers}};
    final response = await _dio.get(
      '{resource_name}',
      queryParameters: {{'page': page, 'limit': limit}},
      options: Options(
        headers: mergedHeaders,
        sendTimeout: requestTimeout ?? sendTimeout,
        receiveTimeout: requestTimeout ?? receiveTimeout,
      ),
      cancelToken: cancelToken,
    );
    return (response.data as List).map((e) => {model_name}.fromJson(e)).toList();
  }} on DioException catch (e) {{
    throw ApiException(
      statusCode: e.response?.statusCode ?? 0,
      message: e.message ?? 'Unknown error',
      body: e.response?.data,
    );
  }}
}}'''

    def _generate_dart_get_method(self, model_name: str, resource_name: str, pk_field: str = "id", pk_type: str = "String") -> str:
        """Generate get-by-id method for Dart API client."""
        method_name = f"get{model_name}"

        return f'''/// Get a single {self._to_snake_case(model_name)} by {pk_field}.
///
/// * [{pk_field}] - The {self._to_snake_case(model_name)} {pk_field}
Future<{model_name}> {self._to_camel_case(method_name)}(
  {pk_type} {pk_field}, {{
  Map<String, String>? headers,
  Duration? requestTimeout,
  CancelToken? cancelToken,
}}) async {{
  try {{
    final mergedHeaders = {{..._defaultHeaders, ...?headers}};
    final response = await _dio.get(
      '{resource_name}/${pk_field}',
      options: Options(
        headers: mergedHeaders,
        sendTimeout: requestTimeout ?? sendTimeout,
        receiveTimeout: requestTimeout ?? receiveTimeout,
      ),
      cancelToken: cancelToken,
    );
    return {model_name}.fromJson(response.data);
  }} on DioException catch (e) {{
    throw ApiException(
      statusCode: e.response?.statusCode ?? 0,
      message: e.message ?? 'Unknown error',
      body: e.response?.data,
    );
  }}
}}'''

    def _generate_dart_create_method(self, model_name: str, resource_name: str) -> str:
        """Generate create method for Dart API client."""
        method_name = f"create{model_name}"
        # Use the model itself as the request body type

        return f'''/// Create a new {self._to_snake_case(model_name)}.
///
/// * [body] - The {self._to_snake_case(model_name)} data to create
Future<{model_name}> {self._to_camel_case(method_name)}(
  {model_name} body, {{
  Map<String, String>? headers,
  Duration? requestTimeout,
  CancelToken? cancelToken,
  void Function(int, int)? onSendProgress,
}}) async {{
  try {{
    final mergedHeaders = {{..._defaultHeaders, ...?headers}};
    final response = await _dio.post(
      '{resource_name}',
      data: body.toJson(),
      options: Options(
        headers: mergedHeaders,
        sendTimeout: requestTimeout ?? sendTimeout,
        receiveTimeout: requestTimeout ?? receiveTimeout,
      ),
      onSendProgress: onSendProgress,
      cancelToken: cancelToken,
    );
    return {model_name}.fromJson(response.data);
  }} on DioException catch (e) {{
    throw ApiException(
      statusCode: e.response?.statusCode ?? 0,
      message: e.message ?? 'Unknown error',
      body: e.response?.data,
    );
  }}
}}'''

    def _generate_dart_update_method(self, model_name: str, resource_name: str, pk_field: str = "id", pk_type: str = "String") -> str:
        """Generate update method for Dart API client."""
        method_name = f"update{model_name}"
        # Use the model itself as the request body type

        return f'''/// Update an existing {self._to_snake_case(model_name)}.
///
/// * [{pk_field}] - The {self._to_snake_case(model_name)} {pk_field}
/// * [body] - The updated {self._to_snake_case(model_name)} data
Future<{model_name}> {self._to_camel_case(method_name)}(
  {pk_type} {pk_field},
  {model_name} body, {{
  Map<String, String>? headers,
  Duration? requestTimeout,
  CancelToken? cancelToken,
  void Function(int, int)? onSendProgress,
}}) async {{
  try {{
    final mergedHeaders = {{..._defaultHeaders, ...?headers}};
    final response = await _dio.put(
      '{resource_name}/${pk_field}',
      data: body.toJson(),
      options: Options(
        headers: mergedHeaders,
        sendTimeout: requestTimeout ?? sendTimeout,
        receiveTimeout: requestTimeout ?? receiveTimeout,
      ),
      onSendProgress: onSendProgress,
      cancelToken: cancelToken,
    );
    return {model_name}.fromJson(response.data);
  }} on DioException catch (e) {{
    throw ApiException(
      statusCode: e.response?.statusCode ?? 0,
      message: e.message ?? 'Unknown error',
      body: e.response?.data,
    );
  }}
}}'''

    def _generate_dart_delete_method(self, model_name: str, resource_name: str, pk_field: str = "id", pk_type: str = "String") -> str:
        """Generate delete method for Dart API client."""
        method_name = f"delete{model_name}"

        return f'''/// Delete a {self._to_snake_case(model_name)}.
///
/// * [{pk_field}] - The {self._to_snake_case(model_name)} {pk_field} to delete
Future<void> {self._to_camel_case(method_name)}(
  {pk_type} {pk_field}, {{
  Map<String, String>? headers,
  Duration? requestTimeout,
  CancelToken? cancelToken,
}}) async {{
  try {{
    final mergedHeaders = {{..._defaultHeaders, ...?headers}};
    await _dio.delete(
      '{resource_name}/${pk_field}',
      options: Options(
        headers: mergedHeaders,
        sendTimeout: requestTimeout ?? sendTimeout,
        receiveTimeout: requestTimeout ?? receiveTimeout,
      ),
      cancelToken: cancelToken,
    );
  }} on DioException catch (e) {{
    throw ApiException(
      statusCode: e.response?.statusCode ?? 0,
      message: e.message ?? 'Unknown error',
      body: e.response?.data,
    );
  }}
}}'''

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase or camelCase to snake_case.

        Args:
            name: Name in PascalCase or camelCase

        Returns:
            Name in snake_case
        """
        import re
        # Insert underscore before uppercase letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _pluralize(self, name: str) -> str:
        """Simple pluralization for resource names.

        Args:
            name: Singular name

        Returns:
            Pluralized name
        """
        # Simple English pluralization rules
        if name.endswith('y') and len(name) > 1 and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return name + 'es'
        else:
            return name + 's'
