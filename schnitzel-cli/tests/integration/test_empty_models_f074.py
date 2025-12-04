"""Integration tests for F074: Schema parser handles empty models section gracefully."""

import tempfile
from pathlib import Path

import pytest

from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.models import SchnitzelSchema
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.dart.models import DartModelGenerator


class TestEmptyModelsF074:
    """Test that schema parser handles empty models section gracefully."""

    def test_parse_empty_models_dict(self) -> None:
        """
        Test that models: {} parses successfully.

        Requirements:
        - Parser should handle schema with empty models: {}
        - Should return valid schema with no models
        - Should not crash or raise unexpected errors

        Steps:
        1. Create a YAML schema with models: {}
        2. Parse the schema
        3. Verify schema object is returned
        4. Verify schema.models is an empty dict
        5. Verify no errors are raised
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "empty_models.yaml"

            # Step 1: Create YAML with empty models dict
            content = """
schnitzel: 1.0.0
meta:
  name: test-app
  version: 0.1.0
  org: test
models: {}
"""
            schema_path.write_text(content)

            # Step 2: Parse the schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3: Verify schema object is returned
            assert schema is not None
            assert isinstance(schema, SchnitzelSchema)

            # Step 4: Verify schema.models is an empty dict
            assert isinstance(schema.models, dict)
            assert len(schema.models) == 0
            assert schema.models == {}

            # Step 5: No errors raised (test completes successfully)

    def test_parse_null_models(self) -> None:
        """
        Test that models: null or missing models works.

        Requirements:
        - Parser should handle schema with models: null
        - Should return valid schema with empty models dict
        - Should not crash or raise unexpected errors

        Steps:
        1. Create a YAML schema with models: null
        2. Parse the schema
        3. Verify schema object is returned
        4. Verify schema.models is an empty dict (not None)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "null_models.yaml"

            # Step 1: Create YAML with null models
            content = """
schnitzel: 1.0.0
meta:
  name: test-app
  version: 0.1.0
  org: test
models: null
"""
            schema_path.write_text(content)

            # Step 2: Parse the schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3: Verify schema object is returned
            assert schema is not None
            assert isinstance(schema, SchnitzelSchema)

            # Step 4: Verify schema.models is an empty dict (not None)
            assert isinstance(schema.models, dict)
            assert len(schema.models) == 0
            assert schema.models == {}

    def test_parse_missing_models(self) -> None:
        """
        Test that schema without models key works.

        Requirements:
        - Parser should handle schema without models key
        - Should return valid schema with empty models dict
        - Should not crash or raise unexpected errors

        Steps:
        1. Create a YAML schema without models key
        2. Parse the schema
        3. Verify schema object is returned
        4. Verify schema.models is an empty dict
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "no_models.yaml"

            # Step 1: Create YAML without models key
            content = """
schnitzel: 1.0.0
meta:
  name: test-app
  version: 0.1.0
  org: test
"""
            schema_path.write_text(content)

            # Step 2: Parse the schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 3: Verify schema object is returned
            assert schema is not None
            assert isinstance(schema, SchnitzelSchema)

            # Step 4: Verify schema.models is an empty dict
            assert isinstance(schema.models, dict)
            assert len(schema.models) == 0
            assert schema.models == {}

    def test_empty_models_validation_passes(self) -> None:
        """
        Test that validation accepts empty models.

        Requirements:
        - Validation should pass (empty is valid)
        - No validation errors should be raised

        Steps:
        1. Create a YAML schema with empty models
        2. Parse the schema (which includes validation)
        3. Verify no validation errors are raised
        4. Verify schema passes all validation checks
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "empty_validated.yaml"

            # Step 1: Create YAML with empty models
            content = """
schnitzel: 1.0.0
meta:
  name: test-app
  version: 0.1.0
  org: test
  description: Test app with no models
models: {}
"""
            schema_path.write_text(content)

            # Step 2-3: Parse and verify no errors
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 4: Verify schema is valid
            assert schema is not None
            assert schema.schnitzel == "1.0.0"
            assert schema.meta is not None
            assert schema.meta.name == "test-app"
            assert len(schema.models) == 0

    def test_generate_python_with_empty_models(self) -> None:
        """
        Test that Python generator produces minimal output with empty models.

        Requirements:
        - Generation should produce minimal output
        - Should not crash with empty models
        - Generated code should be valid Python

        Steps:
        1. Create a schema with empty models
        2. Generate Python code
        3. Verify generation succeeds
        4. Verify generated code contains only imports (no model classes)
        5. Verify generated code is valid Python syntax
        """
        # Step 1: Create schema with empty models
        schema = SchnitzelSchema(
            schnitzel="1.0.0",
            models={}
        )

        # Step 2: Generate Python code
        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Step 3: Verify generation succeeds
        assert code is not None
        assert isinstance(code, str)
        assert len(code) > 0

        # Step 4: Verify minimal output (only imports, no model classes)
        assert "from pydantic import BaseModel" in code
        # Should not contain any class definitions
        assert "class " not in code or code.count("class ") == 0

        # Step 5: Verify valid Python syntax by compiling
        compile(code, "<string>", "exec")

    def test_generate_dart_with_empty_models(self) -> None:
        """
        Test that Dart generator produces minimal output with empty models.

        Requirements:
        - Generation should produce minimal output
        - Should not crash with empty models
        - Generated code should be valid Dart

        Steps:
        1. Create a schema with empty models
        2. Generate Dart code
        3. Verify generation succeeds
        4. Verify generated code contains minimal content
        5. Verify no model classes are generated
        """
        # Step 1: Create schema with empty models
        schema = SchnitzelSchema(
            schnitzel="1.0.0",
            models={}
        )

        # Step 2: Generate Dart code
        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Step 3: Verify generation succeeds
        assert code is not None
        assert isinstance(code, str)
        assert len(code) > 0

        # Step 4-5: Verify minimal output (no model classes)
        # Should not contain any class definitions
        assert "class " not in code or code.count("class ") == 0

    def test_empty_models_schema_structure(self) -> None:
        """
        Test that returned schema has correct structure with empty models.

        Requirements:
        - Returned schema should have empty dict for models
        - Schema should be properly structured
        - All other schema fields should work normally

        Steps:
        1. Create and parse schema with empty models but other sections
        2. Verify models field is empty dict
        3. Verify other schema sections are preserved
        4. Verify schema structure is valid
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "structured.yaml"

            # Step 1: Create YAML with empty models but other sections
            content = """
