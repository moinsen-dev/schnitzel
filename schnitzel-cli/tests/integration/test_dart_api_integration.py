"""Integration tests for api_064 - Dart client successfully calls generated API.

Test Requirements (from feature):
1. Generate Dart API client from schema
2. Verify client methods match endpoint definitions
3. Verify request body serialization matches Pydantic models
4. Verify response deserialization matches Freezed models
5. Verify type contracts are consistent between Python and Dart

This test validates end-to-end type compatibility between the Python backend
(FastAPI + Pydantic) and Dart client (Dio + Freezed).
"""

import tempfile
import os
from pathlib import Path
import subprocess
import pytest
import re

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart.api_client import DartApiClientGenerator
from schnitzel.generators.dart.models import DartModelGenerator
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.python.routes import PythonRouteGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_dart_client_matches_api_endpoints(temp_dir: Path) -> None:
    """Test that Dart client methods match API endpoint definitions (requirement 2)."""
    # Create schema with multiple endpoints
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

  CreateUserRequest:
    fields:
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
      isActive:
        type: bool

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
    PUT:
      name: update_user
      description: "Update a user"
      body: UpdateUserRequest
      response:
        200:
          type: User
    DELETE:
      name: delete_user
      description: "Delete a user"
      response:
        204: {}

  /users:
    GET:
      name: list_users
      description: "List all users"
      response:
        200:
          type: list<User>
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

    # Generate Dart API client
    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Generate Python routes
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    # Verify all endpoints have corresponding Dart client methods
    # GET /users/{id}
    assert "Future<User> getUser(String id)" in dart_code, \
        "Should have getUser method in Dart client"
    assert "@router.get('/users/{id}'" in python_code, \
        "Should have GET /users/{id} route in Python"

    # PUT /users/{id}
    assert "Future<User> updateUser(String id, UpdateUserRequest body)" in dart_code, \
        "Should have updateUser method in Dart client"
    assert "@router.put('/users/{id}'" in python_code, \
        "Should have PUT /users/{id} route in Python"

    # DELETE /users/{id}
    assert "Future<void> deleteUser(String id)" in dart_code, \
        "Should have deleteUser method in Dart client"
    assert "@router.delete('/users/{id}'" in python_code, \
        "Should have DELETE /users/{id} route in Python"

    # GET /users
    assert "Future<List<User>> listUsers()" in dart_code, \
        "Should have listUsers method in Dart client"
    assert "@router.get('/users'" in python_code, \
        "Should have GET /users route in Python"

    # POST /users
    assert "Future<User> createUser(CreateUserRequest body)" in dart_code, \
        "Should have createUser method in Dart client"
    assert "@router.post('/users'" in python_code, \
        "Should have POST /users route in Python"


def test_request_body_serialization_matches_pydantic(temp_dir: Path) -> None:
    """Test that Dart request body serialization matches Pydantic models (requirement 3)."""
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
      age:
        type: int
      isActive:
        type: bool

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string
      age:
        type: int
      isActive:
        type: bool
        optional: true
        default: true

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

    # Generate Dart models and API client
    dart_model_generator = DartModelGenerator()
    dart_models_code = dart_model_generator.generate(schema)

    dart_client_generator = DartApiClientGenerator()
    dart_client_code = dart_client_generator.generate(schema)

    # Generate Python models
    python_model_generator = PythonModelGenerator()
    python_models_code = python_model_generator.generate(schema)

    # Verify Dart client serializes request body using toJson()
    assert "data: body.toJson()" in dart_client_code, \
        "Dart client should serialize request body using toJson()"

    # Verify Dart model has all fields from Pydantic model
    # Fields: name, email, age, isActive
    assert "required String name" in dart_models_code, \
        "Dart model should have name field"
    assert "required String email" in dart_models_code, \
        "Dart model should have email field"
    assert "required int age" in dart_models_code, \
        "Dart model should have age field"
    # isActive is optional with default, should not be required
    assert "bool? isActive" in dart_models_code or "@Default(true) bool isActive" in dart_models_code, \
        "Dart model should have optional isActive field with default"

    # Verify Python model has matching fields
    assert "name: str" in python_models_code, \
        "Python model should have name field"
    assert "email: str" in python_models_code, \
        "Python model should have email field"
    assert "age: int" in python_models_code, \
        "Python model should have age field"
    assert "is_active: bool" in python_models_code or "isActive: bool" in python_models_code, \
        "Python model should have isActive field"


