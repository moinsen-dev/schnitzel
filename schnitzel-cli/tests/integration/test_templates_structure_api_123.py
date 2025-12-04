"""Integration tests for API-123 - Templates directory includes all required Jinja2 templates.

Test Requirements:
1. Verify schnitzel-cli/src/schnitzel/templates/ directory exists
2. Verify python/ subdirectory with Pydantic, ORM, routes templates
3. Verify dart/ subdirectory with Freezed, API client templates
4. Verify infra/ subdirectory with Alembic migration templates
5. Verify all templates are valid Jinja2 syntax

This test ensures the templates directory structure is complete and all templates
are valid for code generation.
"""

import os
from pathlib import Path
import pytest
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError, StrictUndefined


@pytest.fixture
def templates_dir():
    """Get the path to the templates directory."""
    import schnitzel
    schnitzel_path = Path(schnitzel.__file__).parent
    return schnitzel_path / "templates"


@pytest.fixture
def jinja_env(templates_dir):
    """Create a Jinja2 environment for template validation."""
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


class TestTemplatesDirectoryStructure:
    """Test that the templates directory structure is complete."""

    def test_templates_directory_exists(self, templates_dir: Path) -> None:
        """Test that the templates directory exists."""
        assert templates_dir.exists(), \
            f"Templates directory should exist at {templates_dir}"
        assert templates_dir.is_dir(), \
            f"Templates path should be a directory: {templates_dir}"

    def test_python_subdirectory_exists(self, templates_dir: Path) -> None:
        """Test that the python/ subdirectory exists."""
        python_dir = templates_dir / "python"
        assert python_dir.exists(), \
            f"Python templates subdirectory should exist at {python_dir}"
        assert python_dir.is_dir(), \
            f"Python templates path should be a directory: {python_dir}"

    def test_dart_subdirectory_exists(self, templates_dir: Path) -> None:
        """Test that the dart/ subdirectory exists."""
        dart_dir = templates_dir / "dart"
        assert dart_dir.exists(), \
            f"Dart templates subdirectory should exist at {dart_dir}"
        assert dart_dir.is_dir(), \
            f"Dart templates path should be a directory: {dart_dir}"

    def test_infra_subdirectory_exists(self, templates_dir: Path) -> None:
        """Test that the infra/ subdirectory exists."""
        infra_dir = templates_dir / "infra"
        assert infra_dir.exists(), \
            f"Infra templates subdirectory should exist at {infra_dir}"
        assert infra_dir.is_dir(), \
            f"Infra templates path should be a directory: {infra_dir}"