schnitzel: 1.0.0
meta:
  name: test-app
  version: 0.1.0
  org: test
  description: App with no models yet
  docs: https://example.com
models: {}
auth:
  enabled: true
"""
            schema_path.write_text(content)

            # Parse the schema
            parser = SchemaParser()
            schema = parser.parse(schema_path)

            # Step 2: Verify models field is empty dict
            assert isinstance(schema.models, dict)
            assert len(schema.models) == 0

            # Step 3: Verify other sections are preserved
            assert schema.schnitzel == "1.0.0"
            assert schema.meta is not None
            assert schema.meta.name == "test-app"
            assert schema.meta.version == "0.1.0"
            assert schema.meta.org == "test"
            assert schema.meta.description == "App with no models yet"
            assert schema.auth is not None
            assert schema.auth.get("enabled") is True

            # Step 4: Schema structure is valid (test completes successfully)

    def test_empty_models_with_imports(self) -> None:
        """
        Test that empty models work correctly with import system.

        Requirements:
        - Empty models should work with imports
        - Imported files can have empty models
        - Should not crash during import resolution

        Steps:
        1. Create base schema with empty models
        2. Create importing schema that imports base
        3. Parse the importing schema
        4. Verify both schemas handle empty models correctly
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.yaml"
            main_path = Path(tmpdir) / "main.yaml"

            # Step 1: Create base schema with empty models
            base_content = """
schnitzel: 1.0.0
models: {}
"""
            base_path.write_text(base_content)

            # Step 2: Create importing schema
            main_content = """
schnitzel: 1.0.0
imports:
  - base.yaml
models: {}
"""
            main_path.write_text(main_content)

            # Step 3: Parse the importing schema
            parser = SchemaParser()
            schema = parser.parse(main_path)

            # Step 4: Verify empty models handled correctly
            assert schema is not None
            assert isinstance(schema.models, dict)
            assert len(schema.models) == 0
            assert "imports" not in schema.__dict__ or schema.imports is None

    def test_empty_models_file_generation(self) -> None:
        """
        Test that file generation works with empty models.

        Requirements:
        - generate_to_file should work with empty models
        - Generated files should be valid
        - Should not crash or produce errors

        Steps:
        1. Create schema with empty models
        2. Generate Python models to file
        3. Verify file is created
        4. Verify file contains valid Python code
        5. Verify file can be imported as Python module
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Step 1: Create schema with empty models
            schema = SchnitzelSchema(
                schnitzel="1.0.0",
                models={}
            )

            # Step 2: Generate to file
            generator = PythonModelGenerator()
            generated_path, line_count = generator.generate_to_file(
                schema,
                output_dir,
                schema_source="empty.yaml"
            )

            # Step 3: Verify file is created
            assert generated_path.exists()
            assert generated_path.is_file()

            # Step 4: Verify file contains valid Python code
            code = generated_path.read_text()
            assert len(code) > 0
            assert "from pydantic import BaseModel" in code

            # Step 5: Verify file can be compiled as Python
            compile(code, str(generated_path), "exec")
            assert line_count >= 0  # Should have some lines (at least imports)