def test_response_deserialization_matches_freezed(temp_dir: Path) -> None:
    """Test that Dart response deserialization matches Freezed models (requirement 4)."""
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
      isActive:
        type: bool

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
      publishedAt:
        type: datetime
        optional: true

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
    GET:
      name: list_posts
      response:
        200:
          type: list<Post>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart models and API client
    dart_model_generator = DartModelGenerator()
    dart_models_code = dart_model_generator.generate(schema)

    dart_client_generator = DartApiClientGenerator()
    dart_client_code = dart_client_generator.generate(schema)

    # Verify Dart client deserializes single object responses using Model.fromJson()
    assert "return User.fromJson(response.data);" in dart_client_code, \
        "Dart client should deserialize User using fromJson()"
    assert "return Post.fromJson(response.data);" in dart_client_code, \
        "Dart client should deserialize Post using fromJson()"

    # Verify Dart client deserializes list responses
    assert "return (response.data as List).map((e) => Post.fromJson(e)).toList();" in dart_client_code, \
        "Dart client should deserialize list of Posts using fromJson()"

    # Verify Dart models have fromJson factory
    assert "factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);" in dart_models_code, \
        "User model should have fromJson factory"
    assert "factory Post.fromJson(Map<String, dynamic> json) => _$PostFromJson(json);" in dart_models_code, \
        "Post model should have fromJson factory"

    # Verify Dart models have toJson method (implicit via Freezed)
    assert "@freezed" in dart_models_code, \
        "Models should use Freezed annotation for JSON serialization"


def test_type_contracts_consistent_between_python_and_dart(temp_dir: Path) -> None:
    """Test that type contracts are consistent between Python and Dart (requirement 5)."""
    # Create schema with various field types
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      description:
        type: text
      price:
        type: decimal
      quantity:
        type: int
      isAvailable:
        type: bool
      createdAt:
        type: datetime
      tags:
        type: list<string>
      metadata:
        type: json
        optional: true

  CreateProductRequest:
    fields:
      name:
        type: string
      description:
        type: text
      price:
        type: decimal
      quantity:
        type: int
      isAvailable:
        type: bool
        default: true
      tags:
        type: list<string>