class TestPythonTemplates:
    """Test that all required Python templates exist and are valid."""

    def test_pydantic_model_template_exists(self, templates_dir: Path) -> None:
        """Test that pydantic_model.py.j2 template exists."""
        template_file = templates_dir / "python" / "pydantic_model.py.j2"
        assert template_file.exists(), \
            f"Pydantic model template should exist at {template_file}"
        assert template_file.is_file(), \
            f"Pydantic model template should be a file: {template_file}"

    def test_orm_template_exists(self, templates_dir: Path) -> None:
        """Test that orm.py.j2 template exists."""
        template_file = templates_dir / "python" / "orm.py.j2"
        assert template_file.exists(), \
            f"ORM template should exist at {template_file}"
        assert template_file.is_file(), \
            f"ORM template should be a file: {template_file}"

    def test_routes_template_exists(self, templates_dir: Path) -> None:
        """Test that routes.py.j2 template exists."""
        template_file = templates_dir / "python" / "routes.py.j2"
        assert template_file.exists(), \
            f"Routes template should exist at {template_file}"
        assert template_file.is_file(), \
            f"Routes template should be a file: {template_file}"

    def test_pydantic_model_template_valid_jinja2(self, jinja_env: Environment) -> None:
        """Test that pydantic_model.py.j2 has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("python/pydantic_model.py.j2")
            assert template is not None, "Template should load successfully"
        except TemplateSyntaxError as e:
            pytest.fail(f"Pydantic model template has invalid Jinja2 syntax: {e}")

    def test_orm_template_valid_jinja2(self, jinja_env: Environment) -> None:
        """Test that orm.py.j2 has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("python/orm.py.j2")
            assert template is not None, "Template should load successfully"
        except TemplateSyntaxError as e:
            pytest.fail(f"ORM template has invalid Jinja2 syntax: {e}")

    def test_routes_template_valid_jinja2(self, jinja_env: Environment) -> None:
        """Test that routes.py.j2 has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("python/routes.py.j2")
            assert template is not None, "Template should load successfully"
        except TemplateSyntaxError as e:
            pytest.fail(f"Routes template has invalid Jinja2 syntax: {e}")

    def test_pydantic_model_template_renders(self, jinja_env: Environment) -> None:
        """Test that pydantic_model.py.j2 can render with sample data."""
        template = jinja_env.get_template("python/pydantic_model.py.j2")

        # Minimal context for rendering
        context = {
            "needs_future_annotations": False,
            "imports": ["from pydantic import BaseModel"],
            "models": [
                {
                    "name": "User",
                    "description": "A user model",
                    "fields": [
                        {
                            "name": "id",
                            "type": "int",
                            "default": None,
                            "optional": False,
                        },
                        {
                            "name": "name",
                            "type": "str",
                            "default": None,
                            "optional": False,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        try:
            output = template.render(**context)
            assert "class User(BaseModel):" in output, \
                "Rendered output should contain User class"
            assert "id: int" in output, "Rendered output should contain id field"
            assert "name: str" in output, "Rendered output should contain name field"
        except Exception as e:
            pytest.fail(f"Failed to render pydantic_model template: {e}")

    def test_orm_template_renders(self, jinja_env: Environment) -> None:
        """Test that orm.py.j2 can render with sample data."""
        template = jinja_env.get_template("python/orm.py.j2")

        # Minimal context for rendering
        context = {
            "needs_datetime": False,
            "needs_uuid": False,
            "needs_any": False,
            "needs_relationship": False,
            "models": [
                {
                    "name": "User",
                    "table_name": "users",
                    "description": "A user table",
                    "fields": [
                        {
                            "name": "id",
                            "type_hint": "int",
                            "column_def": "sa.Integer, primary_key=True",
                        },
                        {
                            "name": "name",
                            "type_hint": "str",
                            "column_def": "sa.String(255)",
                        },
                    ],
                    "foreign_keys": [],
                    "relationships": [],
                }
            ],
        }

        try:
            output = template.render(**context)
            assert "class User(Base):" in output, \
                "Rendered output should contain User class"
            assert '__tablename__ = "users"' in output, \
                "Rendered output should contain table name"
            assert "id: Mapped[int]" in output, "Rendered output should contain id field"
        except Exception as e:
            pytest.fail(f"Failed to render orm template: {e}")

    def test_routes_template_renders(self, jinja_env: Environment) -> None:
        """Test that routes.py.j2 can render with sample data."""
        template = jinja_env.get_template("python/routes.py.j2")

        # Minimal context for rendering
        context = {
            "imports": ["from fastapi import APIRouter"],
            "routes": [
                {
                    "method": "get",
                    "path": "/users",
                    "status_code": 200,
                    "operation_id": "list_users",
                    "function_name": "list_users",
                    "parameters": [],
                    "return_type": "list[User]",
                    "description": "List all users",
                }
            ],
        }

        try:
            output = template.render(**context)
            assert "router = APIRouter()" in output, \
                "Rendered output should contain router"
            assert "@router.get" in output, \
                "Rendered output should contain GET decorator"
            assert "async def list_users" in output, \
                "Rendered output should contain function definition"
        except Exception as e:
            pytest.fail(f"Failed to render routes template: {e}")


class TestDartTemplates:
    """Test that all required Dart templates exist and are valid."""

    def test_freezed_model_template_exists(self, templates_dir: Path) -> None:
        """Test that freezed_model.dart.j2 template exists."""
        template_file = templates_dir / "dart" / "freezed_model.dart.j2"
        assert template_file.exists(), \
            f"Freezed model template should exist at {template_file}"
        assert template_file.is_file(), \
            f"Freezed model template should be a file: {template_file}"

    def test_api_client_template_exists(self, templates_dir: Path) -> None:
        """Test that api_client.dart.j2 template exists."""
        template_file = templates_dir / "dart" / "api_client.dart.j2"
        assert template_file.exists(), \
            f"API client template should exist at {template_file}"
        assert template_file.is_file(), \
            f"API client template should be a file: {template_file}"

    def test_freezed_model_template_valid_jinja2(self, jinja_env: Environment) -> None:
        """Test that freezed_model.dart.j2 has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("dart/freezed_model.dart.j2")
            assert template is not None, "Template should load successfully"
        except TemplateSyntaxError as e:
            pytest.fail(f"Freezed model template has invalid Jinja2 syntax: {e}")

    def test_api_client_template_valid_jinja2(self, jinja_env: Environment) -> None:
        """Test that api_client.dart.j2 has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("dart/api_client.dart.j2")
            assert template is not None, "Template should load successfully"
        except TemplateSyntaxError as e:
            pytest.fail(f"API client template has invalid Jinja2 syntax: {e}")

    def test_freezed_model_template_renders(self, jinja_env: Environment) -> None:
        """Test that freezed_model.dart.j2 can render with sample data."""
        template = jinja_env.get_template("dart/freezed_model.dart.j2")

        # Minimal context for rendering
        context = {
            "imports": [],
            "filename": "models",
            "models": [
                {
                    "name": "User",
                    "description": "A user model",
                    "fields": [
                        {
                            "name": "id",
                            "type": "int",
                            "required": True,
                            "default": None,
                            "json_key": None,
                            "description": None,
                        },
                        {
                            "name": "name",
                            "type": "String",
                            "required": True,
                            "default": None,
                            "json_key": None,
                            "description": None,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        try:
            output = template.render(**context)
            assert "@freezed" in output, "Rendered output should contain @freezed"
            assert "abstract class User" in output, \
                "Rendered output should contain User class"
            assert "const factory User" in output, \
                "Rendered output should contain factory constructor"
            assert "fromJson" in output, \
                "Rendered output should contain fromJson method"
        except Exception as e:
            pytest.fail(f"Failed to render freezed_model template: {e}")

    def test_api_client_template_renders(self, jinja_env: Environment) -> None:
        """Test that api_client.dart.j2 can render with sample data."""
        template = jinja_env.get_template("dart/api_client.dart.j2")

        # Minimal context for rendering
        context = {
            "needs_models": False,
            "methods": [
                {
                    "name": "getUsers",
                    "description": "Get all users",
                    "return_type": "List<User>",
                    "params": "",
                    "http_method": "get",
                    "path": "/users",
                    "query_params": [],
                    "has_body": False,
                    "body_var": None,
                    "has_response": True,
                    "is_list_response": True,
                    "response_model": "User",
                }
            ],
        }

        try:
            output = template.render(**context)
            assert "class ApiClient" in output, \
                "Rendered output should contain ApiClient class"
            assert "final Dio _dio;" in output, \
                "Rendered output should contain Dio field"
            assert "Future<List<User>> getUsers" in output, \
                "Rendered output should contain getUsers method"
        except Exception as e:
            pytest.fail(f"Failed to render api_client template: {e}")


class TestInfraTemplates:
    """Test that all required infrastructure templates exist and are valid."""

    def test_alembic_migration_template_exists(self, templates_dir: Path) -> None:
        """Test that alembic_migration.py.j2 template exists."""
        template_file = templates_dir / "infra" / "alembic_migration.py.j2"
        assert template_file.exists(), \
            f"Alembic migration template should exist at {template_file}"
        assert template_file.is_file(), \
            f"Alembic migration template should be a file: {template_file}"

    def test_alembic_migration_template_valid_jinja2(self, jinja_env: Environment) -> None:
        """Test that alembic_migration.py.j2 has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("infra/alembic_migration.py.j2")
            assert template is not None, "Template should load successfully"
        except TemplateSyntaxError as e:
            pytest.fail(f"Alembic migration template has invalid Jinja2 syntax: {e}")

    def test_alembic_migration_template_renders(self, jinja_env: Environment) -> None:
        """Test that alembic_migration.py.j2 can render with sample data."""
        template = jinja_env.get_template("infra/alembic_migration.py.j2")

        # Minimal context for rendering
        context = {
            "migration_name": "create users table",
            "revision_id": "abc123",
            "down_revision": None,
            "create_date": "2025-01-01 12:00:00",
            "upgrade_operations": [
                "op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True))"
            ],
            "downgrade_operations": [
                "op.drop_table('users')"
            ],
        }

        try:
            output = template.render(**context)
            assert "revision = 'abc123'" in output, \
                "Rendered output should contain revision ID"
            assert "def upgrade() -> None:" in output, \
                "Rendered output should contain upgrade function"
            assert "def downgrade() -> None:" in output, \
                "Rendered output should contain downgrade function"
            assert "op.create_table" in output, \
                "Rendered output should contain create_table operation"
        except Exception as e:
            pytest.fail(f"Failed to render alembic_migration template: {e}")


