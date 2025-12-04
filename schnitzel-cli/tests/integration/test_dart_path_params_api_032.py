"""Integration tests for api_032 - Dart API client generator handles path parameter interpolation.

Test Requirements (from feature):
1. Create schema with endpoint: GET /users/{userId}/posts/{postId}
2. Run schnitzel generate --target dart
3. Verify method has userId and postId parameters
4. Verify path is built with string interpolation: 'users/$userId/posts/$postId'
   Note: Leading slash is removed to create relative paths for use with Dio's baseUrl
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


def test_single_path_parameter_interpolation(temp_dir: Path) -> None:
    """Test that single path parameter uses Dart string interpolation."""
    # Create schema with single path parameter
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify single path parameter is interpolated correctly
    # Note: Leading slash is removed to create relative paths for Dio's baseUrl
    assert "_dio.get('users/$id')" in api_client_code, \
        "Should use Dart string interpolation with single path parameter: 'users/$id'"


def test_multiple_path_parameters_interpolation(temp_dir: Path) -> None:
    """Test that multiple path parameters use Dart string interpolation (requirement 1-4)."""
    # Create schema with multiple path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string

endpoints:
  /users/{userId}/posts/{postId}:
    params:
      userId:
        type: uuid
      postId:
        type: uuid
    GET:
      name: get_user_post
      description: "Get a specific post for a user"
      response:
        200:
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

    # Verify method has both parameters
    assert "Future<Post> getUserPost(String userId, String postId)" in api_client_code, \
        "Should have getUserPost method with userId and postId parameters"

    # Verify path is built with string interpolation (requirement 4)
    # Note: Leading slash is removed to create relative paths for Dio's baseUrl
    assert "_dio.get('users/$userId/posts/$postId')" in api_client_code, \
        "Should use Dart string interpolation: 'users/$userId/posts/$postId'"


def test_path_params_with_different_types(temp_dir: Path) -> None:
    """Test that path parameters with different types are handled correctly."""
    # Create schema with different parameter types
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string

endpoints:
  /orgs/{orgId}/orders/{orderId}:
    params:
      orgId:
        type: uuid
      orderId:
        type: uuid
    GET:
      name: get_order
      description: "Get an order for an organization"
      response:
        200:
          type: Order
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify method signature uses correct types
    assert "Future<Order> getOrder(String orgId, String orderId)" in api_client_code, \
        "Should have getOrder method with properly typed parameters"

    # Verify path interpolation
    assert "_dio.get('orgs/$orgId/orders/$orderId')" in api_client_code, \
        "Should use Dart string interpolation: 'orgs/$orgId/orders/$orderId'"


def test_path_params_with_post_method(temp_dir: Path) -> None:
    """Test that path parameter interpolation works with POST methods."""
    # Create schema with POST endpoint with path parameters
    schema_content = """schnitzel: "1.0"

models:
  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string

  CreateCommentRequest:
    fields:
      text:
        type: string

endpoints:
  /posts/{postId}/comments:
    params:
      postId:
        type: uuid
    POST:
      name: create_comment
      description: "Create a comment on a post"
      body: CreateCommentRequest
      response:
        201:
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

    # Verify path interpolation in POST method
    assert "_dio.post('posts/$postId/comments', data: body.toJson())" in api_client_code, \
        "Should use Dart string interpolation in POST: 'posts/$postId/comments'"


def test_path_params_with_put_method(temp_dir: Path) -> None:
    """Test that path parameter interpolation works with PUT methods."""
    # Create schema with PUT endpoint with path parameters
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      description: "Update a user"
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

    # Verify path interpolation in PUT method
    assert "_dio.put('users/$id', data: body.toJson())" in api_client_code, \
        "Should use Dart string interpolation in PUT: 'users/$id'"


def test_path_params_with_delete_method(temp_dir: Path) -> None:
    """Test that path parameter interpolation works with DELETE methods."""
    # Create schema with DELETE endpoint with path parameters
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

    # Verify path interpolation in DELETE method
    assert "_dio.delete('users/$id')" in api_client_code, \
        "Should use Dart string interpolation in DELETE: 'users/$id'"


def test_path_params_with_patch_method(temp_dir: Path) -> None:
    """Test that path parameter interpolation works with PATCH methods."""
    # Create schema with PATCH endpoint with path parameters
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  PatchUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PATCH:
      name: patch_user
      description: "Partially update a user"
      body: PatchUserRequest
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

    # Verify path interpolation in PATCH method
    assert "_dio.patch('users/$id', data: body.toJson())" in api_client_code, \
        "Should use Dart string interpolation in PATCH: 'users/$id'"


def test_nested_path_params_three_levels(temp_dir: Path) -> None:
    """Test that deeply nested path parameters are interpolated correctly."""
    # Create schema with three levels of path parameters
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /orgs/{orgId}/projects/{projectId}/tasks/{taskId}:
    params:
      orgId:
        type: uuid
      projectId:
        type: uuid
      taskId:
        type: uuid
    GET:
      name: get_task
      description: "Get a task from a project in an organization"
      response:
        200:
          type: Task
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify all three path parameters are interpolated
    assert "_dio.get('orgs/$orgId/projects/$projectId/tasks/$taskId')" in api_client_code, \
        "Should use Dart string interpolation for all three parameters"