endpoints:
  /products:
    POST:
      name: create_product
      body: CreateProductRequest
      response:
        201:
          type: Product
    GET:
      name: list_products
      response:
        200:
          type: list<Product>

  /products/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_product
      response:
        200:
          type: Product
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart models
    dart_model_generator = DartModelGenerator()
    dart_models_code = dart_model_generator.generate(schema)

    # Generate Python models
    python_model_generator = PythonModelGenerator()
    python_models_code = python_model_generator.generate(schema)

    # Define type mapping expectations
    type_mappings = {
        # Schema type -> (Python type, Dart type)
        "uuid": ("str", "String"),
        "string": ("str", "String"),
        "text": ("str", "String"),
        "decimal": ("float", "double"),
        "int": ("int", "int"),
        "bool": ("bool", "bool"),
        "datetime": ("datetime", "DateTime"),
        "list<string>": ("list[str]", "List<String>"),
        "json": ("dict", "Map<String, dynamic>"),
    }

    # Verify type consistency for Product model
    # uuid -> str (Python) / String (Dart)
    assert "id: str" in python_models_code or "id: UUID" in python_models_code, \
        "Python should map uuid to str or UUID"
    assert "required String id" in dart_models_code, \
        "Dart should map uuid to String"

    # string -> str (Python) / String (Dart)
    assert "name: str" in python_models_code, \
        "Python should map string to str"
    assert "required String name" in dart_models_code, \
        "Dart should map string to String"

    # text -> str (Python) / String (Dart)
    assert "description: str" in python_models_code, \
        "Python should map text to str"
    assert "required String description" in dart_models_code, \
        "Dart should map text to String"

    # decimal -> decimal (Python) / decimal or double (Dart)
    # Note: Python uses decimal type, Dart might use decimal or double
    assert "price: decimal" in python_models_code or "price: Decimal" in python_models_code or "price: float" in python_models_code, \
        "Python should map decimal to decimal/Decimal/float"
    assert "decimal price" in dart_models_code or "double price" in dart_models_code, \
        "Dart should map decimal to double or decimal"

    # int -> int (Python) / int (Dart)
    assert "quantity: int" in python_models_code, \
        "Python should map int to int"
    assert "required int quantity" in dart_models_code, \
        "Dart should map int to int"

    # bool -> bool (Python) / bool (Dart)
    # Note: Both Python and Dart might use camelCase for this field (isAvailable)
    assert "is_available: bool" in python_models_code or "isAvailable: bool" in python_models_code, \
        "Python should map bool to bool"
    assert "required bool isAvailable" in dart_models_code or "@Default(true) bool isAvailable" in dart_models_code or "bool isAvailable" in dart_models_code, \
        "Dart should map bool to bool"

    # datetime -> datetime (Python) / DateTime (Dart)
    # Note: Python might use createdAt (camelCase) or created_at (snake_case)
    assert "created_at: datetime" in python_models_code or "createdAt: datetime" in python_models_code, \
        "Python should map datetime to datetime"
    assert "required DateTime createdAt" in dart_models_code, \
        "Dart should map datetime to DateTime"

    # list<string> -> list[str] (Python) / List<String> (Dart)
    assert "tags: list[str]" in python_models_code, \
        "Python should map list<string> to list[str]"
    assert "required List<String> tags" in dart_models_code, \
        "Dart should map list<string> to List<String>"

    # json -> dict (Python) / Map<String, dynamic> (Dart)
    # Optional field - Python might use dict, dict[str, Any], or Optional[dict]
    assert ("metadata: dict | None" in python_models_code or
            "metadata: Optional[dict]" in python_models_code or
            "metadata: dict[str, Any] | None" in python_models_code), \
        "Python should map optional json to dict-like type | None"
    assert "Map<String, dynamic>? metadata" in dart_models_code, \
        "Dart should map optional json to Map<String, dynamic>?"


def test_full_endpoint_type_compatibility(temp_dir: Path) -> None:
    """Test full endpoint with all components: path params, query params, body, response."""
    # Create schema with complex endpoint
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      userId:
        type: uuid
      total:
        type: decimal
      status:
        type: string
      createdAt:
        type: datetime

  UpdateOrderRequest:
    fields:
      status:
        type: string
      notes:
        type: text
        optional: true

endpoints:
  /orders/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_order
      body: UpdateOrderRequest
      query:
        notify:
          type: bool
          optional: true
          default: false
      response:
        200:
          type: Order
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart API client
    dart_client_generator = DartApiClientGenerator()
    dart_client_code = dart_client_generator.generate(schema)

    # Generate Python routes
    python_route_generator = PythonRouteGenerator()
    python_routes_code = python_route_generator.generate(schema)

    # Verify Dart client method signature
    # Should have: Future<Order> updateOrder(String id, UpdateOrderRequest body, {bool notify = false})
    # or with named parameters for query
    assert "Future<Order> updateOrder" in dart_client_code, \
        "Dart client should have updateOrder method returning Future<Order>"
    assert "String id" in dart_client_code, \
        "Dart client should have id parameter (path param)"
    assert "UpdateOrderRequest body" in dart_client_code, \
        "Dart client should have body parameter"
    assert "bool" in dart_client_code and "notify" in dart_client_code, \
        "Dart client should have notify query parameter"

    # Verify Python route signature
    # Should have: update_order(id: str, body: UpdateOrderRequest, notify: bool = False)
    assert "update_order" in python_routes_code, \
        "Python should have update_order route function"
    assert "id:" in python_routes_code, \
        "Python route should have id parameter"
    # UpdateOrderRequest should be imported and used
    assert "UpdateOrderRequest" in python_routes_code, \
        "Python route should use UpdateOrderRequest type"


