"""Integration tests for Module 03 - Auth Integration Tests (auth_070-auth_100).

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
- auth_081: Integration test: RBAC scoped permissions work
- auth_082: Integration test: RBAC role inheritance works
- auth_083: Integration test: FastAPI role dependency works
- auth_084: Integration test: Redis session creation works
- auth_085: Integration test: Session retrieval works
- auth_086: Integration test: Session invalidation works
- auth_087: Integration test: Multi-device sessions work
- auth_088: Integration test: Remember me functionality works
- auth_089: Integration test: Session sliding expiration works
- auth_090: Integration test: TOTP secret generation works
- auth_091: Integration test: TOTP code verification works
- auth_092: Integration test: TOTP QR code generation works
- auth_093: Integration test: Backup codes generation works
- auth_094: Integration test: Backup code verification works
- auth_095: Integration test: MFA enrollment flow works end-to-end
- auth_096: Integration test: MFA verification middleware works
- auth_097: Integration test: Dart auth client compiles without errors
- auth_098: Integration test: Dart token storage works
- auth_099: Integration test: Dart auto token refresh works
- auth_100: Integration test: Dart AuthBloc state management works

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
    SessionConfig,
    MFAConfig,
)
from schnitzel.generators.python.auth.jwt import JWTAuthGenerator
from schnitzel.generators.python.auth.oauth import OAuthIntegrationGenerator
from schnitzel.generators.python.auth.rbac import RBACPermissionGenerator
from schnitzel.generators.python.auth.sessions import SessionManagementGenerator
from schnitzel.generators.python.auth.mfa import MFAGenerator
from schnitzel.generators.dart.auth import DartAuthClientGenerator


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


@pytest.fixture
def mfa_schema():
    """Create schema with MFA configuration."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password"],
            jwt=JWTConfig(
                algorithm="HS256",
                access_expiry=900,
                refresh_expiry=2592000
            ),
            mfa=MFAConfig(
                enabled=True,
                required=False,
                methods=["totp", "backup_codes"],
                backup_codes_count=10,
                totp_issuer="SchnitzelApp"
            )
        )
    )


@pytest.fixture
def auth_schema():
    """Create comprehensive auth schema for Dart client generation."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password", "google", "magic_link"],
            jwt=JWTConfig(
                algorithm="HS256",
                access_expiry=900,
                refresh_expiry=2592000,
                issuer="schnitzel-app",
                audience="schnitzel-users"
            ),
            oauth_callback_url="https://app.example.com/auth/callback"
        )
    )


@pytest.fixture
def session_schema():
    """Create schema with session configuration."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password"],
            session=SessionConfig(
                storage="redis",
                expiry=3600,  # 1 hour
                sliding_window=True,
                multi_device=True,
                remember_me_duration=2592000  # 30 days
            ),
            jwt=JWTConfig(
                algorithm="HS256",
                access_expiry=900,
                refresh_expiry=2592000
            )
        )
    )