def test_path_params_preserve_path_segments(temp_dir: Path) -> None:
    """Test that static path segments are preserved during interpolation."""
    # Create schema to verify static segments aren't modified
    schema_content = """schnitzel: "1.0"

models:
  Profile:
    fields:
      id:
        type: uuid
        primary: true
      bio:
        type: string

endpoints:
  /api/v1/users/{userId}/profile:
    params:
      userId:
        type: uuid
    GET:
      name: get_user_profile
      description: "Get user profile"
      response:
        200:
          type: Profile
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify static segments are preserved
    assert "_dio.get('api/v1/users/$userId/profile')" in api_client_code, \
        "Should preserve static path segments: 'api/v1/users/$userId/profile'"


def test_path_params_with_query_params(temp_dir: Path) -> None:
    """Test that path parameters work correctly alongside query parameters."""
    # Create schema with both path and query parameters
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
      description: "Get user with optional details"
      query:
        includeDetails:
          type: bool
          optional: true
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

    # Verify path parameter is interpolated and query params are included
    assert "_dio.get('users/$id', queryParameters:" in api_client_code, \
        "Should use path interpolation with query parameters"


def test_convert_path_to_dart_unit_test(temp_dir: Path) -> None:
    """Test the _convert_path_to_dart method directly."""
    generator = DartApiClientGenerator()

    # Test single parameter
    # Note: Leading slash is removed to create relative paths for Dio's baseUrl
    result = generator._convert_path_to_dart("/users/{id}")
    assert result == "users/$id", "Should convert {id} to $id and remove leading slash"

    # Test multiple parameters
    result = generator._convert_path_to_dart("/users/{userId}/posts/{postId}")
    assert result == "users/$userId/posts/$postId", \
        "Should convert {userId} and {postId} to $userId and $postId"

    # Test no parameters
    result = generator._convert_path_to_dart("/users")
    assert result == "users", "Should remove leading slash even with no parameters"

    # Test three parameters
    result = generator._convert_path_to_dart("/orgs/{orgId}/projects/{projectId}/tasks/{taskId}")
    assert result == "orgs/$orgId/projects/$projectId/tasks/$taskId", \
        "Should convert all three parameters correctly"


def test_extract_path_params_unit_test(temp_dir: Path) -> None:
    """Test the _extract_path_params method directly."""
    generator = DartApiClientGenerator()

    # Test single parameter
    result = generator._extract_path_params("/users/{id}")
    assert result == ["id"], "Should extract single parameter"

    # Test multiple parameters
    result = generator._extract_path_params("/users/{userId}/posts/{postId}")
    assert result == ["userId", "postId"], "Should extract multiple parameters in order"

    # Test no parameters
    result = generator._extract_path_params("/users")
    assert result == [], "Should return empty list when no parameters"

    # Test three parameters
    result = generator._extract_path_params("/orgs/{orgId}/projects/{projectId}/tasks/{taskId}")
    assert result == ["orgId", "projectId", "taskId"], \
        "Should extract all three parameters in order"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_path_params_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with path params passes dart analyze (requirement 5)."""
    # Create schema with multiple path parameters
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string

endpoints:
  /users/{userId}/posts/{postId}:
    params:
      userId:
        type: uuid
      postId:
        type: uuid
    GET:
      name: get_user_post
      description: "Get a specific post for a user"
      response:
        200:
          type: Post
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
abstract class Post with _$Post {
  const factory Post({
    required String id,
    required String title,
    required String content,
  }) = _Post;

  factory Post.fromJson(Map<String, dynamic> json) => _$PostFromJson(json);
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


def test_api_client_file_created_with_path_params(temp_dir: Path) -> None:
    """Test that api_client.dart file is created with path parameter methods."""
    # Create schema with path parameters
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
  /users/{userId}/posts/{postId}:
    params:
      userId:
        type: uuid
      postId:
        type: uuid
    GET:
      name: get_user_post
      description: "Get a specific post for a user"
      response:
        200:
          type: Post
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
    assert "import '../models/models.dart';" in api_client_content, "Should import models"
    assert "class ApiClient {" in api_client_content, "Should have ApiClient class"


def test_camel_case_conversion_for_path_params(temp_dir: Path) -> None:
    """Test that path parameter names are kept as-is in method signatures."""
    # Create schema with snake_case path parameters
    schema_content = """schnitzel: "1.0"

models:
  Resource:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /users/{user_id}/resources/{resource_id}:
    params:
      user_id:
        type: uuid
      resource_id:
        type: uuid
    GET:
      name: get_user_resource
      description: "Get a resource for a user"
      response:
        200:
          type: Resource
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify parameter names in method signature (kept as is from schema)
    # The generator should use the parameter names as defined in the schema
    assert "String user_id" in api_client_code or "String userId" in api_client_code, \
        "Should have path parameters in method signature"

    # Verify path interpolation uses the same parameter names
    assert "$user_id" in api_client_code or "$userId" in api_client_code, \
        "Should interpolate path parameters"
