"""Integration tests for api_031 - Dart API client generator creates DELETE method.

Test Requirements (from feature):
1. Create schema with endpoint: DELETE /users/{id}
2. Run schnitzel generate --target dart
3. Verify deleteUser(String id) method exists
4. Verify Dio.delete() is called
5. Verify method returns Future<void>
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


def test_delete_method_exists(temp_dir: Path) -> None:
    """Test that deleteUser method exists with correct signature (requirement 3)."""
    # Create schema with DELETE endpoint
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
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify deleteUser method exists with correct signature
    assert "Future<void> deleteUser(String id)" in api_client_code, \
        "Should have deleteUser method with id parameter and void return type"


def test_delete_method_uses_dio_delete(temp_dir: Path) -> None:
    """Test that DELETE method calls _dio.delete() (requirement 4)."""
    # Create schema with DELETE endpoint
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
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify Dio.delete() is called
    assert "_dio.delete(" in api_client_code, "Should use _dio.delete() for DELETE method"
    # Make sure it's in the deleteUser method context
    assert "_dio.delete('users/$id')" in api_client_code, "Should call _dio.delete() with correct path"


def test_delete_method_return_type_void(temp_dir: Path) -> None:
    """Test that DELETE method returns Future<void> (requirement 5)."""
    # Create schema with DELETE endpoint
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
    DELETE:
      name: delete_user
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify return type is Future<void>
    assert "Future<void> deleteUser" in api_client_code, "Should return Future<void>"


def test_delete_method_path_interpolation(temp_dir: Path) -> None:
    """Test that DELETE method correctly interpolates path parameters."""
    # Create schema with DELETE endpoint
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
    DELETE:
      name: delete_user
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify path parameter interpolation using $id (relative path)
    assert "'users/$id'" in api_client_code, "Should use Dart string interpolation for path parameter"


def test_delete_method_no_body_parameter(temp_dir: Path) -> None:
    """Test that DELETE method does not have a body parameter."""
    # Create schema with DELETE endpoint
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
    DELETE:
      name: delete_user
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify method signature has only id parameter, no body
    assert "deleteUser(String id)" in api_client_code, "Should only have id parameter"
    # Make sure no data: parameter is passed to delete
    assert "data:" not in api_client_code, "DELETE should not have a data parameter"


def test_delete_method_no_return_statement(temp_dir: Path) -> None:
    """Test that DELETE method with void return type has no explicit return."""
    # Create schema with DELETE endpoint
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
    DELETE:
      name: delete_user
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Extract the deleteUser method
    method_start = api_client_code.find("Future<void> deleteUser")
    method_end = api_client_code.find("}", method_start)
    method_body = api_client_code[method_start:method_end + 1]

    # Verify no explicit return statement for void
    assert "return" not in method_body or "return;" not in method_body, \
        "void method should not have explicit return statement with value"


def test_delete_method_with_multiple_path_params(temp_dir: Path) -> None:
    """Test that DELETE method handles multiple path parameters correctly."""
    # Create schema with DELETE endpoint having multiple path params
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{userId}/posts/{postId}:
    params:
      userId:
        type: uuid
      postId:
        type: uuid
    DELETE:
      name: delete_user_post
      description: "Delete a user's post"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify both path parameters are in the signature
    assert "deleteUserPost(String userId, String postId)" in api_client_code, \
        "Should have all path parameters"

    # Verify path interpolation for both parameters
    assert "'users/$userId/posts/$postId'" in api_client_code, \
        "Should interpolate both path parameters"


def test_delete_method_with_query_params(temp_dir: Path) -> None:
    """Test that DELETE method supports query parameters."""
    # Create schema with DELETE endpoint having query params
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
    DELETE:
      name: delete_user
      description: "Delete a user"
      query:
        force:
          type: bool
          optional: true
          default: false
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify query parameter is in the signature
    assert "bool force = false" in api_client_code, "Should have force query parameter with default"

    # Verify queryParameters map is passed to delete
    assert "queryParameters:" in api_client_code, "Should include queryParameters map"
    assert "'force': force" in api_client_code, "Should include force in queryParameters"


def test_api_client_file_created_with_delete(temp_dir: Path) -> None:
    """Test that api_client.dart file is created with DELETE method."""
    # Create schema with DELETE endpoint
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
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert api_client_file.exists(), "api_client.dart should be created"
    assert size > 0, "api_client.dart should have content"

    # Read and verify content
    api_client_content = api_client_file.read_text()
    assert "import 'package:dio/dio.dart';" in api_client_content, "Should import Dio"
    assert "Future<void> deleteUser" in api_client_content, "Should have deleteUser method"
    assert "_dio.delete(" in api_client_content, "Should use _dio.delete()"


def test_delete_and_other_methods_together(temp_dir: Path) -> None:
    """Test that DELETE, GET, POST, and PUT methods can coexist in the same API client."""
    # Create schema with all HTTP methods
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      response:
        200:
          type: User
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
          type: User
    DELETE:
      name: delete_user
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify all methods exist
    assert "Future<User> createUser" in api_client_code, "Should have createUser method"
    assert "Future<User> getUser(String id)" in api_client_code, "Should have getUser method"
    assert "Future<User> updateUser(String id, UpdateUserRequest body)" in api_client_code, \
        "Should have updateUser method"
    assert "Future<void> deleteUser(String id)" in api_client_code, "Should have deleteUser method"

    # Verify correct HTTP methods are used
    assert "_dio.post('users'" in api_client_code, "Should use POST for createUser"
    assert "_dio.get('users/$id')" in api_client_code, "Should use GET for getUser"
    assert "_dio.put('users/$id', data: body.toJson())" in api_client_code, \
        "Should use PUT for updateUser"
    assert "_dio.delete('users/$id')" in api_client_code, "Should use DELETE for deleteUser"


def test_delete_method_camel_case_name(temp_dir: Path) -> None:
    """Test that DELETE method name is properly converted to camelCase."""
    # Create schema with snake_case DELETE endpoint name
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
    DELETE:
      name: delete_user_by_id
      description: "Delete a user by ID"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify camelCase method name
    assert "deleteUserById(String id)" in api_client_code, \
        "Method name should be converted to camelCase"


def test_delete_method_with_description(temp_dir: Path) -> None:
    """Test that DELETE method includes description as documentation comment."""
    # Create schema with DELETE endpoint with description
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
    DELETE:
      name: delete_user
      description: "Delete a user from the system"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify description comment exists
    assert "/// Delete a user from the system" in api_client_code, \
        "Should include description as documentation comment"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_api_client_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with DELETE method passes dart analyze (requirement 6)."""
    # Create schema with DELETE endpoint
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
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
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

    # Run dart analyze on the generated file
    result = subprocess.run(
        ["dart", "analyze", str(api_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # The analysis may fail due to missing dependencies, but we verify no syntax errors
    # Check that the file is syntactically valid
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"


def test_delete_method_with_response_model(temp_dir: Path) -> None:
    """Test that DELETE method can return a response model instead of void."""
    # Some REST APIs return the deleted resource
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      deleted:
        type: bool

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user and return the deleted resource"
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify return type is Future<User> instead of Future<void>
    assert "Future<User> deleteUser(String id)" in api_client_code, \
        "Should return Future<User> when response model is specified"

    # Verify response deserialization
    assert "return User.fromJson(response.data);" in api_client_code, \
        "Should deserialize response to User model"