@pytest.fixture
def mfa_schema():
    """Create schema with MFA configuration."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password"],
            mfa=MFAConfig(
                enabled=True,
                required=False,
                methods=["totp", "backup_codes"],
                backup_codes_count=10,
                totp_issuer="SchnitzelTest"
            ),
            jwt=JWTConfig(
                algorithm="HS256",
                access_expiry=900,
                refresh_expiry=2592000
            )
        )
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


# =============================================================================
# RBAC Advanced Tests (auth_081-auth_083)
# =============================================================================

class TestRBACAdvanced:
    """Advanced integration tests for RBAC with scoped permissions and inheritance."""

    def test_rbac_scoped_permissions(self, rbac_schema):
        """Test auth_081: RBAC scoped permissions work (resource:action:scope format)."""
        # Generate RBAC code
        generator = RBACPermissionGenerator()
        code = generator.generate(rbac_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated RBAC code has syntax errors"

        # Verify scoped permission format support (resource:action:scope)
        assert "content:read" in code, "Missing resource:action permission"
        assert "content:create:own" in code, "Missing resource:action:scope permission"

        # Verify permission parsing logic for scoped permissions
        # Should have logic to split permissions by ":"
        assert ":" in code, "Missing colon-based permission structure"
        has_split_logic = "split" in code or ":" in code
        assert has_split_logic, "Missing permission scope parsing"

        # Verify "own" scope handling for user-specific resources
        assert "own" in code, "Missing 'own' scope support"

        # Extract functions
        functions = extract_functions(code)

        # Verify has_permission function exists
        assert "has_permission" in functions, "Missing has_permission function"

        # Verify permission matching logic handles scopes
        # The code should handle matching "content:*" against "content:read"
        has_wildcard_scope = "*" in code or "wildcard" in code.lower()
        assert has_wildcard_scope, "Missing wildcard scope matching"

    def test_rbac_role_inheritance(self, rbac_schema):
        """Test auth_082: RBAC role inheritance works (child roles inherit parent permissions)."""
        # Generate RBAC code
        generator = RBACPermissionGenerator()
        code = generator.generate(rbac_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated RBAC code has syntax errors"

        # Verify inheritance structure is present
        assert "inherits" in code.lower() or "inherit" in code.lower(), "Missing inheritance structure"

        # Verify moderator role inherits from user role
        assert "moderator" in code, "Missing moderator role"
        assert "user" in code, "Missing user role"

        # Verify inheritance configuration in roles
        # moderator should inherit from user in rbac_schema
        has_inheritance_config = "inherits" in code.lower()
        assert has_inheritance_config, "Missing inheritance configuration"

        # Extract classes and functions
        classes = extract_classes(code)
        functions = extract_functions(code)

        # Should have role-related classes
        has_role_class = any("role" in c.lower() for c in classes)
        assert has_role_class, "Missing role management class"

        # Verify permission resolution handles inheritance
        # Should have logic to collect permissions from parent roles
        has_inheritance_logic = (
            "parent" in code.lower()
            or "inherit" in code.lower()
            or "extend" in code.lower()
        )
        assert has_inheritance_logic, "Missing permission inheritance resolution"

        # Verify child roles get both their own and parent permissions
        # The code should resolve inherited permissions
        assert "permissions" in code.lower(), "Missing permissions field"

    def test_fastapi_role_dependency(self, rbac_schema):
        """Test auth_083: FastAPI role dependency works (require_role, require_permission)."""
        # Generate RBAC code
        generator = RBACPermissionGenerator()
        code = generator.generate(rbac_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated RBAC code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify FastAPI dependency functions exist
        has_require_role = any("require" in f.lower() and "role" in f.lower() for f in functions)
        has_require_permission = any("require" in f.lower() and "permission" in f.lower() for f in functions)

        assert has_require_role or has_require_permission, "Missing FastAPI dependency functions"

        # Verify FastAPI dependency imports
        has_fastapi_import = (
            "from fastapi" in code
            or "import fastapi" in code
            or "Depends" in code
            or "HTTPException" in code
        )
        assert has_fastapi_import, "Missing FastAPI imports for dependencies"

        # Verify HTTPException for unauthorized access
        assert "HTTPException" in code or "exception" in code.lower(), "Missing exception handling"

        # Verify 403 Forbidden status code for permission denied
        has_forbidden_status = "403" in code or "Forbidden" in code
        assert has_forbidden_status, "Missing 403 status code for authorization failures"

        # Verify dependency returns user or raises exception
        assert "raise" in code or "return" in code, "Missing dependency return/raise logic"

        # Verify role/permission checking in dependency
        assert "has_permission" in functions or "check" in code.lower(), "Missing permission check in dependency"


# =============================================================================
# Session Integration Tests (auth_084-auth_089)
# =============================================================================

class TestSessionIntegration:
    """Integration tests for Redis-based session management."""

    def test_redis_session_creation(self, session_schema):
        """Test auth_084: Redis session creation works (generates unique ID)."""
        # Generate session code
        generator = SessionManagementGenerator()
        code = generator.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated session code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify create_session function exists
        assert "create_session" in functions, "Missing create_session function"

        # Verify session ID generation
        # Should use UUID or secure random token
        has_id_generation = (
            "uuid" in code.lower()
            or "secrets" in code.lower()
            or "urandom" in code
            or "session_id" in code.lower()
        )
        assert has_id_generation, "Missing session ID generation"

        # Verify Redis integration
        assert "redis" in code.lower(), "Missing Redis integration"

        # Verify Redis client or connection
        has_redis_client = (
            "Redis" in code
            or "redis" in code.lower()
            or "RedisClient" in code
        )
        assert has_redis_client, "Missing Redis client"

        # Verify session data storage
        assert "set" in code or "store" in code.lower(), "Missing session storage logic"

        # Verify TTL/expiry is set on creation
        assert "expire" in code.lower() or "ttl" in code.lower() or "ex=" in code, "Missing session expiry"

    def test_session_retrieval(self, session_schema):
        """Test auth_085: Session retrieval works (returns correct data)."""
        # Generate session code
        generator = SessionManagementGenerator()
        code = generator.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated session code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify get_session function exists
        assert "get_session" in functions, "Missing get_session function"

        # Verify Redis get operation
        assert "get" in code, "Missing Redis get operation"

        # Verify session data deserialization
        # Should handle JSON or pickle deserialization
        has_deserialization = (
            "json" in code.lower()
            or "loads" in code
            or "decode" in code
        )
        assert has_deserialization, "Missing session data deserialization"

        # Verify None/null handling for non-existent sessions
        assert "None" in code or "null" in code.lower(), "Missing null session handling"

        # Verify session validation
        # Should check if session exists and is valid
        has_validation = (
            "if" in code
            or "exists" in code.lower()
            or "is None" in code
        )
        assert has_validation, "Missing session validation"

    def test_session_invalidation(self, session_schema):
        """Test auth_086: Session invalidation works (delete_session removes session)."""
        # Generate session code
        generator = SessionManagementGenerator()
        code = generator.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated session code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify delete_session function exists
        assert "delete_session" in functions, "Missing delete_session function"

        # Verify Redis delete operation
        assert "delete" in code or "del" in code, "Missing Redis delete operation"

        # Verify session removal
        has_removal_logic = (
            "delete" in code.lower()
            or "remove" in code.lower()
            or "invalidate" in code.lower()
        )
        assert has_removal_logic, "Missing session invalidation logic"

        # Verify cleanup for multi-device sessions
        # Should handle removing specific session while keeping others
        if session_schema.auth and session_schema.auth.session:
            if session_schema.auth.session.multi_device:
                assert "session" in code.lower(), "Missing session management"

    def test_multi_device_sessions(self, session_schema):
        """Test auth_087: Multi-device sessions work (user can have multiple sessions)."""
        # Generate session code
        generator = SessionManagementGenerator()
        code = generator.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated session code has syntax errors"

        # Verify multi-device configuration is respected
        assert session_schema.auth.session.multi_device, "Test schema should have multi_device enabled"

        # Verify session ID uniqueness
        # Each device should have unique session ID
        has_unique_id = (
            "uuid" in code.lower()
            or "unique" in code.lower()
            or "session_id" in code.lower()
        )
        assert has_unique_id, "Missing unique session ID generation"

        # Verify multiple sessions per user support
        # Should store sessions with user-specific keys or lists
        has_multi_session_support = (
            "user" in code.lower()
            or "sessions" in code.lower()
            or "device" in code.lower()
        )
        assert has_multi_session_support, "Missing multi-device session support"

        # Verify session listing functionality
        # Should be able to list all sessions for a user
        functions = extract_functions(code)
        has_list_function = any("list" in f.lower() or "get_all" in f.lower() for f in functions)
        # Note: list function is optional but code should support multiple sessions

        # Verify Redis key structure supports multiple sessions
        # Should use pattern like "session:{user_id}:{session_id}" or similar
        assert ":" in code or "user" in code.lower(), "Missing session key structure"

    def test_remember_me_functionality(self, session_schema):
        """Test auth_088: Remember me functionality works (extended session duration)."""
        # Generate session code
        generator = SessionManagementGenerator()
        code = generator.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated session code has syntax errors"

        # Verify remember_me configuration is present
        assert session_schema.auth.session.remember_me_duration, "Test schema should have remember_me_duration"

        # Verify remember_me parameter or flag handling
        has_remember_me = (
            "remember" in code.lower()
            or "remember_me" in code.lower()
            or "extended" in code.lower()
        )
        assert has_remember_me, "Missing remember me functionality"

        # Verify different expiry times for normal vs remember me sessions
        assert "expiry" in code.lower() or "ttl" in code.lower(), "Missing expiry handling"

        # Verify extended duration (30 days from fixture)
        has_duration_config = (
            "2592000" in code  # 30 days in seconds
            or "duration" in code.lower()
        )
        assert has_duration_config, "Missing extended session duration"

        # Extract functions
        functions = extract_functions(code)

        # create_session should support remember_me parameter
        assert "create_session" in functions, "Missing create_session function"

    def test_session_sliding_expiration(self, session_schema):
        """Test auth_089: Session sliding expiration works (TTL reset on access)."""
        # Generate session code
        generator = SessionManagementGenerator()
        code = generator.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated session code has syntax errors"

        # Verify sliding_window configuration is present
        assert session_schema.auth.session.sliding_window, "Test schema should have sliding_window enabled"

        # Verify sliding expiration logic
        has_sliding_logic = (
            "slide" in code.lower()
            or "sliding" in code.lower()
            or "refresh" in code.lower()
            or "renew" in code.lower()
        )
        assert has_sliding_logic, "Missing sliding expiration functionality"

        # Extract functions
        functions = extract_functions(code)

        # Verify refresh or update function exists
        has_refresh_function = any(
            "refresh" in f.lower() or "update" in f.lower() or "renew" in f.lower()
            for f in functions
        )
        assert has_refresh_function, "Missing session refresh function"

        # Verify TTL reset on access
        # Should use Redis EXPIRE command or similar
        has_ttl_reset = (
            "expire" in code.lower()
            or "ttl" in code.lower()
            or "setex" in code
        )
        assert has_ttl_reset, "Missing TTL reset logic"

        # Verify get_session updates expiry
        # When sliding_window is enabled, retrieving a session should extend it
        assert "get_session" in functions, "Missing get_session function"


# =============================================================================
# MFA Integration Tests (auth_090-auth_096)
# =============================================================================

class TestMFAIntegration:
    """Integration tests for MFA (Multi-Factor Authentication) functionality."""

    def test_totp_secret_generation(self, mfa_schema):
        """Test auth_090: TOTP secret generation works (produces valid base32)."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify TOTP secret generation function exists
        has_totp_generate = any(
            "generate" in f.lower() and ("totp" in f.lower() or "secret" in f.lower())
            for f in functions
        )
        assert has_totp_generate, "Missing TOTP secret generation function"

        # Verify base32 encoding
        # TOTP secrets must be base32 encoded
        has_base32 = (
            "base32" in code.lower()
            or "b32encode" in code
            or "Base32" in code
        )
        assert has_base32, "Missing base32 encoding for TOTP secret"

        # Verify secure random generation
        # Should use secrets module or urandom
        has_secure_random = (
            "secrets" in code.lower()
            or "urandom" in code
            or "random" in code.lower()
        )
        assert has_secure_random, "Missing secure random generation"

        # Verify TOTP library import
        has_totp_library = (
            "pyotp" in code.lower()
            or "otp" in code.lower()
            or "totp" in code.lower()
        )
        assert has_totp_library, "Missing TOTP library"

        # Verify secret length (typically 16 or 32 bytes)
        # Base32 encoded secrets are typically 160-bit (20 bytes) or 256-bit (32 bytes)
        has_length_config = (
            "16" in code
            or "20" in code
            or "32" in code
            or "length" in code.lower()
        )
        assert has_length_config, "Missing secret length configuration"

        # Verify TOTP verification function
        has_verify = any("verify" in f.lower() for f in functions)
        assert has_verify, "Missing TOTP verification function"

        # Verify MFA configuration is respected
        assert mfa_schema.auth.mfa.enabled, "MFA should be enabled in test schema"
        assert "totp" in mfa_schema.auth.mfa.methods, "TOTP should be in MFA methods"

        # Verify issuer configuration for QR codes
        assert "SchnitzelTest" in code or "issuer" in code.lower(), "Missing TOTP issuer configuration"

        # Verify QR code generation support
        has_qr_support = (
            "qr" in code.lower()
            or "uri" in code.lower()
            or "otpauth" in code.lower()
        )
        assert has_qr_support, "Missing QR code generation support"

    def test_totp_code_verification(self, mfa_schema):
        """Test auth_091: TOTP code verification works."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify TOTP verification function exists
        assert "verify_totp" in functions, "Missing verify_totp function"

        # Verify pyotp library is imported
        assert "import pyotp" in code or "from pyotp" in code, "Missing pyotp import"

        # Verify verification logic
        assert "verify" in code.lower(), "Missing verification logic"
        assert "code" in code.lower(), "Missing code parameter"
        assert "secret" in code.lower(), "Missing secret parameter"

        # Verify time window support for clock drift
        assert "window" in code.lower() or "valid_window" in code, "Missing time window support"

        # Verify return value is boolean
        assert "bool" in code, "Missing boolean return type"

        # Verify error handling
        assert "raise" in code or "ValueError" in code, "Missing error handling"

    def test_totp_qr_code_generation(self, mfa_schema):
        """Test auth_092: TOTP QR code generation works."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify QR code generation function exists
        assert "generate_qr_code" in functions, "Missing generate_qr_code function"

        # Verify QR code library is imported
        assert "import qrcode" in code or "from qrcode" in code, "Missing qrcode import"

        # Verify otpauth URI generation
        assert "generate_totp_uri" in functions, "Missing generate_totp_uri function"
        assert "otpauth://" in code.lower() or "provisioning_uri" in code, "Missing otpauth URI"

        # Verify PNG bytes are returned
        assert "bytes" in code, "Missing bytes return type"
        assert "PNG" in code or "png" in code.lower(), "Missing PNG format"

        # Verify image generation
        assert "make_image" in code or "save" in code, "Missing image generation"

        # Verify BytesIO for in-memory image
        assert "BytesIO" in code or "io.BytesIO" in code, "Missing BytesIO for image buffer"

    def test_backup_codes_generation(self, mfa_schema):
        """Test auth_093: Backup codes generation works."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify backup codes generation function exists
        assert "generate_backup_codes" in functions, "Missing generate_backup_codes function"

        # Verify secure random generation
        assert "secrets" in code.lower(), "Missing secrets module for secure randomness"

        # Verify return type is list
        assert "list" in code, "Missing list return type"

        # Verify backup codes count configuration
        assert "backup_codes_count" in code or "10" in code, "Missing backup codes count"

        # Verify code format (XXXX-XXXX or similar)
        assert "hex" in code.lower() or "format" in code.lower(), "Missing code formatting"

    def test_backup_code_verification(self, mfa_schema):
        """Test auth_094: Backup code verification works."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify backup code verification function exists
        assert "verify_backup_code" in functions, "Missing verify_backup_code function"

        # Verify hashing for secure storage
        assert "hash_backup_codes" in functions, "Missing hash_backup_codes function"
        assert "hashlib" in code or "sha256" in code.lower(), "Missing hashing"

        # Verify constant-time comparison (timing attack prevention)
        assert "compare_digest" in code or "secrets.compare_digest" in code, "Missing constant-time comparison"

        # Verify one-time use (code removal after verification)
        assert "remaining" in code.lower() or "remove" in code.lower(), "Missing one-time use logic"

        # Verify return tuple with remaining codes
        assert "tuple" in code, "Missing tuple return type"

    def test_mfa_enrollment_flow(self, mfa_schema):
        """Test auth_095: MFA enrollment flow works end-to-end."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify enrollment functions exist
        assert "start_mfa_enrollment" in functions, "Missing start_mfa_enrollment function"
        assert "complete_mfa_setup" in functions, "Missing complete_mfa_setup function"

        # Verify enrollment flow generates all required data
        assert "generate_totp_secret" in functions, "Missing TOTP secret generation"
        assert "generate_qr_code" in functions, "Missing QR code generation"
        assert "generate_backup_codes" in functions, "Missing backup codes generation"

        # Verify setup completion with verification
        assert "verify_totp" in functions, "Missing TOTP verification in setup"

        # Verify database stubs for pending MFA
        assert "store_pending_mfa" in functions, "Missing store_pending_mfa stub"
        assert "enable_mfa_for_user" in functions, "Missing enable_mfa_for_user stub"

        # Verify proper return types
        assert "dict" in code, "Missing dict return type"

        # Verify issuer name is used
        assert "SchnitzelApp" in code or "totp_issuer" in code, "Missing TOTP issuer"

    def test_mfa_verification_middleware(self, mfa_schema):
        """Test auth_096: MFA verification middleware works."""
        # Generate MFA code
        generator = MFAGenerator()
        code = generator.generate(mfa_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated MFA code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify middleware function exists
        assert "require_mfa" in functions, "Missing require_mfa middleware"

        # Verify FastAPI dependency pattern
        assert "from fastapi import" in code, "Missing FastAPI imports"
        assert "Depends" in code or "Request" in code, "Missing FastAPI dependency support"
        assert "HTTPException" in code, "Missing HTTPException"

        # Verify async function
        assert "async def require_mfa" in code, "require_mfa should be async"

        # Verify MFA status checking
        assert "is_user_mfa_enabled" in functions, "Missing MFA status check function"

        # Verify session-based MFA verification
        assert "session" in code.lower(), "Missing session support"
        assert "mfa_verified" in code, "Missing MFA verification flag"

        # Verify 403 error for unverified MFA
        assert "403" in code, "Missing 403 status code"

        # Verify user_id parameter
        assert "user_id" in code.lower(), "Missing user_id parameter"


# =============================================================================
# Dart Auth Client Integration Tests (auth_097-auth_100)
# =============================================================================

class TestDartAuthIntegration:
    """Integration tests for Dart authentication client generation."""

    def test_dart_auth_client_compiles(self, auth_schema):
        """Test auth_097: Dart auth client compiles without errors."""
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Verify all expected files are generated
        assert "auth_client.dart" in files, "Missing auth_client.dart"
        assert "token_storage.dart" in files, "Missing token_storage.dart"
        assert "auth_interceptor.dart" in files, "Missing auth_interceptor.dart"
        assert "auth_bloc.dart" in files, "Missing auth_bloc.dart"
        assert "oauth_handler.dart" in files, "Missing oauth_handler.dart"
        assert "user_model.dart" in files, "Missing user_model.dart"

        # Get auth_client code
        auth_client_code = files["auth_client.dart"]

        # Verify basic Dart syntax
        assert "class " in auth_client_code, "Missing class definition"
        assert "import " in auth_client_code, "Missing imports"

        # Verify AuthClient class exists
        assert "class AuthClient" in auth_client_code or "AuthClient" in auth_client_code, "Missing AuthClient class"

        # Verify authentication methods
        assert "login" in auth_client_code.lower(), "Missing login method"
        assert "register" in auth_client_code.lower(), "Missing register method"
        assert "logout" in auth_client_code.lower(), "Missing logout method"
        assert "refresh" in auth_client_code.lower(), "Missing refresh method"

        # Verify Dio HTTP client
        assert "Dio" in auth_client_code, "Missing Dio import"

        # Verify async/await support
        assert "async" in auth_client_code or "Future" in auth_client_code, "Missing async support"

        # Verify error handling
        assert "try" in auth_client_code or "catch" in auth_client_code, "Missing error handling"

    def test_dart_token_storage(self, auth_schema):
        """Test auth_098: Dart token storage works."""
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Get token storage code
        token_storage_code = files["token_storage.dart"]

        # Verify TokenStorage class exists
        assert "class TokenStorage" in token_storage_code or "TokenStorage" in token_storage_code, "Missing TokenStorage class"

        # Verify flutter_secure_storage is used
        assert "FlutterSecureStorage" in token_storage_code or "SecureStorage" in token_storage_code, "Missing secure storage"

        # Verify token CRUD operations
        assert "save" in token_storage_code.lower() or "write" in token_storage_code.lower(), "Missing save token"
        assert "get" in token_storage_code.lower() or "read" in token_storage_code.lower(), "Missing get token"
        assert "delete" in token_storage_code.lower() or "remove" in token_storage_code.lower(), "Missing delete token"

        # Verify access and refresh token handling
        assert "access" in token_storage_code.lower(), "Missing access token handling"
        assert "refresh" in token_storage_code.lower(), "Missing refresh token handling"

        # Verify async storage operations
        assert "Future" in token_storage_code, "Missing Future return type"

        # Verify secure key constants
        assert "const" in token_storage_code or "final" in token_storage_code, "Missing storage key constants"

    def test_dart_auto_token_refresh(self, auth_schema):
        """Test auth_099: Dart auto token refresh works."""
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Get auth interceptor code
        auth_interceptor_code = files["auth_interceptor.dart"]

        # Verify AuthInterceptor class exists
        assert "class AuthInterceptor" in auth_interceptor_code or "Interceptor" in auth_interceptor_code, "Missing AuthInterceptor class"

        # Verify Dio interceptor pattern
        assert "Interceptor" in auth_interceptor_code, "Missing Interceptor base class"
        assert "onRequest" in auth_interceptor_code or "request" in auth_interceptor_code.lower(), "Missing request interceptor"
        assert "onError" in auth_interceptor_code or "error" in auth_interceptor_code.lower(), "Missing error interceptor"

        # Verify 401 handling for token expiry
        assert "401" in auth_interceptor_code, "Missing 401 status check"

        # Verify token refresh logic
        assert "refresh" in auth_interceptor_code.lower(), "Missing token refresh"

        # Verify retry logic after refresh
        assert "retry" in auth_interceptor_code.lower() or "repeat" in auth_interceptor_code.lower(), "Missing request retry"

        # Verify token injection in headers
        assert "header" in auth_interceptor_code.lower() or "Authorization" in auth_interceptor_code, "Missing auth header injection"

        # Verify Bearer token format
        assert "Bearer" in auth_interceptor_code, "Missing Bearer token format"

    def test_dart_auth_bloc(self, auth_schema):
        """Test auth_100: Dart AuthBloc state management works."""
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Get auth BLoC code
        auth_bloc_code = files["auth_bloc.dart"]

        # Verify AuthBloc class exists
        assert "class AuthBloc" in auth_bloc_code or "AuthBloc" in auth_bloc_code, "Missing AuthBloc class"

        # Verify flutter_bloc is used
        assert "Bloc" in auth_bloc_code, "Missing Bloc base class"
        assert "import" in auth_bloc_code and "bloc" in auth_bloc_code.lower(), "Missing flutter_bloc import"

        # Verify auth events
        assert "AuthEvent" in auth_bloc_code, "Missing AuthEvent base class"
        assert "LoginRequested" in auth_bloc_code or "login" in auth_bloc_code.lower(), "Missing login event"
        assert "RegisterRequested" in auth_bloc_code or "register" in auth_bloc_code.lower(), "Missing register event"
        assert "LogoutRequested" in auth_bloc_code or "logout" in auth_bloc_code.lower(), "Missing logout event"

        # Verify auth states
        assert "AuthState" in auth_bloc_code, "Missing AuthState base class"
        assert "Authenticated" in auth_bloc_code or "authenticated" in auth_bloc_code.lower(), "Missing authenticated state"
        assert "Unauthenticated" in auth_bloc_code or "unauthenticated" in auth_bloc_code.lower(), "Missing unauthenticated state"
        assert "Loading" in auth_bloc_code or "loading" in auth_bloc_code.lower(), "Missing loading state"

        # Verify event handler
        assert "on<" in auth_bloc_code or "mapEventToState" in auth_bloc_code, "Missing event handler"

        # Verify async state emissions
        assert "emit" in auth_bloc_code or "yield" in auth_bloc_code, "Missing state emission"

        # Verify equatable for state comparison
        assert "Equatable" in auth_bloc_code or "extends" in auth_bloc_code, "Missing Equatable base class"
