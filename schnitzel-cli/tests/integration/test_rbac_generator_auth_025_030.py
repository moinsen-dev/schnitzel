"""Integration tests for RBAC Permission Generator (auth_025-auth_030).

Tests for:
- auth_025: RBAC permission generator file exists with correct structure
- auth_026: RBAC permission template exists
- auth_027: RBAC generator creates role definitions from schema
- auth_028: RBAC generator creates permission checking utility
- auth_029: RBAC generator supports wildcard permissions
- auth_030: RBAC generator supports scoped permissions
"""

import pytest
import yaml
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, RoleConfig
from schnitzel.generators.python.auth.rbac import RBACPermissionGenerator


class TestRBACGeneratorStructure:
    """Tests for auth_025: RBAC permission generator file exists with correct structure."""

    def test_rbac_generator_class_exists(self):
        """Test that RBACPermissionGenerator class exists."""
        from schnitzel.generators.python.auth.rbac import RBACPermissionGenerator
        assert RBACPermissionGenerator is not None

    def test_rbac_generator_has_generate_method(self):
        """Test that generator has generate method."""
        generator = RBACPermissionGenerator()
        assert hasattr(generator, 'generate')
        assert callable(generator.generate)

    def test_rbac_generator_has_generate_to_file_method(self):
        """Test that generator has generate_to_file method."""
        generator = RBACPermissionGenerator()
        assert hasattr(generator, 'generate_to_file')
        assert callable(generator.generate_to_file)

    def test_rbac_generator_has_extract_roles_config_method(self):
        """Test that generator has _extract_roles_config method."""
        generator = RBACPermissionGenerator()
        assert hasattr(generator, '_extract_roles_config')
        assert callable(generator._extract_roles_config)

    def test_rbac_generator_is_exported_from_auth_module(self):
        """Test that RBACPermissionGenerator is exported from auth module."""
        from schnitzel.generators.python.auth import RBACPermissionGenerator
        assert RBACPermissionGenerator is not None


class TestRBACTemplate:
    """Tests for auth_026: RBAC permission template exists."""

    def test_rbac_template_file_exists(self):
        """Test that rbac.py.j2 template file exists."""
        template_path = Path(__file__).parent.parent.parent / "schnitzel-cli" / "src" / "schnitzel" / "templates" / "python" / "auth" / "rbac.py.j2"
        # Alternative path for running from project root
        if not template_path.exists():
            template_path = Path("schnitzel-cli/src/schnitzel/templates/python/auth/rbac.py.j2")
        if not template_path.exists():
            template_path = Path("src/schnitzel/templates/python/auth/rbac.py.j2")

        assert template_path.exists(), f"Template file not found at {template_path}"

    def test_template_can_be_loaded(self):
        """Test that template can be loaded by Jinja2."""
        generator = RBACPermissionGenerator()
        template = generator.env.get_template("auth/rbac.py.j2")
        assert template is not None

    def test_template_has_role_class(self):
        """Test that template defines Role class."""
        generator = RBACPermissionGenerator()
        template = generator.env.get_template("auth/rbac.py.j2")
        content = template.render(roles=[])
        assert "class Role:" in content or "@dataclass" in content

    def test_template_has_role_registry_class(self):
        """Test that template defines RoleRegistry class."""
        generator = RBACPermissionGenerator()
        template = generator.env.get_template("auth/rbac.py.j2")
        content = template.render(roles=[])
        assert "class RoleRegistry:" in content


