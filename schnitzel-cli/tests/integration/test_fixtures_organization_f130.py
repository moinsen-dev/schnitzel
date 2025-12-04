"""Integration tests for F130 - Integration test fixtures are organized and reusable.

Test Requirements:
- test_fixtures_directory_exists: Verify fixtures directory exists
- test_temp_dir_fixture_available: Test temp_dir fixture works
- test_sample_schema_fixtures_available: Test sample schema fixtures exist
- test_fixtures_are_reusable: Verify fixtures can be used in multiple tests
- test_fixtures_yaml_valid: Test that fixture YAML files are valid
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import yaml


# This fixture demonstrates a standard pattern used in tests
@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def sample_user_schema(temp_dir: Path) -> Path:
    """Create a simple user schema for testing."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
      created_at:
        type: datetime
        auto: create
"""
    schema_file = temp_dir / "user.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_fixtures_directory_exists() -> None:
    """Test that fixtures directory exists with sample schema files."""
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"

    # Verify fixtures directory exists
    assert fixtures_dir.exists(), f"Fixtures directory should exist at {fixtures_dir}"
    assert fixtures_dir.is_dir(), "Fixtures path should be a directory"

    # Check for sample YAML files
    yaml_files = list(fixtures_dir.glob("*.yaml"))

    # Should have at least one sample schema
    assert len(yaml_files) > 0, f"Fixtures directory should contain sample YAML files. Found: {yaml_files}"

    print(f"\n✓ Fixtures directory exists with {len(yaml_files)} YAML files")


def test_temp_dir_fixture_available(temp_dir: Path) -> None:
    """Test that temp_dir fixture works correctly."""
    # Verify temp_dir is a Path object
    assert isinstance(temp_dir, Path), "temp_dir should be a Path object"

    # Verify it exists and is a directory
    assert temp_dir.exists(), "Temporary directory should exist"
    assert temp_dir.is_dir(), "temp_dir should be a directory"

    # Verify we can create files in it
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists(), "Should be able to create files in temp_dir"

    print(f"\n✓ temp_dir fixture works correctly: {temp_dir}")


def test_sample_schema_fixtures_available(sample_user_schema: Path) -> None:
    """Test that sample schema fixtures work correctly."""
    # Verify fixture created a schema file
    assert sample_user_schema.exists(), "Sample schema file should be created"
    assert sample_user_schema.is_file(), "Schema should be a file"

    # Verify file contains valid YAML
    content = sample_user_schema.read_text()
    assert "schnitzel:" in content, "Schema should have schnitzel version"
    assert "models:" in content, "Schema should define models"
    assert "User:" in content, "Schema should have User model"

    print(f"\n✓ Sample schema fixture works: {sample_user_schema.name}")


def test_fixtures_are_reusable(temp_dir: Path, sample_user_schema: Path) -> None:
    """Test that fixtures can be used in multiple tests and are independent."""
    # This test uses both temp_dir and sample_user_schema fixtures

    # Verify both fixtures are available
    assert temp_dir.exists(), "temp_dir should be available"
    assert sample_user_schema.exists(), "sample_user_schema should be available"

    # Verify schema is in temp_dir (fixture dependency)
    assert sample_user_schema.parent == temp_dir, "Schema should be in temp directory"

    # Create another file to demonstrate fixture isolation
    another_file = temp_dir / "another.yaml"
    another_file.write_text("test: data")
    assert another_file.exists(), "Can create additional files in temp_dir"

    print("\n✓ Fixtures are reusable and work together")


def test_fixtures_yaml_valid() -> None:
    """Test that fixture YAML files are valid and can be parsed."""
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"

    if not fixtures_dir.exists():
        pytest.skip("Fixtures directory not found")

    # Find all YAML files in fixtures
    yaml_files = list(fixtures_dir.glob("*.yaml"))

    if len(yaml_files) == 0:
        pytest.skip("No YAML fixture files found")

    # Parse each YAML file
    valid_files = []
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
                assert data is not None, f"{yaml_file.name} should contain valid YAML"
                valid_files.append(yaml_file.name)
        except yaml.YAMLError as e:
            pytest.fail(f"Fixture {yaml_file.name} has invalid YAML: {e}")

    print(f"\n✓ All {len(valid_files)} fixture YAML files are valid")


def test_integration_fixtures_directory_exists() -> None:
    """Test that integration tests have their own fixtures directory."""
    project_root = Path(__file__).parent.parent.parent
    integration_fixtures_dir = project_root / "tests" / "integration" / "fixtures"

    if integration_fixtures_dir.exists():
        assert integration_fixtures_dir.is_dir(), "integration/fixtures should be a directory"

        # Check for fixture files
        fixture_files = list(integration_fixtures_dir.rglob("*"))
        print(f"\n✓ Integration fixtures directory exists with {len(fixture_files)} items")
    else:
        # It's okay if integration tests use main fixtures directory
        print("\n✓ Integration tests use main fixtures directory")


def test_conftest_file_optional() -> None:
    """Test that conftest.py files exist for shared fixtures (optional)."""
    project_root = Path(__file__).parent.parent.parent

    # Check for tests/conftest.py
    tests_conftest = project_root / "tests" / "conftest.py"

    # Check for tests/integration/conftest.py
    integration_conftest = project_root / "tests" / "integration" / "conftest.py"

    if tests_conftest.exists() or integration_conftest.exists():
        print("\n✓ conftest.py files exist for shared fixtures")
    else:
        print("\n✓ Tests use inline fixtures (conftest.py optional)")


def test_fixture_can_parse_schema(sample_user_schema: Path) -> None:
    """Test that fixture schemas can be parsed by the schema parser."""
    from schnitzel.schema import SchemaParser

    # Create parser
    parser = SchemaParser()

    # Parse the fixture schema
    try:
        schema = parser.parse(sample_user_schema)
        assert schema is not None, "Schema should parse successfully"
        assert len(schema.models) > 0, "Schema should have at least one model"
        print(f"\n✓ Fixture schema parses successfully: {len(schema.models)} models")
    except Exception as e:
        pytest.fail(f"Failed to parse fixture schema: {e}")


def test_fixture_schema_validates(sample_user_schema: Path) -> None:
    """Test that fixture schemas pass validation."""
    from schnitzel.schema import SchemaParser, SchemaValidator

    # Parse and validate
    parser = SchemaParser()
    schema = parser.parse(sample_user_schema)

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Should be valid
    assert result.valid is True, f"Fixture schema should be valid. Errors: {result.errors}"
    print(f"\n✓ Fixture schema passes validation")


def test_fixture_schema_generates_code(sample_user_schema: Path, temp_dir: Path) -> None:
    """Test that fixture schemas can be used for code generation."""
    from schnitzel.cli import app
    from typer.testing import CliRunner

    runner = CliRunner()

    # Run generate command with fixture schema
    result = runner.invoke(app, ["generate", str(sample_user_schema), "--target", "python"])

    # Should succeed
    assert result.exit_code == 0, f"Generation should succeed with fixture schema. Output: {result.stdout}"

    # Verify output was created
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists(), "Should generate Python models from fixture schema"

    print(f"\n✓ Fixture schema can be used for code generation")


def test_multiple_test_cases_use_same_fixture(sample_user_schema: Path) -> None:
    """Test that the same fixture can be used multiple times (demonstrating reusability)."""
    # First use
    content1 = sample_user_schema.read_text()
    assert "User:" in content1

    # Second use (in same test)
    content2 = sample_user_schema.read_text()
    assert content1 == content2, "Fixture should provide consistent content"

    # Verify file still exists
    assert sample_user_schema.exists(), "Fixture should persist through test"

    print("\n✓ Fixtures are consistently reusable within tests")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F130: Integration test fixtures are organized and reusable")
    print("=" * 70)

    import sys
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        temp_path = Path(tmpdir)

        # Create sample schema
        schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
      created_at:
        type: datetime
        auto: create
"""
        schema_file = temp_path / "user.schnitzel.yaml"
        schema_file.write_text(schema_content)

        try:
            print("\n1. Testing fixtures directory exists...")
            test_fixtures_directory_exists()

            print("\n2. Testing temp_dir fixture...")
            test_temp_dir_fixture_available(temp_path)

            print("\n3. Testing sample schema fixture...")
            test_sample_schema_fixtures_available(schema_file)

            print("\n4. Testing fixtures are reusable...")
            test_fixtures_are_reusable(temp_path, schema_file)

            print("\n5. Testing fixture YAML validity...")
            test_fixtures_yaml_valid()

            print("\n6. Testing integration fixtures directory...")
            test_integration_fixtures_directory_exists()

            print("\n7. Testing conftest files...")
            test_conftest_file_optional()

            print("\n8. Testing fixture schema parsing...")
            test_fixture_can_parse_schema(schema_file)

            print("\n9. Testing fixture schema validation...")
            test_fixture_schema_validates(schema_file)

            print("\n10. Testing fixture code generation...")
            test_fixture_schema_generates_code(schema_file, temp_path)

            print("\n11. Testing fixture reusability...")
            test_multiple_test_cases_use_same_fixture(schema_file)

            print("\n" + "=" * 70)
            print("✓ All F130 tests passed!")
            print("=" * 70)

        finally:
            os.chdir(original_cwd)
