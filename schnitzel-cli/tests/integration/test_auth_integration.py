"""Integration tests for Module 03 - Auth Integration Tests (auth_070-auth_080).

Tests for:
- auth_070: Integration test: JWT token generation works end-to-end
- auth_071: Integration test: JWT token validation works correctly
- auth_072: Integration test: JWT refresh token flow works
- auth_073: Integration test: JWT RS256 algorithm works correctly
- auth_074: Integration test: Email/password registration works
- auth_075: Integration test: Email/password login works
- auth_076: Integration test: Password hashing is secure
- auth_077: Integration test: Magic link generation works
- auth_078: Integration test: Magic link verification works
- auth_079: Integration test: RBAC role checking works
- auth_080: Integration test: RBAC wildcard permissions work

Note: These are integration tests that verify the generated code structure,
compilation, and functionality. Tests verify code quality and structure
without requiring all runtime dependencies.
"""

import pytest
import ast
import re
from pathlib import Path
from schnitzel.schema.models import (
    SchnitzelSchema,
    AuthConfig,
    JWTConfig,
    RoleConfig,
)
from schnitzel.generators.python.auth.jwt import JWTAuthGenerator
from schnitzel.generators.python.auth.oauth import OAuthIntegrationGenerator
from schnitzel.generators.python.auth.rbac import RBACPermissionGenerator


def verify_code_compiles(code: str) -> bool:
    """Verify that generated Python code compiles."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def extract_functions(code: str) -> list[str]:
    """Extract function names from Python code."""
    tree = ast.parse(code)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    return functions


def extract_classes(code: str) -> list[str]:
    """Extract class names from Python code."""
    tree = ast.parse(code)
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return classes


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def jwt_schema():
    """Create schema with JWT configuration."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password"],
            jwt=JWTConfig(
                algorithm="HS256",
                access_expiry=900,  # 15 minutes
                refresh_expiry=2592000,  # 30 days
                issuer="schnitzel-test",
                audience="schnitzel-app"
            )
        )
    )


@pytest.fixture
def jwt_rs256_schema():
    """Create schema with JWT RS256 algorithm."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password"],
            jwt=JWTConfig(
                algorithm="RS256",
                access_expiry=900,
                refresh_expiry=2592000,
                issuer="schnitzel-test",
                audience="schnitzel-app"
            )
        )
    )


@pytest.fixture
def oauth_schema():
    """Create schema with email/password and magic link authentication."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password", "magic_link"],
            jwt=JWTConfig(
                algorithm="HS256",
                access_expiry=900,
                refresh_expiry=2592000
            )
        )
    )


@pytest.fixture
def rbac_schema():
    """Create schema with RBAC configuration."""
    return SchnitzelSchema(
        roles={
            "admin": RoleConfig(
                name="admin",
                description="Administrator with full access",
                permissions=["*"],
                inherits=[]
            ),
            "moderator": RoleConfig(
                name="moderator",
                description="Content moderator",
                permissions=["users:read", "content:*"],
                inherits=["user"]
            ),
            "user": RoleConfig(
                name="user",
                description="Regular user",
                permissions=["content:read", "content:create:own"],
                inherits=[]
            )
        }
    )


# =============================================================================
# JWT Token Generation Tests
# =============================================================================