class TestRoleDefinitionGeneration:
    """Tests for auth_027: RBAC generator creates role definitions from schema."""

    def test_generates_role_from_simple_schema(self):
        """Test role generation from simple schema."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(
                    name="admin",
                    description="Administrator",
                    permissions=["*"],
                    inherits=[]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "admin" in code
        assert "Administrator" in code
        assert '"*"' in code

    def test_generates_multiple_roles(self):
        """Test generation of multiple roles."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(
                    name="admin",
                    permissions=["*"]
                ),
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "admin" in code
        assert "user" in code
        assert '"*"' in code
        assert '"content:read"' in code

    def test_generates_role_with_inheritance(self):
        """Test role generation with inheritance."""
        schema = SchnitzelSchema(
            roles={
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["users:read"],
                    inherits=["user"]
                ),
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "moderator" in code
        assert "user" in code
        assert '"users:read"' in code
        assert "inherits" in code

    def test_generates_default_role_when_no_roles_defined(self):
        """Test that default role is generated when schema has no roles."""
        schema = SchnitzelSchema(roles=None)

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have default user role
        assert "user" in code.lower()

    def test_extract_roles_config_from_fixture(self):
        """Test extracting roles from YAML fixture."""
        # Load fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "rbac.yaml"
        with open(fixture_path) as f:
            schema_data = yaml.safe_load(f)

        schema = SchnitzelSchema(**schema_data)
        generator = RBACPermissionGenerator()
        roles = generator._extract_roles_config(schema)

        # Should have 4 roles from fixture
        assert len(roles) == 4
        role_names = [r["name"] for r in roles]
        assert "admin" in role_names
        assert "moderator" in role_names
        assert "user" in role_names
        assert "guest" in role_names

    def test_role_permissions_are_preserved(self):
        """Test that role permissions are correctly preserved."""
        schema = SchnitzelSchema(
            roles={
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["users:read", "content:*"],
                    inherits=[]
                )
            }
        )

        generator = RBACPermissionGenerator()
        roles = generator._extract_roles_config(schema)

        moderator = next(r for r in roles if r["name"] == "moderator")
        assert "users:read" in moderator["permissions"]
        assert "content:*" in moderator["permissions"]


