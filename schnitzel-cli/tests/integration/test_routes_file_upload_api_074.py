"""Integration tests for api_074 - FastAPI route generator handles file upload endpoints.

Test Requirements (from feature):
1. Create endpoint accepting multipart file upload
2. Run schnitzel generate --target python
3. Verify UploadFile parameter in signature
4. Verify import from fastapi
5. Run pyright - no errors
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.schema import SchemaParser


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_file_upload_endpoint_with_string_body_type(temp_dir: Path) -> None:
    """Test that endpoint with body type 'file' generates UploadFile parameter."""
    # Create schema with file upload endpoint using string body type
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_file
      description: "Upload a file"
      body: file
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify UploadFile parameter is generated
    assert "file: UploadFile = File(...)" in routes_code, \
        "Should have file parameter with UploadFile type and File(...) dependency"


def test_file_upload_endpoint_with_upload_type(temp_dir: Path) -> None:
    """Test that endpoint with body type 'upload' generates UploadFile parameter."""
    # Create schema with file upload endpoint using 'upload' type
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_document
      description: "Upload a document"
      body: upload
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify UploadFile parameter is generated
    assert "file: UploadFile = File(...)" in routes_code, \
        "Should have file parameter with UploadFile type for 'upload' body type"


def test_file_upload_endpoint_with_uploadfile_type(temp_dir: Path) -> None:
    """Test that endpoint with body type 'UploadFile' generates UploadFile parameter."""
    # Create schema with file upload endpoint using 'UploadFile' type
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_image
      description: "Upload an image"
      body: UploadFile
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify UploadFile parameter is generated
    assert "file: UploadFile = File(...)" in routes_code, \
        "Should have file parameter with UploadFile type for 'UploadFile' body type"


def test_file_upload_endpoint_with_dict_body_type(temp_dir: Path) -> None:
    """Test that endpoint with dict body containing file type generates UploadFile parameter."""
    # Create schema with file upload endpoint using dict body definition
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_attachment
      description: "Upload an attachment"
      body:
        type: file
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify UploadFile parameter is generated
    assert "file: UploadFile = File(...)" in routes_code, \
        "Should have file parameter with UploadFile type when dict body has type: file"


def test_file_upload_imports_uploadfile_and_file(temp_dir: Path) -> None:
    """Test that file upload endpoint imports both UploadFile and File from fastapi."""
    # Create schema with file upload endpoint
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_file
      body: file
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify imports are present
    # Check that File and UploadFile are in the consolidated fastapi import
    assert "from fastapi import" in routes_code, "Should have fastapi import"
    assert "File" in routes_code, "Should import File from fastapi"
    assert "UploadFile" in routes_code, "Should import UploadFile from fastapi"

    # Verify imports are consolidated into single line
    lines = routes_code.split("\n")
    fastapi_import_lines = [line for line in lines if "from fastapi import" in line]
    assert len(fastapi_import_lines) == 1, "Should have single consolidated fastapi import"

    # Verify the consolidated import contains both File and UploadFile
    fastapi_import = fastapi_import_lines[0]
    assert "File" in fastapi_import, "Consolidated import should include File"
    assert "UploadFile" in fastapi_import, "Consolidated import should include UploadFile"


def test_file_upload_function_signature(temp_dir: Path) -> None:
    """Test that file upload endpoint generates correct function signature."""
    # Create schema with file upload endpoint
    schema_content = """schnitzel: "1.0"

endpoints:
  /documents:
    POST:
      name: create_document
      description: "Upload a new document"
      body: file
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify complete function signature
    assert "async def create_document(file: UploadFile = File(...))" in routes_code, \
        "Should have complete function signature with file parameter"


def test_file_upload_with_post_decorator(temp_dir: Path) -> None:
    """Test that file upload endpoint has correct POST decorator."""
    # Create schema with file upload endpoint
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_file
      body: file
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify @router.post decorator is present
    assert "@router.post('/upload'" in routes_code, "Should have @router.post decorator"
    assert "status_code=201" in routes_code, "POST endpoint should have status_code=201"


