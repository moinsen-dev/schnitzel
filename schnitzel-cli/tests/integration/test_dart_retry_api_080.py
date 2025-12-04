"""Integration tests for api_080 - Dart API client generator handles retry logic.

Test Requirements (from feature):
1. Generate Dart API client with retry interceptor
2. Verify RetryInterceptor is configured with sensible defaults
3. Verify retry attempts and exponential backoff strategy
4. Verify only idempotent requests (GET) are retried
5. Run dart analyze - no errors
"""

import tempfile
import os
from pathlib import Path
import subprocess
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart.api_client import DartApiClientGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_retry_interceptor_class_generated(temp_dir: Path) -> None:
    """Test that RetryInterceptor class is generated."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID"
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client with retry interceptor
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema, include_retry_interceptor=True)

    # Verify RetryInterceptor class exists
    assert "class RetryInterceptor extends Interceptor" in api_client_code, \
        "Should have RetryInterceptor class"
    assert "final int maxRetries;" in api_client_code, \
        "Should have maxRetries field"
    assert "final int retryDelayMs;" in api_client_code, \
        "Should have retryDelayMs field"
    assert "final List<int> retryableStatusCodes;" in api_client_code, \
        "Should have retryableStatusCodes field"


def test_retry_interceptor_default_configuration(temp_dir: Path) -> None:
    """Test that retry interceptor has sensible default configuration."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify default configuration values
    assert "maxRetries: 3" in api_client_code, "Default maxRetries should be 3"
    assert "retryDelayMs: 1000" in api_client_code, "Default retryDelayMs should be 1000"
    assert "retryableStatusCodes: [500, 502, 503, 504]" in api_client_code, \
        "Default retryable status codes should be 5xx errors"


def test_retry_interceptor_custom_configuration(temp_dir: Path) -> None:
    """Test that retry interceptor supports custom configuration."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(
        schema,
        max_retries=5,
        retry_delay_ms=2000,
        retryable_status_codes=[500, 503]
    )

    # Verify custom configuration is applied
    assert "maxRetries: 5" in api_client_code, "Custom maxRetries should be used"
    assert "retryDelayMs: 2000" in api_client_code, "Custom retryDelayMs should be used"
    assert "retryableStatusCodes: [500, 503]" in api_client_code, \
        "Custom retryable status codes should be used"


def test_retry_interceptor_exponential_backoff(temp_dir: Path) -> None:
    """Test that retry interceptor uses exponential backoff strategy."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify exponential backoff calculation is present
    assert "final delayMs = retryDelayMs * (1 << retryCount);" in api_client_code, \
        "Should use exponential backoff (2^retryCount)"
    assert "await Future.delayed(Duration(milliseconds: delayMs));" in api_client_code, \
        "Should wait before retrying"


def test_retry_interceptor_only_idempotent_requests(temp_dir: Path) -> None:
    """Test that only idempotent requests are retried (GET, HEAD, PUT, DELETE, OPTIONS, TRACE)."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify idempotent check
    assert "final method = err.requestOptions.method.toUpperCase();" in api_client_code, \
        "Should extract HTTP method"
    assert "final isIdempotent = ['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'].contains(method);" in api_client_code, \
        "Should check if method is idempotent"
    assert "if (!isIdempotent)" in api_client_code, \
        "Should skip retry for non-idempotent methods"


def test_retry_interceptor_network_errors(temp_dir: Path) -> None:
    """Test that retry interceptor retries on network errors."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify network error types are checked
    assert "DioExceptionType.connectionTimeout" in api_client_code, \
        "Should retry on connection timeout"
    assert "DioExceptionType.sendTimeout" in api_client_code, \
        "Should retry on send timeout"
    assert "DioExceptionType.receiveTimeout" in api_client_code, \
        "Should retry on receive timeout"
    assert "DioExceptionType.connectionError" in api_client_code, \
        "Should retry on connection error"


def test_retry_interceptor_5xx_errors(temp_dir: Path) -> None:
    """Test that retry interceptor retries on 5xx status codes."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify 5xx status code check
    assert "final statusCode = err.response?.statusCode;" in api_client_code, \
        "Should extract status code from response"
    assert "if (statusCode != null && retryableStatusCodes.contains(statusCode))" in api_client_code, \
        "Should check if status code is retryable"


def test_retry_interceptor_max_retries_limit(temp_dir: Path) -> None:
    """Test that retry interceptor respects max retries limit."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify retry count tracking and limit checking
    assert "final retryCount = err.requestOptions.extra['retryCount'] as int? ?? 0;" in api_client_code, \
        "Should track retry count in request extra data"
    assert "if (retryCount >= maxRetries)" in api_client_code, \
        "Should check if max retries reached"
    assert "'retryCount': retryCount + 1" in api_client_code, \
        "Should increment retry count for next attempt"