class TestPermissionCheckingUtility:
    """Tests for auth_028: RBAC generator creates permission checking utility."""

    def test_generates_has_permission_function(self):
        """Test that has_permission function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "def has_permission" in code
        assert "user_roles" in code
        assert "permission" in code

    def test_generates_has_any_permission_function(self):
        """Test that has_any_permission function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "def has_any_permission" in code

    def test_generates_has_all_permissions_function(self):
        """Test that has_all_permissions function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "def has_all_permissions" in code

    def test_generates_require_permission_dependency(self):
        """Test that require_permission FastAPI dependency is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "def require_permission" in code
        assert "Depends" in code
        assert "HTTPException" in code

    def test_generated_code_has_role_registry(self):
        """Test that generated code has RoleRegistry class."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "RoleRegistry" in code
        assert "registry = RoleRegistry()" in code
        assert "register_role" in code


class TestWildcardPermissions:
    """Tests for auth_029: RBAC generator supports wildcard permissions."""

    def test_generates_wildcard_permission_check(self):
        """Test that wildcard permission checking is included."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have wildcard checking logic
        assert '"*"' in code
        assert "wildcard" in code.lower() or "*" in code

    def test_generates_admin_role_with_global_wildcard(self):
        """Test admin role with global wildcard."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(
                    name="admin",
                    description="Full access",
                    permissions=["*"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "admin" in code
        assert '"*"' in code

    def test_generates_partial_wildcard_support(self):
        """Test partial wildcard support (e.g., users:*)."""
        schema = SchnitzelSchema(
            roles={
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["content:*"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "content:*" in code or "content:\\*" in code

    def test_wildcard_checking_logic_in_template(self):
        """Test that template has wildcard checking logic."""
        generator = RBACPermissionGenerator()
        template = generator.env.get_template("auth/rbac.py.j2")
        content = template.render(roles=[])

        # Should have logic to check for wildcards
        assert '"*"' in content
        assert "split(" in content  # For parsing permission parts


class TestScopedPermissions:
    """Tests for auth_030: RBAC generator supports scoped permissions."""

    def test_generates_scoped_permission_examples(self):
        """Test that scoped permissions are handled in generated code."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read:own", "content:create:own"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "content:read:own" in code
        assert "content:create:own" in code

    def test_generates_resource_action_scope_format(self):
        """Test resource:action:scope format is preserved."""
        schema = SchnitzelSchema(
            roles={
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["users:read:*", "users:update:own"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check both permissions are in code
        assert "users:read:*" in code or "users:read:\\*" in code
        assert "users:update:own" in code

    def test_scoped_permission_parsing_logic(self):
        """Test that generated code has logic to parse scoped permissions."""
        generator = RBACPermissionGenerator()
        template = generator.env.get_template("auth/rbac.py.j2")
        content = template.render(roles=[])

        # Should have logic to split permissions by ":"
        assert "split(':')" in content or 'split(":")' in content

    def test_generates_complex_role_with_scoped_permissions(self):
        """Test complex role with multiple scoped permissions."""
        schema = SchnitzelSchema(
            roles={
                "moderator": RoleConfig(
                    name="moderator",
                    description="Moderator with scoped access",
                    permissions=[
                        "users:read",
                        "content:*",
                        "comments:delete:flagged",
                        "posts:edit:own"
                    ],
                    inherits=["user"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        assert "users:read" in code
        assert "content:*" in code or "content:\\*" in code
        assert "comments:delete:flagged" in code
        assert "posts:edit:own" in code


class TestGenerateToFile:
    """Test file generation functionality."""

    def test_generate_to_file_dry_run(self, tmp_path):
        """Test dry run mode doesn't write files."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        file_path, size = generator.generate_to_file(
            schema,
            tmp_path,
            dry_run=True
        )

        # File should not exist in dry run
        assert not file_path.exists()
        assert size > 0

    def test_generate_to_file_creates_file(self, tmp_path):
        """Test that file is created when not in dry run mode."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        file_path, size = generator.generate_to_file(
            schema,
            tmp_path,
            dry_run=False
        )

        # File should exist
        assert file_path.exists()
        assert file_path.name == "rbac.py"

        # Read and verify content
        content = file_path.read_text()
        assert "Generated by Schnitzel Framework" in content
        assert "DO NOT EDIT" in content
        assert "user" in content

    def test_generate_to_file_with_custom_source(self, tmp_path):
        """Test file generation with custom source schema name."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"])
            }
        )

        generator = RBACPermissionGenerator()
        file_path, _ = generator.generate_to_file(
            schema,
            tmp_path,
            schema_source="custom.schnitzel.yaml"
        )

        content = file_path.read_text()
        assert "custom.schnitzel.yaml" in content


class TestCompleteRBACWorkflow:
    """End-to-end workflow tests."""

    def test_complete_rbac_generation_from_fixture(self, tmp_path):
        """Test complete RBAC generation from fixture file."""
        # Load fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "rbac.yaml"
        with open(fixture_path) as f:
            schema_data = yaml.safe_load(f)

        schema = SchnitzelSchema(**schema_data)
        generator = RBACPermissionGenerator()

        # Generate to file
        file_path, size = generator.generate_to_file(schema, tmp_path)

        # Verify file
        assert file_path.exists()
        content = file_path.read_text()

        # Check all roles from fixture are present
        assert "admin" in content
        assert "moderator" in content
        assert "user" in content
        assert "guest" in content

        # Check permissions
        assert '"*"' in content  # admin wildcard
        assert "users:read" in content
        assert "content:*" in content or "content:\\*" in content
        assert "content:read" in content
        assert "content:create:own" in content

    def test_generated_code_is_valid_python(self, tmp_path):
        """Test that generated code is valid Python syntax."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"]),
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        file_path, _ = generator.generate_to_file(schema, tmp_path)

        # Try to compile the generated Python code
        content = file_path.read_text()
        try:
            compile(content, str(file_path), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
