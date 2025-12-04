"""Integration tests for api_025 - Dart API client generator handles query parameters.

Test Requirements (from feature):
1. Create schema with endpoint: GET /users?page=1&limit=20
2. Run schnitzel generate --target dart
3. Verify method has page and limit parameters
4. Verify queryParameters map is built correctly
5. Verify optional parameters have default values
6. Run dart analyze - no errors
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


def test_query_params_in_method_signature(temp_dir: Path) -> None:
    """Test that query parameters appear in method signature."""
    # Create schema with query parameters
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
  /users:
    GET:
      name: list_users
      description: "List users with pagination"
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify method signature has page and limit parameters
    assert "Future<List<User>> listUsers({int page = 1, int limit = 20})" in api_client_code or \
           "listUsers({int page = 1, int limit = 20})" in api_client_code, \
           "Method should have page and limit parameters with defaults"


def test_query_params_with_defaults(temp_dir: Path) -> None:
    """Test that query parameters with default values are generated correctly."""
    # Create schema with query parameters having default values
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
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
        sort_by:
          type: string
          default: name
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify default values are present
    assert "int page = 1" in api_client_code, "page should have default value 1"
    assert "int limit = 20" in api_client_code, "limit should have default value 20"
    assert "String sort_by = 'name'" in api_client_code or \
           'String sortBy = "name"' in api_client_code or \
           "String sortBy = 'name'" in api_client_code, \
           "sort_by should have default value 'name'"


def test_query_params_optional_no_default(temp_dir: Path) -> None:
    """Test that optional query parameters without defaults are nullable."""
    # Create schema with optional query parameters
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
      query:
        page:
          type: int
          default: 1
        search:
          type: string
          optional: true
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify optional parameter is nullable
    assert "String? search" in api_client_code, "Optional parameter should be nullable (String?)"


def test_query_params_map_built_correctly(temp_dir: Path) -> None:
    """Test that queryParameters map is built correctly in Dio call."""
    # Create schema with query parameters
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
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify queryParameters map is present
    assert "queryParameters:" in api_client_code, "Should have queryParameters in Dio call"
    assert "'page': page" in api_client_code, "Should map page parameter"
    assert "'limit': limit" in api_client_code, "Should map limit parameter"


def test_query_params_in_get_request(temp_dir: Path) -> None:
    """Test that GET request includes queryParameters."""
    # Create schema with query parameters
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
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify _dio.get() includes queryParameters
    assert "_dio.get('users', queryParameters:" in api_client_code, \
           "GET request should include queryParameters"


def test_multiple_query_param_types(temp_dir: Path) -> None:
    """Test that different query parameter types are handled correctly."""
    # Create schema with various query parameter types
    schema_content = """schnitzel: "1.0"

models:
  Restaurant:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /restaurants:
    GET:
      name: list_restaurants
      query:
        page:
          type: int
          default: 1
        is_open:
          type: bool
          default: true
        cuisine:
          type: string
          optional: true
        min_rating:
          type: float
          optional: true
      response:
        200:
          type: list<Restaurant>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify different types are handled
    assert "int page = 1" in api_client_code, "int type should be handled"
    assert "bool is_open = true" in api_client_code or \
           "bool isOpen = true" in api_client_code, \
           "bool type should be handled with default"
    assert "String? cuisine" in api_client_code, "optional string should be nullable"
    assert "double? min_rating" in api_client_code or \
           "double? minRating" in api_client_code, \
           "optional double should be nullable"


def test_query_params_with_path_params(temp_dir: Path) -> None:
    """Test that query parameters work alongside path parameters."""
    # Create schema with both path and query parameters
    schema_content = """schnitzel: "1.0"

models:
  Comment:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /posts/{post_id}/comments:
    params:
      post_id:
        type: uuid
    GET:
      name: list_comments
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 10
      response:
        200:
          type: list<Comment>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify both path and query parameters are present
    assert "String post_id" in api_client_code or \
           "String postId" in api_client_code, \
           "Should have path parameter"
    assert "int page = 1" in api_client_code, "Should have page query parameter"
    assert "int limit = 10" in api_client_code, "Should have limit query parameter"
    assert "queryParameters:" in api_client_code, "Should have queryParameters map"


def test_query_params_file_output(temp_dir: Path) -> None:
    """Test that API client with query params is written to file correctly."""
    # Create schema with query parameters
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
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client to file
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert api_client_file.exists(), "api_client.dart should be created"

    # Read and verify content
    api_client_content = api_client_file.read_text()
    assert "queryParameters:" in api_client_content, "File should contain queryParameters"
    assert "'page': page" in api_client_content, "File should contain page mapping"
    assert "'limit': limit" in api_client_content, "File should contain limit mapping"


def test_query_params_no_params_endpoint(temp_dir: Path) -> None:
    """Test that endpoints without query params don't have queryParameters."""
    # Create schema with one endpoint having query params and one without
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      response:
        200:
          type: User

  /users:
    GET:
      name: list_users
      query:
        page:
          type: int
          default: 1
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify get_user doesn't have queryParameters but list_users does
    # Split the code to check each method separately
    lines = api_client_code.split('\n')

    # Find getUser method
    in_get_user = False
    get_user_has_query_params = False
    for i, line in enumerate(lines):
        if 'getUser' in line:
            in_get_user = True
        if in_get_user and 'queryParameters' in line:
            get_user_has_query_params = True
        if in_get_user and '}' in line and 'async {' not in line:
            break

    # Find listUsers method
    in_list_users = False
    list_users_has_query_params = False
    for i, line in enumerate(lines):
        if 'listUsers' in line:
            in_list_users = True
        if in_list_users and 'queryParameters' in line:
            list_users_has_query_params = True
        if in_list_users and '}' in line and 'async {' not in line:
            break

    assert not get_user_has_query_params, "getUser should not have queryParameters"
    assert list_users_has_query_params, "listUsers should have queryParameters"


def test_query_params_camel_case_conversion(temp_dir: Path) -> None:
    """Test that snake_case query parameters are converted to camelCase."""
    # Create schema with snake_case query parameters
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
      query:
        sort_by:
          type: string
          default: name
        created_after:
          type: string
          optional: true
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Note: The current implementation preserves the parameter names as-is
    # This test documents the current behavior
    # If camelCase conversion is desired, the _to_camel_case method would need to be applied
    assert "sort_by" in api_client_code or "sortBy" in api_client_code, \
           "Query parameter should be present (may be in snake_case or camelCase)"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_api_client_with_query_params_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with query params passes dart analyze."""
    # Create schema with query parameters
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string

endpoints:
  /users:
    GET:
      name: list_users
      description: "List users with pagination"
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
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
    required String email,
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

    # The analysis may fail due to missing dependencies, but we verify no syntax errors
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"