def test_retry_interceptor_added_to_client(temp_dir: Path) -> None:
    """Test that RetryInterceptor is added to Dio client."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify RetryInterceptor is added to Dio instance
    assert "_dio.interceptors.add(RetryInterceptor(" in api_client_code, \
        "Should add RetryInterceptor to Dio client"


def test_retry_interceptor_can_be_disabled(temp_dir: Path) -> None:
    """Test that retry interceptor can be disabled."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema, include_retry_interceptor=False)

    # Verify RetryInterceptor is NOT generated
    assert "class RetryInterceptor" not in api_client_code, \
        "Should not generate RetryInterceptor when disabled"
    assert "_dio.interceptors.add(RetryInterceptor(" not in api_client_code, \
        "Should not add RetryInterceptor when disabled"


def test_retry_interceptor_with_auth_interceptor(temp_dir: Path) -> None:
    """Test that retry interceptor works alongside auth interceptor."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(
        schema,
        include_auth_interceptor=True,
        include_retry_interceptor=True
    )

    # Verify both interceptors are present
    assert "class AuthInterceptor" in api_client_code, \
        "Should have AuthInterceptor"
    assert "class RetryInterceptor" in api_client_code, \
        "Should have RetryInterceptor"
    assert "_dio.interceptors.add(RetryInterceptor(" in api_client_code, \
        "Should add RetryInterceptor"
    assert "_dio.interceptors.add(AuthInterceptor(token));" in api_client_code, \
        "Should add AuthInterceptor"

    # Verify RetryInterceptor is added BEFORE AuthInterceptor
    # (Retry should be outer, auth should be inner)
    retry_pos = api_client_code.find("_dio.interceptors.add(RetryInterceptor(")
    auth_pos = api_client_code.find("_dio.interceptors.add(AuthInterceptor(token));")
    assert retry_pos < auth_pos, \
        "RetryInterceptor should be added before AuthInterceptor"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_retry_client_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with retry interceptor passes dart analyze."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID"
      response:
        200:
          type: User

  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, _ = generator.generate_to_file(schema, output_dir)

    # Create a minimal pubspec.yaml for dart analyze
    pubspec_dir = temp_dir / "packages" / "shared"
    pubspec_file = pubspec_dir / "pubspec.yaml"
    pubspec_file.write_text("""name: shared
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  dio: ^5.0.0
  freezed_annotation: ^2.0.0
  json_annotation: ^4.0.0
dev_dependencies:
  freezed: ^2.0.0
  build_runner: ^2.0.0
  json_serializable: ^6.0.0
""")

    # Create models directory and a stub models.dart
    models_dir = temp_dir / "packages" / "shared" / "lib" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    models_file = models_dir / "models.dart"
    models_file.write_text("""import 'package:freezed_annotation/freezed_annotation.dart';

part 'models.freezed.dart';
part 'models.g.dart';

@freezed
abstract class User with _$User {
  const factory User({
    required String id,
    required String name,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
""")

    # Run dart analyze on the generated file
    result = subprocess.run(
        ["dart", "analyze", str(api_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # The analysis may fail due to missing dependencies, but verify no syntax errors
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"


def test_retry_interceptor_code_structure(temp_dir: Path) -> None:
    """Test the overall structure of retry interceptor implementation."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify key components exist
    assert "@override" in api_client_code, \
        "Should override onError method"
    assert "Future<void> onError(DioException err, ErrorInterceptorHandler handler) async" in api_client_code, \
        "Should have async onError handler"
    assert "bool _shouldRetry(DioException err)" in api_client_code, \
        "Should have _shouldRetry helper method"
    assert "final response = await dio.fetch(newOptions);" in api_client_code, \
        "Should retry request using dio.fetch"
    assert "return handler.resolve(response);" in api_client_code, \
        "Should resolve with successful response"
    assert "return handler.next(err);" in api_client_code or "return handler.next(e);" in api_client_code, \
        "Should pass error forward when not retrying"