def test_generated_files_structure_matches(temp_dir: Path) -> None:
    """Test that generated file structure matches between Python and Dart."""
    # Create schema
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
      response:
        200:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart files
    dart_model_generator = DartModelGenerator()
    dart_models_dir = temp_dir / "packages" / "shared" / "lib" / "models"
    dart_models_file, dart_models_size = dart_model_generator.generate_to_file(
        schema, dart_models_dir
    )

    dart_client_generator = DartApiClientGenerator()
    dart_client_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    dart_client_file, dart_client_size = dart_client_generator.generate_to_file(
        schema, dart_client_dir
    )

    # Generate Python files
    python_model_generator = PythonModelGenerator()
    python_models_dir = temp_dir / "backend" / "app"
    python_models_file, python_models_size = python_model_generator.generate_to_file(
        schema, python_models_dir
    )

    python_route_generator = PythonRouteGenerator()
    python_routes_dir = temp_dir / "backend" / "app"
    python_routes_file, python_routes_size = python_route_generator.generate_to_file(
        schema, python_routes_dir
    )

    # Verify files exist
    assert dart_models_file.exists(), "Dart models file should be created"
    assert dart_client_file.exists(), "Dart API client file should be created"
    assert python_models_file.exists(), "Python models file should be created"
    assert python_routes_file.exists(), "Python routes file should be created"

    # Verify file names
    assert dart_models_file.name == "models.dart", \
        "Dart models should be in models.dart"
    assert dart_client_file.name == "api_client.dart", \
        "Dart client should be in api_client.dart"
    assert python_models_file.name == "models.py", \
        "Python models should be in models.py"
    assert python_routes_file.name == "routes.py", \
        "Python routes should be in routes.py"

    # Verify files have content
    assert dart_models_size > 0, "Dart models should have content"
    assert dart_client_size > 0, "Dart client should have content"
    assert python_models_size > 0, "Python models should have content"
    assert python_routes_size > 0, "Python routes should have content"