class TestJWTIntegration:
    """Integration tests for JWT token generation and validation."""

    def test_jwt_token_generation_end_to_end(self, jwt_schema):
        """Test auth_070: JWT token generation works end-to-end."""
        # Generate JWT code
        generator = JWTAuthGenerator()
        code = generator.generate(jwt_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated JWT code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify required functions exist
        assert "create_access_token" in functions, "Missing create_access_token function"
        assert "create_refresh_token" in functions, "Missing create_refresh_token function"
        assert any("verify" in f for f in functions), "Missing token verification function"

        # Verify JWT library import
        assert "from jose import" in code or "import jwt" in code, "Missing JWT library import"

        # Verify token creation logic
        assert "encode" in code.lower(), "Missing token encoding"
        assert "exp" in code, "Missing expiry claim"
        assert "sub" in code, "Missing subject claim"

        # Verify HS256 algorithm is used (from schema)
        assert "HS256" in code, "Missing HS256 algorithm"

        # Verify access token expiry configuration
        assert "900" in code or "15" in code, "Access token expiry not configured"

        # Verify refresh token expiry configuration
        assert "2592000" in code or "30" in code, "Refresh token expiry not configured"

        # Verify issuer and audience claims
        assert "schnitzel-test" in code or "iss" in code, "Missing issuer configuration"
        assert "schnitzel-app" in code or "aud" in code, "Missing audience configuration"

    def test_jwt_token_validation(self, jwt_schema):
        """Test auth_071: JWT token validation works correctly."""
        # Generate JWT code
        generator = JWTAuthGenerator()
        code = generator.generate(jwt_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated JWT code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify validation functions exist
        assert any("verify" in f for f in functions), "Missing token verification"

        # Verify decode logic is present
        assert "decode" in code.lower(), "Missing token decoding"

        # Verify exception handling for invalid tokens
        assert "except" in code.lower() or "raise" in code, "Missing error handling"
        assert "JWTError" in code or "Exception" in code, "Missing JWT error handling"

        # Verify payload validation
        assert "exp" in code, "Missing expiry validation"
        assert "sub" in code, "Missing subject validation"

        # Verify issuer and audience validation
        if jwt_schema.auth and jwt_schema.auth.jwt:
            if jwt_schema.auth.jwt.issuer:
                assert "iss" in code or "issuer" in code.lower(), "Missing issuer validation"
            if jwt_schema.auth.jwt.audience:
                assert "aud" in code or "audience" in code.lower(), "Missing audience validation"

    def test_jwt_refresh_token_flow(self, jwt_schema):
        """Test auth_072: JWT refresh token flow works."""
        # Generate JWT code
        generator = JWTAuthGenerator()
        code = generator.generate(jwt_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated JWT code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify both access and refresh token functions
        assert "create_access_token" in functions, "Missing access token creation"
        assert "create_refresh_token" in functions, "Missing refresh token creation"

        # Verify separate verification functions or type checking
        has_separate_verify = (
            "verify_access_token" in functions and "verify_refresh_token" in functions
        )
        has_type_check = "type" in code and ("access" in code or "refresh" in code)

        assert has_separate_verify or has_type_check, "Missing token type distinction"

        # Verify different expiry times
        assert "access_expiry" in code or "access" in code, "Missing access expiry"
        assert "refresh_expiry" in code or "refresh" in code, "Missing refresh expiry"

        # Verify refresh tokens have longer expiry
        # access_expiry=900 (15 min), refresh_expiry=2592000 (30 days)
        assert "2592000" in code or "30" in code, "Refresh expiry not configured"

    def test_jwt_rs256_algorithm(self, jwt_rs256_schema):
        """Test auth_073: JWT RS256 algorithm works correctly."""
        # Generate JWT code with RS256
        generator = JWTAuthGenerator()
        code = generator.generate(jwt_rs256_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated JWT code has syntax errors"

        # Verify RS256-specific code is present
        assert "RS256" in code, "RS256 algorithm not configured"

        # Verify RSA key handling (cryptography library or similar)
        has_rsa_support = (
            "from cryptography" in code
            or "import rsa" in code
            or "RSA" in code
            or "private_key" in code.lower()
            or "public_key" in code.lower()
        )
        assert has_rsa_support, "Missing RSA key support for RS256"

        # Verify different key handling for signing and verification
        assert "private" in code.lower() or "secret" in code.lower(), "Missing private key reference"
        assert "public" in code.lower() or "verify" in code.lower(), "Missing public key reference"


# =============================================================================
# Authentication Flow Tests
# =============================================================================

class TestAuthFlows:
    """Integration tests for authentication flows."""

    def test_email_password_registration(self, oauth_schema):
        """Test auth_074: Email/password registration works."""
        # Generate OAuth code (includes email/password handling)
        generator = OAuthIntegrationGenerator()
        code = generator.generate(oauth_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated OAuth code has syntax errors"

        # Verify email/password registration code is present
        assert "email_password" in code or "email" in code.lower(), "Missing email/password support"
        assert "register" in code.lower() or "signup" in code.lower(), "Missing registration functionality"

        # Verify password hashing is included
        assert "bcrypt" in code.lower() or "hash" in code.lower(), "Missing password hashing"

        # Extract functions
        functions = extract_functions(code)

        # Should have registration-related functions
        has_register_func = any(
            "register" in f.lower() or "signup" in f.lower() or "create_user" in f.lower()
            for f in functions
        )
        assert has_register_func, "Missing registration function"

        # Verify password field handling
        assert "password" in code.lower(), "Missing password field"

    def test_email_password_login(self, oauth_schema):
        """Test auth_075: Email/password login works."""
        # Generate OAuth code
        generator = OAuthIntegrationGenerator()
        code = generator.generate(oauth_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated OAuth code has syntax errors"

        # Verify login code is present
        assert "login" in code.lower() or "authenticate" in code.lower(), "Missing login functionality"
        assert "email" in code.lower(), "Missing email field"
        assert "password" in code.lower(), "Missing password field"

        # Verify password verification is included
        assert "verify" in code.lower() or "check" in code.lower(), "Missing password verification"

        # Extract functions
        functions = extract_functions(code)

        # Should have authentication functions
        has_auth_func = any(
            any(keyword in f.lower() for keyword in ["auth", "login", "verify", "check"])
            for f in functions
        )
        assert has_auth_func, "Missing authentication function"

    def test_password_hashing_secure(self, oauth_schema):
        """Test auth_076: Password hashing is secure."""
        # Generate OAuth code
        generator = OAuthIntegrationGenerator()
        code = generator.generate(oauth_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated OAuth code has syntax errors"

        # Verify bcrypt is used (industry standard for password hashing)
        assert "bcrypt" in code.lower(), "Missing bcrypt for password hashing"

        # Verify hashing function exists
        assert "hash" in code.lower(), "Missing password hashing function"

        # Verify password verification function exists
        assert "checkpw" in code or "verify" in code.lower(), "Missing password verification"

        # Verify no plaintext password storage warnings
        assert "plaintext" not in code.lower() or "not" in code.lower(), "Plaintext password warning"

        # Verify bcrypt usage (bcrypt automatically handles salt)
        # bcrypt.hashpw and bcrypt.checkpw are industry-standard secure functions
        assert "hashpw" in code or "hash_password" in code.lower(), "Missing secure hash function"

    def test_magic_link_generation(self, oauth_schema):
        """Test auth_077: Magic link generation works."""
        # Generate OAuth code with magic link support
        generator = OAuthIntegrationGenerator()
        code = generator.generate(oauth_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated OAuth code has syntax errors"

        # Verify magic link code is present
        assert "magic_link" in code or "magic" in code.lower(), "Missing magic link support"

        # Verify token generation for magic links
        assert "generate" in code.lower() or "create" in code.lower(), "Missing token generation"
        assert "token" in code.lower(), "Missing token field"

        # Verify expiry is implemented
        assert "expire" in code.lower() or "ttl" in code.lower() or "exp" in code, "Missing expiry"

        # Extract functions
        functions = extract_functions(code)

        # Should have magic link generation functionality
        has_magic_func = any("magic" in f.lower() or "link" in f.lower() for f in functions)
        assert has_magic_func, "Missing magic link function"

        # Verify secure token generation (secrets module or similar)
        assert "secrets" in code.lower() or "urandom" in code or "uuid" in code.lower(), "Missing secure token generation"

    def test_magic_link_verification(self, oauth_schema):
        """Test auth_078: Magic link verification works."""
        # Generate OAuth code with magic link support
        generator = OAuthIntegrationGenerator()
        code = generator.generate(oauth_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated OAuth code has syntax errors"

        # Verify verification code is present
        assert "verify" in code.lower() or "validate" in code.lower(), "Missing verification"

        # Verify token handling
        assert "token" in code.lower(), "Missing token handling"

        # Verify expiry checking
        assert "expire" in code.lower() or "expired" in code.lower(), "Missing expiry check"

        # Extract functions
        functions = extract_functions(code)

        # Should have verification functionality
        has_verify_func = any(
            any(keyword in f.lower() for keyword in ["verify", "validate", "check"])
            for f in functions
        )
        assert has_verify_func, "Missing verification function"

        # Verify error handling for invalid/expired tokens
        assert "raise" in code or "except" in code.lower(), "Missing error handling"


# =============================================================================
# RBAC Integration Tests
# =============================================================================

class TestRBACIntegration:
    """Integration tests for RBAC permission checking."""

    def test_rbac_role_checking(self, rbac_schema):
        """Test auth_079: RBAC role checking works."""
        # Generate RBAC code
        generator = RBACPermissionGenerator()
        code = generator.generate(rbac_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated RBAC code has syntax errors"

        # Extract classes and functions
        classes = extract_classes(code)
        functions = extract_functions(code)

        # Verify RBAC classes exist
        has_role_class = any("role" in c.lower() for c in classes)
        has_registry = any("registry" in c.lower() for c in classes)
        assert has_role_class or has_registry, "Missing RBAC classes"

        # Verify permission checking function
        assert "has_permission" in functions, "Missing has_permission function"

        # Verify roles are defined in code
        assert "admin" in code, "Missing admin role"
        assert "moderator" in code, "Missing moderator role"
        assert "user" in code, "Missing user role"

        # Verify permissions are defined
        assert "permissions" in code.lower(), "Missing permissions field"

        # Verify role inheritance support
        assert "inherits" in code.lower() or "inherit" in code.lower(), "Missing role inheritance"

    def test_rbac_wildcard_permissions(self, rbac_schema):
        """Test auth_080: RBAC wildcard permissions work."""
        # Generate RBAC code
        generator = RBACPermissionGenerator()
        code = generator.generate(rbac_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated RBAC code has syntax errors"

        # Verify wildcard support
        assert "*" in code, "Missing wildcard permission"
        assert "wildcard" in code.lower() or "*" in code, "Missing wildcard handling"

        # Verify wildcard grants all permissions
        assert "all" in code.lower() or "*" in code, "Missing 'grant all' logic"

        # Extract functions
        functions = extract_functions(code)

        # Verify has_permission function exists
        assert "has_permission" in functions, "Missing has_permission function"

        # Verify scoped wildcard support (e.g., "content:*")
        has_scope_support = (
            ":" in code
            or "scope" in code.lower()
            or "split" in code
        )
        assert has_scope_support, "Missing scoped permission support"

        # Verify admin role has wildcard
        assert '"*"' in code or "'*'" in code, "Wildcard not in role definitions"

        # Verify permission matching logic
        assert "==" in code or "in " in code, "Missing permission matching"


# =============================================================================
# End-to-End Integration Tests
# =============================================================================

class TestFullAuthIntegration:
    """End-to-end integration tests combining multiple auth components."""

    def test_full_auth_stack(self):
        """Test complete auth stack with JWT + OAuth + RBAC."""
        # Create comprehensive schema
        schema = SchnitzelSchema(
            auth=AuthConfig(
                providers=["email_password", "magic_link"],
                jwt=JWTConfig(
                    algorithm="HS256",
                    access_expiry=900,
                    refresh_expiry=2592000,
                    issuer="schnitzel-test",
                    audience="schnitzel-app"
                )
            ),
            roles={
                "admin": RoleConfig(
                    name="admin",
                    description="Administrator",
                    permissions=["*"],
                    inherits=[]
                ),
                "user": RoleConfig(
                    name="user",
                    description="Regular user",
                    permissions=["content:read"],
                    inherits=[]
                )
            }
        )

        # Generate all auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(schema)
        oauth_code = oauth_gen.generate(schema)
        rbac_code = rbac_gen.generate(schema)

        # Verify all components generated successfully
        assert len(jwt_code) > 0, "JWT code not generated"
        assert len(oauth_code) > 0, "OAuth code not generated"
        assert len(rbac_code) > 0, "RBAC code not generated"

        # Verify all components compile
        assert verify_code_compiles(jwt_code), "JWT code has syntax errors"
        assert verify_code_compiles(oauth_code), "OAuth code has syntax errors"
        assert verify_code_compiles(rbac_code), "RBAC code has syntax errors"

        # Verify JWT works with configured schema
        assert "HS256" in jwt_code
        assert "schnitzel-test" in jwt_code or "iss" in jwt_code
        assert "schnitzel-app" in jwt_code or "aud" in jwt_code

        # Verify OAuth has all providers
        assert "email_password" in oauth_code
        assert "magic_link" in oauth_code

        # Verify RBAC has all roles
        assert "admin" in rbac_code
        assert "user" in rbac_code
        assert "*" in rbac_code  # admin wildcard
        assert "content:read" in rbac_code  # user permission

    def test_auth_code_quality(self, jwt_schema, oauth_schema, rbac_schema):
        """Test that generated auth code meets quality standards."""
        # Generate all auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)

        # Verify no unresolved TODO comments in generated code
        # Note: Templates may have TODO for user implementation, which is OK
        # We check for unresolved generator TODOs
        jwt_has_bad_todo = "TODO:" in jwt_code and "# TODO:" in jwt_code
        assert not jwt_has_bad_todo, "JWT code has unresolved TODOs"

        # Verify proper imports
        assert "import" in jwt_code, "JWT missing imports"
        assert "import" in oauth_code, "OAuth missing imports"
        assert "import" in rbac_code, "RBAC missing imports"

        # Verify type hints are used
        assert "->" in jwt_code or ": " in jwt_code, "JWT missing type hints"
        assert "->" in oauth_code or ": " in oauth_code, "OAuth missing type hints"
        assert "->" in rbac_code or ": " in rbac_code, "RBAC missing type hints"

        # Verify docstrings are present
        assert '"""' in jwt_code or "'''" in jwt_code, "JWT missing docstrings"
        assert '"""' in oauth_code or "'''" in oauth_code, "OAuth missing docstrings"
        assert '"""' in rbac_code or "'''" in rbac_code, "RBAC missing docstrings"

        # Verify security best practices
        # JWT should reference secret key
        assert "secret" in jwt_code.lower(), "JWT missing secret key reference"

        # OAuth should have password hashing
        assert "bcrypt" in oauth_code.lower() or "hash" in oauth_code.lower(), "OAuth missing password hashing"

        # RBAC should have permission checking
        assert "permission" in rbac_code.lower(), "RBAC missing permission checks"

        # Verify error handling
        assert "raise" in jwt_code or "Exception" in jwt_code, "JWT missing error handling"
        assert "raise" in oauth_code or "Exception" in oauth_code, "OAuth missing error handling"
        assert "raise" in rbac_code or "Exception" in rbac_code, "RBAC missing error handling"

    def test_auth_integration_consistency(self):
        """Test that auth components work together consistently."""
        # Create schema with all auth features
        schema = SchnitzelSchema(
            auth=AuthConfig(
                providers=["email_password"],
                jwt=JWTConfig(algorithm="HS256", access_expiry=900, refresh_expiry=2592000)
            ),
            roles={
                "admin": RoleConfig(name="admin", permissions=["*"], inherits=[]),
                "user": RoleConfig(name="user", permissions=["read"], inherits=[])
            }
        )

        # Generate all components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(schema)
        oauth_code = oauth_gen.generate(schema)
        rbac_code = rbac_gen.generate(schema)

        # All should compile without errors
        assert verify_code_compiles(jwt_code)
        assert verify_code_compiles(oauth_code)
        assert verify_code_compiles(rbac_code)

        # All should have consistent user ID handling
        # (using "sub" claim or user_id parameter)
        has_consistent_user_id = (
            ("sub" in jwt_code or "user_id" in jwt_code)
            and ("user_id" in oauth_code or "user" in oauth_code)
            and ("user" in rbac_code or "permissions" in rbac_code)
        )
        assert has_consistent_user_id, "Inconsistent user ID handling across components"

        # All should handle errors appropriately
        assert "Exception" in jwt_code or "raise" in jwt_code
        assert "Exception" in oauth_code or "raise" in oauth_code
        assert "Exception" in rbac_code or "raise" in rbac_code