class TestAllTemplatesAccessible:
    """Test that all templates are accessible as package resources."""

    def test_all_template_files_readable(self, templates_dir: Path) -> None:
        """Test that all .j2 template files are readable."""
        template_files = list(templates_dir.glob("**/*.j2"))
        assert len(template_files) >= 6, \
            f"Should have at least 6 template files, found {len(template_files)}"

        for template_file in template_files:
            assert os.access(template_file, os.R_OK), \
                f"Template file should be readable: {template_file}"

            # Try to read the file
            try:
                content = template_file.read_text()
                assert len(content) > 0, \
                    f"Template file should not be empty: {template_file}"
            except Exception as e:
                pytest.fail(f"Failed to read template file {template_file}: {e}")

    def test_template_files_count(self, templates_dir: Path) -> None:
        """Test that we have the expected number of template files."""
        python_templates = list((templates_dir / "python").glob("*.j2"))
        dart_templates = list((templates_dir / "dart").glob("*.j2"))
        infra_templates = list((templates_dir / "infra").glob("*.j2"))

        assert len(python_templates) >= 3, \
            f"Should have at least 3 Python templates, found {len(python_templates)}"
        assert len(dart_templates) >= 2, \
            f"Should have at least 2 Dart templates, found {len(dart_templates)}"
        assert len(infra_templates) >= 1, \
            f"Should have at least 1 infra template, found {len(infra_templates)}"

    def test_no_syntax_errors_in_any_template(self, jinja_env: Environment, templates_dir: Path) -> None:
        """Test that all templates can be loaded without Jinja2 syntax errors."""
        template_files = list(templates_dir.glob("**/*.j2"))
        errors = []

        for template_file in template_files:
            relative_path = template_file.relative_to(templates_dir)
            try:
                template = jinja_env.get_template(str(relative_path).replace("\\", "/"))
                assert template is not None
            except TemplateSyntaxError as e:
                errors.append(f"{relative_path}: {e}")

        if errors:
            pytest.fail(f"Found Jinja2 syntax errors in templates:\n" + "\n".join(errors))


