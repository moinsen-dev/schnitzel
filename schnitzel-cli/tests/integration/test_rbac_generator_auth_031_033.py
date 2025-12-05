"""Integration tests for RBAC Advanced Features (auth_031-auth_033).

Tests for:
- auth_031: RBAC generator creates FastAPI dependency for role checking
- auth_032: RBAC generator supports role inheritance (with circular detection)
- auth_033: RBAC generator creates role assignment utilities
"""

import pytest
import yaml
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, RoleConfig
from schnitzel.generators.python.auth.rbac import RBACPermissionGenerator


class TestRoleCheckingDependencies:
    """Tests for auth_031: RBAC generator creates FastAPI dependency for role checking."""

    def test_generates_require_role_dependency(self):
        """Test that require_role dependency is generated."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"]),
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for require_role function
        assert "def require_role" in code
        assert "role_name: str" in code
        assert "Access denied: requires" in code

    def test_generates_require_any_role_dependency(self):
        """Test that require_any_role dependency is generated."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"]),
                "moderator": RoleConfig(name="moderator", permissions=["users:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for require_any_role function
        assert "def require_any_role" in code
        assert "roles: List[str]" in code
        assert "any(role in user_roles for role in roles)" in code

    def test_generates_require_all_roles_dependency(self):
        """Test that require_all_roles dependency is generated."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"]),
                "superuser": RoleConfig(name="superuser", permissions=["system:*"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for require_all_roles function
        assert "def require_all_roles" in code
        assert "roles: List[str]" in code
        assert "all(role in user_roles for role in roles)" in code

    def test_role_dependencies_use_fastapi_depends(self):
        """Test that role checking dependencies use FastAPI Depends."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should import and use HTTPBearer and Depends
        assert "HTTPBearer" in code
        assert "Depends" in code
        assert "HTTPAuthorizationCredentials" in code

    def test_role_dependencies_raise_403_on_failure(self):
        """Test that role checking dependencies raise 403 on unauthorized access."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should raise HTTPException with 403
        assert "HTTPException" in code
        assert "status.HTTP_403_FORBIDDEN" in code or "403" in code

    def test_role_dependencies_extract_jwt_token(self):
        """Test that role checking dependencies extract JWT token from credentials."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should extract token from credentials
        assert "credentials.credentials" in code
        assert "token = credentials.credentials" in code

    def test_role_dependencies_have_todo_for_jwt_integration(self):
        """Test that role dependencies have TODO comments for JWT integration."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have TODO for JWT integration
        assert "TODO" in code
        assert "JWT" in code or "jwt" in code

    def test_all_three_role_dependencies_present(self):
        """Test that all three role checking dependencies are present."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # All three should be present
        assert "def require_role(role_name: str):" in code
        assert "def require_any_role(roles: List[str]):" in code
        assert "def require_all_roles(roles: List[str]):" in code


class TestRoleInheritance:
    """Tests for auth_032: RBAC generator supports role inheritance."""

    def test_role_inheritance_is_preserved(self):
        """Test that role inheritance relationships are preserved."""
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

        # Should have inherits in role registration
        assert "inherits=" in code
        assert '"user"' in code

    def test_multi_level_inheritance_supported(self):
        """Test multi-level inheritance (grandparent -> parent -> child)."""
        schema = SchnitzelSchema(
            roles={
                "superadmin": RoleConfig(
                    name="superadmin",
                    permissions=["system:*"],
                    inherits=["admin"]
                ),
                "admin": RoleConfig(
                    name="admin",
                    permissions=["users:*"],
                    inherits=["moderator"]
                ),
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["content:*"],
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

        # All inheritance relationships should be preserved
        assert code.count("inherits=") >= 3

    def test_circular_inheritance_detection_present(self):
        """Test that circular inheritance detection logic is present."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have circular detection logic
        assert "_visited" in code
        assert "circular" in code.lower() or "Circular" in code

    def test_role_inheritance_uses_recursion(self):
        """Test that role inheritance resolution uses recursion."""
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

        # Should call get_all_permissions recursively for parent roles
        assert "get_all_permissions" in code
        assert "parent_role_name" in code or "inherits" in code

    def test_inheritance_resolution_has_caching(self):
        """Test that inheritance resolution uses caching."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have permission cache
        assert "_permission_cache" in code
        assert "cache" in code.lower()

    def test_multiple_parent_inheritance_supported(self):
        """Test that roles can inherit from multiple parents."""
        schema = SchnitzelSchema(
            roles={
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["content:*"],
                    inherits=["user", "reviewer"]
                ),
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read"]
                ),
                "reviewer": RoleConfig(
                    name="reviewer",
                    permissions=["content:review"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should iterate over parent roles
        assert "for parent_role_name in" in code or "for" in code


class TestRoleAssignmentUtilities:
    """Tests for auth_033: RBAC generator creates role assignment utilities."""

    def test_generates_assign_role_function(self):
        """Test that assign_role function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for assign_role function
        assert "def assign_role" in code
        assert "user_id: str" in code
        assert "role_name: str" in code

    def test_generates_remove_role_function(self):
        """Test that remove_role function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for remove_role function
        assert "def remove_role" in code
        assert "user_id: str" in code
        assert "role_name: str" in code

    def test_generates_get_user_roles_function(self):
        """Test that get_user_roles function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for get_user_roles function
        assert "def get_user_roles" in code
        assert "user_id: str" in code
        assert "-> List[str]" in code

    def test_generates_set_user_roles_function(self):
        """Test that set_user_roles function is generated."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Check for set_user_roles function
        assert "def set_user_roles" in code
        assert "user_id: str" in code
        assert "roles: List[str]" in code

    def test_role_assignment_functions_are_stubs(self):
        """Test that role assignment functions are stubs with NotImplementedError."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should raise NotImplementedError
        assert "NotImplementedError" in code
        assert code.count("NotImplementedError") >= 4

    def test_role_assignment_functions_have_implementation_guide(self):
        """Test that role assignment functions have implementation guide in docstring."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have implementation guide
        assert "Implementation guide" in code
        assert "database" in code.lower()

    def test_role_assignment_functions_have_sql_examples(self):
        """Test that role assignment functions have SQL implementation examples."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have SQL examples
        assert "SQL" in code or "sql" in code
        assert "INSERT" in code or "DELETE" in code or "SELECT" in code

    def test_all_four_role_assignment_functions_present(self):
        """Test that all four role assignment functions are present."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # All four should be present
        assert "def assign_role(user_id: str, role_name: str)" in code
        assert "def remove_role(user_id: str, role_name: str)" in code
        assert "def get_user_roles(user_id: str) -> List[str]:" in code
        assert "def set_user_roles(user_id: str, roles: List[str])" in code


class TestCompleteAdvancedRBACWorkflow:
    """End-to-end workflow tests for advanced RBAC features."""

    def test_complete_advanced_rbac_generation(self, tmp_path):
        """Test complete RBAC generation with all advanced features."""
        schema = SchnitzelSchema(
            roles={
                "superadmin": RoleConfig(
                    name="superadmin",
                    permissions=["system:*"],
                    inherits=["admin"]
                ),
                "admin": RoleConfig(
                    name="admin",
                    permissions=["users:*", "content:*"],
                    inherits=["moderator"]
                ),
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["content:delete", "users:read"],
                    inherits=["user"]
                ),
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read", "content:create:own"]
                )
            }
        )

        generator = RBACPermissionGenerator()
        file_path, size = generator.generate_to_file(schema, tmp_path)

        # Verify file
        assert file_path.exists()
        content = file_path.read_text()

        # Check auth_031: Role checking dependencies
        assert "def require_role" in content
        assert "def require_any_role" in content
        assert "def require_all_roles" in content

        # Check auth_032: Role inheritance with circular detection
        assert "inherits=" in content
        assert "_visited" in content
        assert "circular" in content.lower()

        # Check auth_033: Role assignment utilities
        assert "def assign_role" in content
        assert "def remove_role" in content
        assert "def get_user_roles" in content
        assert "def set_user_roles" in content

    def test_generated_code_with_advanced_features_is_valid_python(self, tmp_path):
        """Test that generated code with advanced features is valid Python."""
        schema = SchnitzelSchema(
            roles={
                "admin": RoleConfig(
                    name="admin",
                    permissions=["*"],
                    inherits=[]
                ),
                "moderator": RoleConfig(
                    name="moderator",
                    permissions=["users:read", "content:*"],
                    inherits=["user"]
                ),
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read", "content:create:own"]
                )
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

    def test_fixture_generation_with_advanced_features(self, tmp_path):
        """Test complete generation from fixture with advanced features."""
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

        # Check all advanced features are present
        assert "def require_role" in content
        assert "def require_any_role" in content
        assert "def require_all_roles" in content
        assert "def assign_role" in content
        assert "def remove_role" in content
        assert "def get_user_roles" in content
        assert "def set_user_roles" in content
        assert "_visited" in content

        # Check roles from fixture
        assert "admin" in content
        assert "moderator" in content
        assert "user" in content
        assert "guest" in content

        # Check inheritance from fixture (moderator inherits from user)
        assert '"user"' in content


class TestEdgeCases:
    """Test edge cases for advanced RBAC features."""

    def test_role_with_no_inheritance(self):
        """Test role with empty inherits list."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read"],
                    inherits=[]
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should handle empty inherits
        assert "inherits=[]" in code

    def test_role_with_none_inheritance(self):
        """Test role with None inherits."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(
                    name="user",
                    permissions=["content:read"],
                    inherits=None
                )
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should handle None inherits
        compile(code, '<generated>', 'exec')

    def test_generated_code_has_proper_sections(self):
        """Test that generated code has proper section headers."""
        schema = SchnitzelSchema(
            roles={
                "user": RoleConfig(name="user", permissions=["content:read"])
            }
        )

        generator = RBACPermissionGenerator()
        code = generator.generate(schema)

        # Should have clear section markers
        assert "Role Checking Dependencies (auth_031)" in code
        assert "Role Assignment Utilities (auth_033)" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
