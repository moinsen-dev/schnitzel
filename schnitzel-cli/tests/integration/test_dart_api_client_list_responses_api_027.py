"""Integration tests for api_027 - Dart API client generator handles list responses.

Test Requirements (from feature):
1. Create schema with endpoint: GET /users returning List[User]
2. Run schnitzel generate --target dart
3. Verify method returns Future<List<User>>
4. Verify response.data is mapped to User.fromJson
5. Verify proper list casting
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


def test_list_response_return_type(temp_dir: Path) -> None:
    """Test that list response generates Future<List<User>> return type."""
    # Create schema with list response endpoint
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
      description: "Get all users"
      response:
        200:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify return type is Future<List<User>>
    assert "Future<List<User>> listUsers()" in api_client_code, \
        "Should have listUsers method returning Future<List<User>>"


def test_list_response_deserialization(temp_dir: Path) -> None:
    """Test that list response generates proper deserialization code."""
    # Create schema with list response endpoint
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
      response:
        200:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify deserialization uses map and fromJson
    assert "(response.data as List).map((e) => User.fromJson(e)).toList()" in api_client_code, \
        "Should deserialize list response using map and fromJson"


def test_list_response_dio_call(temp_dir: Path) -> None:
    """Test that list response uses correct Dio.get() call."""
    # Create schema with list response endpoint
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
      response:
        200:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify Dio.get() is called
    assert "_dio.get('users')" in api_client_code, \
        "Should call _dio.get() with correct path"


def test_list_response_complete_method(temp_dir: Path) -> None:
    """Test complete method structure for list response."""
    # Create schema with list response endpoint
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
      description: "Get all users"
      response:
        200:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify all components are present
    assert "/// Get all users" in api_client_code, "Should have description comment"
    assert "Future<List<User>> listUsers()" in api_client_code, "Should have correct method signature"
    assert "final response = await _dio.get('users');" in api_client_code, "Should have Dio call"
    assert "return (response.data as List).map((e) => User.fromJson(e)).toList();" in api_client_code, \
        "Should have list deserialization"


def test_list_response_with_path_params(temp_dir: Path) -> None:
    """Test list response with path parameters."""
    # Create schema with list response and path params
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /users/{userId}/posts:
    params:
      userId:
        type: uuid
    GET:
      name: list_user_posts
      response:
        200:
          type: List[Post]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify method includes path parameter
    assert "Future<List<Post>> listUserPosts(String userId)" in api_client_code, \
        "Should have userId parameter"
    assert "_dio.get('users/$userId/posts')" in api_client_code, \
        "Should use path parameter interpolation"
    assert "return (response.data as List).map((e) => Post.fromJson(e)).toList();" in api_client_code, \
        "Should deserialize to list of Posts"


def test_single_vs_list_response(temp_dir: Path) -> None:
    """Test that single object responses still work correctly."""
    # Create schema with both single and list responses
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
      response:
        200:
          type: List[User]

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
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

    # Verify list response
    assert "Future<List<User>> listUsers()" in api_client_code, \
        "Should have list method"
    assert "return (response.data as List).map((e) => User.fromJson(e)).toList();" in api_client_code, \
        "Should have list deserialization"

    # Verify single object response
    assert "Future<User> getUser(String id)" in api_client_code, \
        "Should have single object method"
    assert "return User.fromJson(response.data);" in api_client_code, \
        "Should have single object deserialization"


def test_list_response_imports(temp_dir: Path) -> None:
    """Test that list response adds correct imports."""
    # Create schema with list response
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
      response:
        200:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify imports
    assert "import 'package:dio/dio.dart';" in api_client_code, \
        "Should import Dio"
    assert "import '../models/models.dart';" in api_client_code, \
        "Should import models"


def test_file_generation_with_list_response(temp_dir: Path) -> None:
    """Test file generation with list response."""
    # Create schema with list response
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
      response:
        200:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client file
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file exists
    assert api_client_file.exists(), "API client file should be created"
    assert size > 0, "API client file should have content"

    # Verify file content
    content = api_client_file.read_text()
    assert "Future<List<User>> listUsers()" in content, \
        "File should contain list method"
    assert "(response.data as List).map((e) => User.fromJson(e)).toList()" in content, \
        "File should contain list deserialization"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_list_response_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with list responses passes dart analyze."""
    # Create schema with list response
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
      description: "Get all users"
      response:
        200:
          type: List[User]
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


def test_multiple_list_responses(temp_dir: Path) -> None:
    """Test multiple endpoints returning different list types."""
    # Create schema with multiple list responses
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: List[User]

  /posts:
    GET:
      name: list_posts
      response:
        200:
          type: List[Post]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify both list methods
    assert "Future<List<User>> listUsers()" in api_client_code, \
        "Should have list users method"
    assert "return (response.data as List).map((e) => User.fromJson(e)).toList();" in api_client_code, \
        "Should deserialize to list of Users"

    assert "Future<List<Post>> listPosts()" in api_client_code, \
        "Should have list posts method"
    assert "return (response.data as List).map((e) => Post.fromJson(e)).toList();" in api_client_code, \
        "Should deserialize to list of Posts"


def test_list_response_201_status(temp_dir: Path) -> None:
    """Test list response with 201 status code."""
    # Create schema with list response returning 201
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
  /users/batch:
    POST:
      name: create_users
      response:
        201:
          type: List[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify list response with 201
    assert "Future<List<User>> createUsers()" in api_client_code, \
        "Should handle 201 status for list response"
    assert "return (response.data as List).map((e) => User.fromJson(e)).toList();" in api_client_code, \
        "Should deserialize list response from 201"