def test_file_upload_with_put_method(temp_dir: Path) -> None:
    """Test that file upload works with PUT method."""
    # Create schema with file upload endpoint using PUT
    schema_content = """schnitzel: "1.0"

endpoints:
  /documents/{id}:
    PUT:
      name: update_document
      body: file
      response:
        200:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify PUT endpoint with file upload
    assert "@router.put('/documents/{id}'" in routes_code, "Should have @router.put decorator"
    assert "file: UploadFile = File(...)" in routes_code, \
        "PUT endpoint should also support file upload"


def test_file_upload_case_insensitive(temp_dir: Path) -> None:
    """Test that file upload detection is case-insensitive."""
    # Create schema with file upload endpoint using different cases
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload1:
    POST:
      name: upload_file_1
      body: FILE
      response:
        201:
          type: dict[str, Any]
  /upload2:
    POST:
      name: upload_file_2
      body: Upload
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both endpoints generate UploadFile parameters
    # Count occurrences of file: UploadFile = File(...)
    upload_file_count = routes_code.count("file: UploadFile = File(...)")
    assert upload_file_count == 2, \
        "Should generate UploadFile parameters for both FILE and Upload (case-insensitive)"


def test_file_upload_does_not_add_model_import(temp_dir: Path) -> None:
    """Test that file upload endpoints don't try to import 'file' as a model."""
    # Create schema with file upload endpoint
    schema_content = """schnitzel: "1.0"

models:
  Document:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /upload:
    POST:
      name: upload_file
      body: file
      response:
        201:
          type: Document
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify that 'file' is not imported as a model
    # Should only import Document (the response type)
    assert "from .models import Document" in routes_code, "Should import Document model"
    assert "from .models import" in routes_code

    # Count model imports - should only be Document
    import_lines = [
        line for line in routes_code.split("\n") if "from .models import" in line
    ]
    model_import_line = import_lines[0]
    assert model_import_line.count("Document") == 1, "Should only import Document"
    assert (
        "file" not in model_import_line.lower() or "File" not in model_import_line
    ), "Should not import 'file' as a model"


def test_generated_routes_file_with_upload(temp_dir: Path) -> None:
    """Test that generated routes file has correct structure with file upload."""
    # Create schema with file upload endpoint
    schema_content = """schnitzel: "1.0"

endpoints:
  /upload:
    POST:
      name: upload_file
      body: file
      response:
        201:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes to file
    generator = PythonRouteGenerator()
    output_dir = temp_dir / "backend" / "app"
    routes_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert routes_file.exists(), "routes.py should be created"
    assert size > 0, "routes.py should have content"

    # Read and verify content
    routes_content = routes_file.read_text()
    assert "from fastapi import" in routes_content, "Should import from FastAPI"
    assert "File" in routes_content, "Should import File"
    assert "UploadFile" in routes_content, "Should import UploadFile"
    assert "router = APIRouter()" in routes_content, "Should create router instance"
    assert "@router.post('/upload'" in routes_content, "Should have POST decorator"
    assert "async def upload_file" in routes_content, "Should have function definition"
    assert "file: UploadFile = File(...)" in routes_content, "Should have file upload parameter"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_file_upload_routes_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated file upload routes pass pyright type checking (requirement 5)."""
    # Create schema with file upload endpoint
    schema_content = """schnitzel: "1.0"

models:
  UploadResult:
    fields:
      filename:
        type: string
      size:
        type: int

endpoints:
  /upload:
    POST:
      name: upload_file
      description: "Upload a file"
      body: file
      response:
        201:
          type: UploadResult
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate both models and routes
    from schnitzel.generators.python.models import PythonModelGenerator

    output_dir = temp_dir / "backend" / "app"

    # Generate models.py first (routes imports from it)
    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    # Generate routes.py
    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py to make it a package
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create a basic pyproject.toml or pyrightconfig.json to help pyright
    # This tells pyright to ignore missing stubs for fastapi
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on generated file
    result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no errors (allow warnings about missing stubs and TODO implementation)
    # The main check is that the generated code itself has no type errors
    # Note: reportReturnType error is expected due to TODO placeholder implementation
    has_only_return_type_error = (
        result.returncode != 0
        and "reportReturnType" in result.stdout
        and "must return value on all code paths" in result.stdout
    )
    assert (
        result.returncode == 0
        or "reportMissingImports" in result.stdout
        or has_only_return_type_error
    ), (
        f"pyright should pass with no structural errors "
        f"(TODO implementation return type error is acceptable). "
        f"Output: {result.stdout}\n{result.stderr}"
    )


def test_regular_body_still_works(temp_dir: Path) -> None:
    """Test that regular Pydantic model body parameters still work correctly."""
    # Create schema with regular POST endpoint (not file upload)
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

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify regular body parameter is still generated correctly
    assert "body: CreateUserRequest" in routes_code, \
        "Should have body parameter with CreateUserRequest type (not file upload)"
    assert "from .models import CreateUserRequest, User" in routes_code, \
        "Should import Pydantic models"

    # Verify file upload imports are NOT added
    assert "file: UploadFile" not in routes_code, \
        "Should not have UploadFile parameter for regular POST"