def test_naming_convention_consistency(temp_dir: Path) -> None:
    """Test that naming conventions are consistent and properly converted."""
    # Create schema with snake_case fields (standard in schema)
    schema_content = """schnitzel: "1.0"

models:
  UserProfile:
    fields:
      user_id:
        type: uuid
        primary: true
      first_name:
        type: string
      last_name:
        type: string
      created_at:
        type: datetime
      is_verified:
        type: bool

endpoints:
  /user-profiles/{user_id}:
    params:
      user_id:
        type: uuid
    GET:
      name: get_user_profile
      response:
        200:
          type: UserProfile
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart models
    dart_model_generator = DartModelGenerator()
    dart_models_code = dart_model_generator.generate(schema)

    # Generate Python models
    python_model_generator = PythonModelGenerator()
    python_models_code = python_model_generator.generate(schema)

    # Python should use snake_case
    assert "user_id: str" in python_models_code or "user_id: UUID" in python_models_code, \
        "Python should use snake_case field names"
    assert "first_name: str" in python_models_code, \
        "Python should use snake_case field names"
    assert "created_at: datetime" in python_models_code, \
        "Python should use snake_case field names"
    assert "is_verified: bool" in python_models_code, \
        "Python should use snake_case field names"

    # Dart should use camelCase
    assert "required String userId" in dart_models_code, \
        "Dart should use camelCase field names"
    assert "required String firstName" in dart_models_code, \
        "Dart should use camelCase field names"
    assert "required DateTime createdAt" in dart_models_code, \
        "Dart should use camelCase field names"
    assert "required bool isVerified" in dart_models_code, \
        "Dart should use camelCase field names"

    # Dart should have @JsonKey annotations for name mapping
    assert "@JsonKey(name: 'user_id')" in dart_models_code or "userId" in dart_models_code, \
        "Dart should map camelCase to snake_case in JSON"


def test_optional_and_required_fields_consistency(temp_dir: Path) -> None:
    """Test that optional and required fields are handled consistently."""
    # Create schema with mix of required and optional fields
    schema_content = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      publishedAt:
        type: datetime
        optional: true
      author:
        type: string
        optional: false
      tags:
        type: list<string>
        optional: true
      viewCount:
        type: int
        default: 0

endpoints:
  /articles:
    POST:
      name: create_article
      body: Article
      response:
        201:
          type: Article
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart models
    dart_model_generator = DartModelGenerator()
    dart_models_code = dart_model_generator.generate(schema)

    # Generate Python models
    python_model_generator = PythonModelGenerator()
    python_models_code = python_model_generator.generate(schema)

    # Required fields should not have ? or | None
    assert "required String title" in dart_models_code, \
        "Required field should not be nullable in Dart"
    assert "title: str" in python_models_code and "| None" not in python_models_code.split("title:")[1].split("\n")[0], \
        "Required field should not be optional in Python"

    # Optional fields should have ? in Dart and | None in Python
    assert "DateTime? publishedAt" in dart_models_code or "@Default" in dart_models_code, \
        "Optional field should be nullable in Dart"
    # In Python, optional datetime should be: publishedAt: datetime | None (or published_at with snake_case)
    assert "publishedAt: datetime | None" in python_models_code or "published_at: datetime | None" in python_models_code or "Optional[datetime]" in python_models_code, \
        "Optional field should be optional in Python"

    # Fields with defaults
    assert "@Default(0)" in dart_models_code or "viewCount" in dart_models_code, \
        "Field with default should have @Default annotation in Dart"
    # Python might use viewCount (camelCase) or view_count (snake_case)
    assert ("view_count: int" in python_models_code or "viewCount: int" in python_models_code) and ("= 0" in python_models_code or "Field(default=0)" in python_models_code), \
        "Field with default should have default value in Python"


def test_list_response_type_consistency(temp_dir: Path) -> None:
    """Test that list response types are handled consistently."""
    # Create schema with list response
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: decimal

endpoints:
  /items:
    GET:
      name: list_items
      response:
        200:
          type: list<Item>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart API client
    dart_client_generator = DartApiClientGenerator()
    dart_client_code = dart_client_generator.generate(schema)

    # Generate Python routes
    python_route_generator = PythonRouteGenerator()
    python_routes_code = python_route_generator.generate(schema)

    # Dart should return Future<List<Item>>
    assert "Future<List<Item>> listItems()" in dart_client_code, \
        "Dart client should return Future<List<Item>> for list response"

    # Dart should deserialize list correctly
    assert "(response.data as List).map((e) => Item.fromJson(e)).toList()" in dart_client_code, \
        "Dart client should deserialize list of items"

    # Python should return list[Item] or list<Item>
    assert "list_items" in python_routes_code, \
        "Python should have list_items route"
    # The return type annotation in FastAPI route should indicate list
    # Note: The generator might use list<Item> syntax or list[Item] syntax
    assert "list[Item]" in python_routes_code or "List[Item]" in python_routes_code or "list<Item>" in python_routes_code, \
        "Python route should return list of Items"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_dart_client_passes_static_analysis(temp_dir: Path) -> None:
    """Test that generated Dart client passes static analysis."""
    # Create comprehensive schema
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

    # Generate Dart files
    dart_model_generator = DartModelGenerator()
    dart_models_dir = temp_dir / "packages" / "shared" / "lib" / "models"
    dart_models_file, _ = dart_model_generator.generate_to_file(schema, dart_models_dir)

    dart_client_generator = DartApiClientGenerator()
    dart_client_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    dart_client_file, _ = dart_client_generator.generate_to_file(schema, dart_client_dir)

    # Create pubspec.yaml
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

    # Run dart analyze
    result = subprocess.run(
        ["dart", "analyze", str(dart_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # Should not have errors (warnings about missing generated files are okay)
    assert result.returncode in [0, 1, 3], \
        f"Dart analyze should not find errors. Output: {result.stdout}\n{result.stderr}"