class TestTemplateConsistency:
    """Test that templates follow consistent patterns and conventions."""

    def test_python_templates_use_consistent_variable_names(self, jinja_env: Environment, templates_dir: Path) -> None:
        """Test that Python templates use consistent variable naming."""
        # Check pydantic_model template by reading the source file
        pydantic_file = templates_dir / "python" / "pydantic_model.py.j2"
        pydantic_source = pydantic_file.read_text()
        assert "models" in pydantic_source, \
            "Pydantic template should use 'models' variable"

        # Check ORM template
        orm_file = templates_dir / "python" / "orm.py.j2"
        orm_source = orm_file.read_text()
        assert "models" in orm_source, \
            "ORM template should use 'models' variable"

    def test_dart_templates_use_consistent_variable_names(self, jinja_env: Environment, templates_dir: Path) -> None:
        """Test that Dart templates use consistent variable naming."""
        # Check freezed_model template by reading the source file
        freezed_file = templates_dir / "dart" / "freezed_model.dart.j2"
        freezed_source = freezed_file.read_text()
        assert "models" in freezed_source, \
            "Freezed template should use 'models' variable"

        # Check api_client template
        api_file = templates_dir / "dart" / "api_client.dart.j2"
        api_source = api_file.read_text()
        assert "methods" in api_source, \
            "API client template should use 'methods' variable"

    def test_templates_have_proper_file_extensions(self, templates_dir: Path) -> None:
        """Test that all templates have .j2 extension."""
        all_files = list(templates_dir.glob("**/*"))
        template_files = [f for f in all_files if f.is_file()]

        for template_file in template_files:
            assert template_file.suffix == ".j2", \
                f"Template file should have .j2 extension: {template_file}"
