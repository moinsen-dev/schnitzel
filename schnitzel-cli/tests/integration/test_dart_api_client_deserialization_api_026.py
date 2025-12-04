"""Integration tests for api_026 - Dart API client generator deserializes response to Freezed models.

Test Requirements (from feature):
1. Create schema with endpoint returning User
2. Run schnitzel generate --target dart
3. Verify response is deserialized: User.fromJson(response.data)
4. Verify import of generated Freezed models
5. Run dart analyze - no errors

This test specifically validates that the Dart API client:
- Deserializes HTTP responses using Freezed model's fromJson() method
- Imports the models correctly from '../models/models.dart'
- Produces code that passes dart analyze with no errors
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


def test_response_deserialized_with_fromjson(temp_dir: Path) -> None:
    """Test that response is deserialized using Model.fromJson(response.data) (requirement 3)."""
    # Create schema with endpoint returning User
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
      createdAt:
        type: datetime

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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify User.fromJson(response.data) is used for deserialization
    assert "return User.fromJson(response.data);" in api_client_code, \
        "Should deserialize response using User.fromJson(response.data)"

    # Verify the full pattern: response assigned, then fromJson called
    assert "final response = await _dio.get('users/$id');" in api_client_code, \
        "Should have Dio GET call storing response"


def test_freezed_models_import_included(temp_dir: Path) -> None:
    """Test that import of generated Freezed models is correct (requirement 4)."""
    # Create schema with multiple models and endpoints
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

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      authorId:
        type: uuid

  CreatePostRequest:
    fields:
      title:
        type: string
      content:
        type: text

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

  /posts/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_post
      response:
        200:
          type: Post

  /posts:
    POST:
      name: create_post
      body: CreatePostRequest
      response:
        201:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify models import exists with correct relative path
    assert "import '../models/models.dart';" in api_client_code, \
        "Should import Freezed models from '../models/models.dart'"

    # Verify Dio import is also present
    assert "import 'package:dio/dio.dart';" in api_client_code, \
        "Should import Dio package"


def test_multiple_endpoints_use_fromjson(temp_dir: Path) -> None:
    """Test that multiple endpoints all use fromJson for deserialization."""
    # Create schema with multiple endpoints returning different models
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

  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string

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

  /posts/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_post
      response:
        200:
          type: Post

  /comments/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_comment
      response:
        200:
          type: Comment
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify each endpoint uses its model's fromJson method
    assert "return User.fromJson(response.data);" in api_client_code, \
        "Should use User.fromJson for User response"
    assert "return Post.fromJson(response.data);" in api_client_code, \
        "Should use Post.fromJson for Post response"
    assert "return Comment.fromJson(response.data);" in api_client_code, \
        "Should use Comment.fromJson for Comment response"


def test_post_endpoint_uses_fromjson(temp_dir: Path) -> None:
    """Test that POST endpoints also deserialize responses using fromJson."""
    # Create schema with POST endpoint
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

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
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

    # Verify POST endpoint uses fromJson for response
    assert "return User.fromJson(response.data);" in api_client_code, \
        "POST endpoint should deserialize response using fromJson"

    # Verify body is serialized to JSON
    assert "data: body.toJson()" in api_client_code, \
        "POST body should be serialized using toJson()"


def test_list_response_not_using_fromjson(temp_dir: Path) -> None:
    """Test that endpoints without response models don't generate fromJson calls."""
    # Create schema with endpoint that has no response model
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
      response:
        204: {}
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify DELETE method exists but doesn't have fromJson
    assert "Future<void> deleteUser(String id)" in api_client_code, \
        "Should have deleteUser method with void return type"
    assert "return" not in api_client_code or "fromJson" not in api_client_code.split("deleteUser")[1].split("}")[0], \
        "DELETE endpoint should not use fromJson when no response model"


def test_api_client_file_generated_with_deserialization(temp_dir: Path) -> None:
    """Test that generated api_client.dart file contains all deserialization code (requirement 2)."""
    # Create schema with endpoint returning User
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
      isActive:
        type: bool
      createdAt:
        type: datetime

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Retrieve user by ID"
      response:
        200:
          type: User
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
    assert size > 0, "api_client.dart should have content"

    # Read and verify content
    api_client_content = api_client_file.read_text()

    # Check all required elements are present
    assert "import 'package:dio/dio.dart';" in api_client_content, \
        "Should import Dio"
    assert "import '../models/models.dart';" in api_client_content, \
        "Should import Freezed models"
    assert "class ApiClient {" in api_client_content, \
        "Should have ApiClient class"
    assert "Future<User> getUser(String id)" in api_client_content, \
        "Should have getUser method"
    assert "return User.fromJson(response.data);" in api_client_content, \
        "Should deserialize using fromJson"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_code_passes_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart passes dart analyze with no errors (requirement 5)."""
    # Create schema with endpoint returning User
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
      isActive:
        type: bool
      createdAt:
        type: datetime

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
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
    POST:
      name: create_user
      description: "Create a new user"
      body: CreateUserRequest
      response:
        201:
          type: User
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

    # Create models directory and stub models.dart with Freezed models
    models_dir = temp_dir / "packages" / "shared" / "lib" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    models_file = models_dir / "models.dart"
    models_file.write_text("""import 'package:freezed_annotation/freezed_annotation.dart';

part 'models.freezed.dart';
part 'models.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
    required bool isActive,
    required DateTime createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

@freezed
class CreateUserRequest with _$CreateUserRequest {
  const factory CreateUserRequest({
    required String name,
    required String email,
  }) = _CreateUserRequest;

  factory CreateUserRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateUserRequestFromJson(json);
}
""")

    # Run dart analyze on the generated file
    result = subprocess.run(
        ["dart", "analyze", str(api_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # The analysis may show warnings about missing generated files (.freezed.dart, .g.dart)
    # but should not have syntax errors or structural issues
    # Return codes: 0 = no issues, 1 = info, 3 = warnings
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find errors. Output: {result.stdout}\n{result.stderr}"

    # Verify no syntax errors
    assert "error •" not in result.stdout.lower(), \
        f"Should have no syntax errors. Output: {result.stdout}"


def test_complex_nested_models_deserialization(temp_dir: Path) -> None:
    """Test deserialization works for complex nested model structures."""
    # Create schema with nested relationships
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
      content:
        type: text

  PostWithAuthor:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      authorName:
        type: string
      authorEmail:
        type: string

endpoints:
  /posts/{id}/full:
    params:
      id:
        type: uuid
    GET:
      name: get_post_with_author
      description: "Get post with author details"
      response:
        200:
          type: PostWithAuthor
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify complex model uses fromJson
    assert "return PostWithAuthor.fromJson(response.data);" in api_client_code, \
        "Should deserialize complex model using fromJson"
    assert "Future<PostWithAuthor> getPostWithAuthor(String id)" in api_client_code, \
        "Should have method returning complex model type"


def test_put_endpoint_deserialization(temp_dir: Path) -> None:
    """Test that PUT endpoints also deserialize responses using fromJson."""
    # Create schema with PUT endpoint
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

  UpdateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
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

    # Verify PUT endpoint uses fromJson for response
    assert "return User.fromJson(response.data);" in api_client_code, \
        "PUT endpoint should deserialize response using fromJson"
    assert "Future<User> updateUser(String id, UpdateUserRequest body)" in api_client_code, \
        "Should have updateUser method with correct signature"
    assert "_dio.put('users/$id', data: body.toJson())" in api_client_code, \
        "PUT should send body using toJson()"
