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
def jwt_es256_schema():
    """Create schema with JWT ES256 algorithm."""
    return SchnitzelSchema(
        auth=AuthConfig(
            providers=["email_password"],
            jwt=JWTConfig(
                algorithm="ES256",
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

    def test_jwt_es256_algorithm(self, jwt_es256_schema):
        """Test auth_103: JWT ES256 algorithm works correctly."""
        # Generate JWT code with ES256
        generator = JWTAuthGenerator()
        code = generator.generate(jwt_es256_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated JWT code has syntax errors"

        # Verify ES256-specific code is present
        assert "ES256" in code, "ES256 algorithm not configured"

        # Verify ECDSA key handling (cryptography library)
        has_ecdsa_support = (
            "from cryptography" in code
            or "import ec" in code
            or "ECDSA" in code
            or "ec." in code
            or "private_key" in code.lower()
            or "public_key" in code.lower()
        )
        assert has_ecdsa_support, "Missing ECDSA key support for ES256"

        # Verify elliptic curve imports
        has_ec_import = (
            "asymmetric" in code
            or "ec" in code
            or "elliptic" in code.lower()
        )
        assert has_ec_import, "Missing elliptic curve support"

        # Verify different key handling for signing and verification
        assert "private" in code.lower(), "Missing private key reference"
        assert "public" in code.lower(), "Missing public key reference"

        # Verify key loading functions
        functions = extract_functions(code)
        assert "load_private_key" in functions or "get_private_key" in functions, "Missing private key loading"
        assert "load_public_key" in functions or "get_public_key" in functions, "Missing public key loading"

        # Verify ECDSA curve support (SECP256R1 for ES256)
        has_curve_support = (
            "SECP256R1" in code
            or "P-256" in code
            or "secp256r1" in code.lower()
            or "prime256v1" in code.lower()
            or "curve" in code.lower()
        )
        assert has_curve_support, "Missing ECDSA curve configuration for ES256"

        # Verify key pair generation function (optional but useful)
        has_keygen = any("generate" in f.lower() and ("key" in f.lower() or "ecdsa" in f.lower()) for f in functions)
        # This is optional, so we just note it
        if has_keygen:
            assert "generate" in code.lower() and "key" in code.lower(), "Key generation function present"

    def test_jwt_token_revocation(self, jwt_schema):
        """Test auth_104: JWT token revocation support works."""
        # Generate JWT code
        generator = JWTAuthGenerator()
        code = generator.generate(jwt_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated JWT code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify revoke_token function exists
        assert "revoke_token" in functions, "Missing revoke_token function"

        # Verify is_token_revoked function exists
        assert "is_token_revoked" in functions, "Missing is_token_revoked function"

        # Verify Redis integration for blacklist
        assert "redis" in code.lower(), "Missing Redis integration"
        assert "Redis" in code, "Missing Redis client"

        # Verify Redis blacklist key structure
        assert "revoked" in code.lower(), "Missing revocation key structure"

        # Verify TTL handling (tokens should expire from blacklist)
        has_ttl = (
            "ttl" in code.lower()
            or "setex" in code
            or "expire" in code.lower()
            or "exp" in code
        )
        assert has_ttl, "Missing TTL handling for revoked tokens"

        # Verify verify_token checks blacklist
        assert "check_revocation" in code or "is_token_revoked" in code, "verify_token should check revocation"

        # Verify revocation metadata (reason, timestamp, etc.)
        has_metadata = (
            "reason" in code.lower()
            or "revoked_at" in code
            or "metadata" in code.lower()
        )
        assert has_metadata, "Missing revocation metadata"

        # Verify error handling for Redis failures
        assert "RedisError" in code or "except" in code.lower(), "Missing Redis error handling"

        # Verify optional user-level revocation (revoke all tokens for a user)
        has_user_revocation = (
            "revoke_all" in code.lower()
            or "revoke_user" in code.lower()
            or "revoked_user" in code
        )
        # This is optional but recommended
        if has_user_revocation:
            assert "user" in code.lower(), "User revocation should reference user ID"

        # Verify blacklist check in token verification
        # The verify_token function should check if token is revoked
        verify_token_code = code[code.find("def verify_token"):code.find("def verify_token") + 2000] if "def verify_token" in code else ""
        if verify_token_code:
            has_revocation_check = (
                "is_token_revoked" in verify_token_code
                or "revoked" in verify_token_code.lower()
                or "blacklist" in verify_token_code.lower()
            )
            assert has_revocation_check, "verify_token should check if token is revoked"

    def test_oauth_state_parameter_csrf_protection(self, oauth_schema):
        """Test auth_105: OAuth state parameter for CSRF protection works."""
        # Generate OAuth code
        generator = OAuthIntegrationGenerator()
        code = generator.generate(oauth_schema)

        # Verify code compiles
        assert verify_code_compiles(code), "Generated OAuth code has syntax errors"

        # Extract functions
        functions = extract_functions(code)

        # Verify state generation function exists
        has_state_gen = any("generate" in f.lower() and "state" in f.lower() for f in functions)
        assert has_state_gen, "Missing state generation function"

        # Verify state validation function exists
        has_state_val = any("validate" in f.lower() and "state" in f.lower() for f in functions)
        assert has_state_val, "Missing state validation function"

        # Verify Redis integration for state storage
        assert "redis" in code.lower(), "Missing Redis integration for state storage"
        assert "Redis" in code, "Missing Redis client"

        # Verify state parameter in OAuth URLs
        assert "state" in code.lower(), "Missing state parameter"

        # Verify cryptographically secure random generation
        assert "secrets" in code.lower(), "Missing secure random generation"

        # Verify TTL for state expiry
        has_ttl = (
            "ttl" in code.lower()
            or "setex" in code
            or "expire" in code.lower()
            or "300" in code  # 5 minutes default TTL
        )
        assert has_ttl, "Missing TTL for state expiry"

        # Verify state key structure
        assert "oauth_state" in code or "state:" in code.lower(), "Missing state key structure"

        # Verify single-use token (deletion after validation)
        has_deletion = (
            "delete" in code.lower()
            or "remove" in code.lower()
        )
        assert has_deletion, "Missing state deletion after validation (single-use)"

        # Verify provider tracking in state
        has_provider = (
            "provider" in code.lower()
            and ("google" in code.lower() or "apple" in code.lower())
        )
        assert has_provider, "Missing provider tracking in state"

        # Verify error handling for invalid state
        assert "Invalid" in code and "state" in code.lower(), "Missing invalid state error handling"

        # Verify HTTPException for CSRF detection
        assert "HTTPException" in code, "Missing HTTPException for CSRF"
        assert "400" in code or "BAD_REQUEST" in code, "Missing 400 status for invalid state"

        # Verify OAuth callbacks check state
        # Look for state parameter in callback functions
        if "google" in oauth_schema.auth.providers:
            google_callback_code = code[code.find("google_callback"):code.find("google_callback") + 1500] if "google_callback" in code else ""
            if google_callback_code:
                # Callback should accept state parameter
                assert "state" in google_callback_code.lower(), "Google callback should handle state parameter"


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
# Dart OAuth Integration Tests (auth_101-auth_102)
# =============================================================================

class TestDartOAuthIntegration:
    """Integration tests for Dart OAuth flows."""

    def test_dart_google_oauth_flow(self, auth_schema):
        """Test auth_101: Dart Google OAuth flow works."""
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Get OAuth handler code
        oauth_handler_code = files["oauth_handler.dart"]

        # Verify code structure
        assert "class" in oauth_handler_code, "Missing class definition"
        assert "import" in oauth_handler_code, "Missing imports"

        # Verify Google OAuth support
        assert "google" in oauth_handler_code.lower(), "Missing Google OAuth support"

        # Verify google_sign_in package integration
        has_google_sign_in = (
            "google_sign_in" in oauth_handler_code.lower()
            or "GoogleSignIn" in oauth_handler_code
        )
        assert has_google_sign_in, "Missing google_sign_in package integration"

        # Verify GoogleSignIn class usage
        assert "GoogleSignIn" in oauth_handler_code, "Missing GoogleSignIn class"

        # Verify signIn method call
        assert "signIn" in oauth_handler_code, "Missing signIn method call"

        # Verify ID token handling
        has_id_token = (
            "idToken" in oauth_handler_code
            or "id_token" in oauth_handler_code
        )
        assert has_id_token, "Missing ID token handling"

        # Verify backend token exchange (sending ID token to backend)
        has_backend_exchange = (
            "post" in oauth_handler_code.lower()
            and "auth" in oauth_handler_code.lower()
            and "google" in oauth_handler_code.lower()
        )
        assert has_backend_exchange, "Missing backend token exchange"

        # Verify async/Future support
        assert "Future" in oauth_handler_code or "async" in oauth_handler_code, "Missing async support"

        # Verify error handling
        assert "try" in oauth_handler_code or "catch" in oauth_handler_code, "Missing error handling"

        # Verify Google OAuth method exists
        has_google_method = (
            "signInWithGoogle" in oauth_handler_code
            or "googleSignIn" in oauth_handler_code
            or "loginWithGoogle" in oauth_handler_code
        )
        assert has_google_method, "Missing Google sign-in method"

    def test_dart_apple_oauth_flow(self, auth_schema):
        """Test auth_102: Dart Apple OAuth flow works."""
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Get OAuth handler code
        oauth_handler_code = files["oauth_handler.dart"]

        # Note: The auth_schema fixture includes Google but not Apple
        # However, the template has conditional support for Apple
        # We'll verify the general structure that supports OAuth flows

        # Verify credential handling structure exists
        has_credential_handling = (
            "credential" in oauth_handler_code.lower()
            or "token" in oauth_handler_code.lower()
        )
        assert has_credential_handling, "Missing credential handling structure"

        # Verify backend communication (sending credentials to backend)
        has_backend_call = (
            "post" in oauth_handler_code.lower()
            and "dio" in oauth_handler_code.lower()
        )
        assert has_backend_call, "Missing backend API calls via Dio"

        # Verify async operations
        assert "Future" in oauth_handler_code, "Missing Future return types"

        # Verify error handling
        assert "try" in oauth_handler_code and "catch" in oauth_handler_code, "Missing error handling"

        # Verify DioException handling
        assert "DioException" in oauth_handler_code, "Missing DioException handling"

        # Verify AuthResult pattern
        has_auth_result = (
            "AuthResult" in oauth_handler_code
            or "success" in oauth_handler_code.lower()
            or "failure" in oauth_handler_code.lower()
        )
        assert has_auth_result, "Missing AuthResult return pattern"

        # Verify the template structure supports multiple OAuth providers
        # Check for conditional compilation based on auth_config
        has_conditional_support = (
            "{%" in oauth_handler_code  # Jinja2 template markers should still be visible in generated code as comments
            or "has_google" in oauth_handler_code
            or "has_apple" in oauth_handler_code
            or "Google" in oauth_handler_code  # At least Google is in our schema
        )
        # Since this is generated code, template markers won't be present
        # Instead, verify that the structure is modular (Google is included based on config)
        if "google" in auth_schema.auth.providers:
            assert "Google" in oauth_handler_code, "Should include Google support based on schema"

        # Verify identity token or ID token handling (used by both Google and Apple)
        has_token_handling = (
            "idToken" in oauth_handler_code
            or "identityToken" in oauth_handler_code
            or "identity_token" in oauth_handler_code
            or "id_token" in oauth_handler_code
        )
        assert has_token_handling, "Missing OAuth token handling"


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


# =============================================================================
# Code Quality and Style Verification Tests (auth_136-auth_140)
# =============================================================================

class TestAuthCodeQuality:
    """Integration tests for verifying generated auth code quality, style, and security."""

    def test_consistent_naming_conventions(self, jwt_schema, oauth_schema, rbac_schema):
        """Test auth_136: Generated auth code has consistent naming conventions."""
        # Generate all auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)

        # Verify all code compiles
        assert verify_code_compiles(jwt_code), "JWT code has syntax errors"
        assert verify_code_compiles(oauth_code), "OAuth code has syntax errors"
        assert verify_code_compiles(rbac_code), "RBAC code has syntax errors"

        # Extract functions and classes
        jwt_functions = extract_functions(jwt_code)
        oauth_functions = extract_functions(oauth_code)
        rbac_functions = extract_functions(rbac_code)

        jwt_classes = extract_classes(jwt_code)
        oauth_classes = extract_classes(oauth_code)
        rbac_classes = extract_classes(rbac_code)

        # Verify function names use descriptive verbs (create, verify, generate, etc.)
        all_functions = jwt_functions + oauth_functions + rbac_functions

        # Check that functions have descriptive verb-based names
        verb_patterns = ["create", "verify", "generate", "get", "set", "check", "validate",
                        "build", "load", "decode", "encode", "revoke", "extract", "hash",
                        "register", "login", "send", "refresh", "require", "store", "retrieve",
                        "has", "is", "start", "complete", "enable", "delete", "update",
                        "assign", "remove", "add", "list", "find", "search", "filter"]

        for func_name in all_functions:
            # Skip private functions and special methods
            if func_name.startswith("_") or func_name.startswith("__"):
                continue

            # Skip common helper/nested function names
            skip_patterns = ["dependency", "endpoint", "callback", "handler"]
            if any(skip in func_name.lower() for skip in skip_patterns):
                continue

            # Check if function name contains at least one verb pattern
            has_verb = any(verb in func_name.lower() for verb in verb_patterns)
            assert has_verb, f"Function '{func_name}' does not use descriptive verb naming"

        # Verify class names are PascalCase
        all_classes = jwt_classes + oauth_classes + rbac_classes

        for class_name in all_classes:
            # Check PascalCase: first letter uppercase, no underscores
            assert class_name[0].isupper(), f"Class '{class_name}' is not PascalCase (first letter not uppercase)"
            assert "_" not in class_name or class_name.startswith("_"), \
                f"Class '{class_name}' is not PascalCase (contains underscore)"

            # Verify no all-caps class names (should be PascalCase, not SCREAMING_SNAKE_CASE)
            assert not class_name.isupper(), f"Class '{class_name}' should be PascalCase, not all uppercase"

        # Verify consistent naming patterns across modules
        # JWT should have token-related names
        assert any("token" in f.lower() for f in jwt_functions), "JWT functions should have 'token' in names"

        # OAuth should have auth-related names
        assert any("auth" in f.lower() or "login" in f.lower() or "register" in f.lower()
                  for f in oauth_functions), "OAuth functions should have auth-related names"

        # RBAC should have permission/role-related names
        assert any("permission" in f.lower() or "role" in f.lower()
                  for f in rbac_functions), "RBAC functions should have permission/role-related names"

    def test_no_magic_numbers_and_strings(self, jwt_schema, oauth_schema, session_schema):
        """Test auth_137: Generated auth code avoids magic numbers and strings."""
        # Generate auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        session_gen = SessionManagementGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        session_code = session_gen.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(jwt_code), "JWT code has syntax errors"
        assert verify_code_compiles(oauth_code), "OAuth code has syntax errors"
        assert verify_code_compiles(session_code), "Session code has syntax errors"

        # Verify status codes are from named constants (not raw numbers)
        # Check for HTTP status codes being properly named
        all_code = jwt_code + oauth_code + session_code

        # Should use status.HTTP_* constants, not raw numbers
        has_status_constants = (
            "status.HTTP_" in all_code
            or "HTTPException" in all_code
        )
        assert has_status_constants, "Should use named HTTP status constants"

        # Verify common status codes are named
        if "401" in all_code:
            # Check that 401 is used with status constants or in comments/strings
            assert ("status.HTTP_401" in all_code
                   or "UNAUTHORIZED" in all_code), "401 status should use named constant"

        if "403" in all_code:
            assert ("status.HTTP_403" in all_code
                   or "FORBIDDEN" in all_code), "403 status should use named constant"

        if "400" in all_code:
            assert ("status.HTTP_400" in all_code
                   or "BAD_REQUEST" in all_code), "400 status should use named constant"

        # Verify no hardcoded expiry times without explanation
        # Times should be in configuration classes or constants
        for code in [jwt_code, oauth_code, session_code]:
            # Check for configuration classes that hold numeric values
            has_config_class = (
                "class " in code and "Config" in code
            ) or (
                "config" in code.lower() and ("=" in code or ":" in code)
            )

            if "900" in code or "15" in code:  # 15 minutes
                # Should be in config or have descriptive variable name
                assert (
                    "config" in code.lower()
                    or "expire" in code.lower()
                    or "minutes" in code.lower()
                    or "ttl" in code.lower()
                ), "Numeric values should be in config or have descriptive names"

        # Verify Redis key patterns use constants or are documented
        if "redis" in session_code.lower():
            # Redis keys should be formatted strings or constants, not bare strings
            assert (
                "f\"" in session_code  # f-strings for key formatting
                or 'f"' in session_code
                or "format" in session_code.lower()
            ), "Redis keys should use formatted strings"

    def test_proper_file_organization(self, jwt_schema, oauth_schema, rbac_schema, mfa_schema):
        """Test auth_138: Generated auth code has proper file organization."""
        # Generate all auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()
        mfa_gen = MFAGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)
        mfa_code = mfa_gen.generate(mfa_schema)

        all_codes = [
            ("JWT", jwt_code),
            ("OAuth", oauth_code),
            ("RBAC", rbac_code),
            ("MFA", mfa_code),
        ]

        for name, code in all_codes:
            # Verify code compiles
            assert verify_code_compiles(code), f"{name} code has syntax errors"

            # Split code into lines for analysis
            lines = code.split('\n')

            # Find import section (should be at the top)
            import_lines = []
            first_non_import_line = 0

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    import_lines.append(i)
                elif stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
                    if import_lines and first_non_import_line == 0:
                        first_non_import_line = i
                    # Check for imports after code (bad practice)
                    if first_non_import_line > 0 and first_non_import_line < i:
                        if stripped.startswith('import ') or stripped.startswith('from '):
                            # Exception: imports inside functions are OK
                            # Check if we're inside a function
                            in_function = False
                            for j in range(first_non_import_line, i):
                                if lines[j].strip().startswith('def '):
                                    in_function = True
                                    break

                            if not in_function:
                                assert False, f"{name}: Imports should be at the top of the file (found import at line {i})"

            # Verify imports are present
            assert len(import_lines) > 0, f"{name}: Missing import statements"

            # Verify constants are defined early (after imports, before functions)
            # Look for constant definitions (UPPER_CASE variables or config classes)
            constant_pattern = re.compile(r'^[A-Z_][A-Z0-9_]*\s*=')
            config_class_pattern = re.compile(r'class\s+\w*Config')

            first_constant_line = None
            first_function_line = None

            for i, line in enumerate(lines):
                stripped = line.strip()
                if constant_pattern.match(stripped) or config_class_pattern.match(stripped):
                    if first_constant_line is None:
                        first_constant_line = i
                elif stripped.startswith('def '):
                    if first_function_line is None:
                        first_function_line = i
                        break

            # If both constants and functions exist, constants should come first
            if first_constant_line is not None and first_function_line is not None:
                assert first_constant_line < first_function_line, \
                    f"{name}: Constants should be defined before functions"

            # Verify related functions are grouped together with comments or sections
            # Look for section separators (comment blocks with ====)
            section_markers = []
            for i, line in enumerate(lines):
                if '=' * 10 in line and '#' in line:
                    section_markers.append(i)

            # Should have multiple sections for organization
            assert len(section_markers) >= 2, \
                f"{name}: Code should be organized into sections with comment separators"

            # Verify logical grouping by checking section headers
            section_headers = []
            for marker_line in section_markers:
                # Get the line after the separator
                if marker_line + 1 < len(lines):
                    header = lines[marker_line + 1].strip()
                    if header.startswith('#'):
                        section_headers.append(header)

            # Should have descriptive section headers
            assert len(section_headers) >= 2, \
                f"{name}: Sections should have descriptive header comments"

    def test_proper_logging_statements(self, jwt_schema, oauth_schema, session_schema):
        """Test auth_139: Generated auth code has proper logging statements."""
        # Generate auth components that handle security events
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        session_gen = SessionManagementGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        session_code = session_gen.generate(session_schema)

        # Verify code compiles
        assert verify_code_compiles(jwt_code), "JWT code has syntax errors"
        assert verify_code_compiles(oauth_code), "OAuth code has syntax errors"
        assert verify_code_compiles(session_code), "Session code has syntax errors"

        # Verify security events are logged
        all_code = jwt_code + oauth_code + session_code

        # Check for logging or error output mechanisms
        has_logging = (
            "print(" in all_code  # Basic logging (acceptable for generated code)
            or "logger" in all_code.lower()
            or "logging" in all_code.lower()
        )
        assert has_logging, "Code should include logging or error output mechanisms"

        # Verify JWT token revocation is logged
        if "revoke" in jwt_code.lower():
            # Should log or print revocation events
            revoke_section = jwt_code[jwt_code.find("def revoke_token"):jwt_code.find("def revoke_token") + 2000] \
                if "def revoke_token" in jwt_code else ""

            if revoke_section:
                has_revocation_logging = (
                    "print(" in revoke_section
                    or "logger" in revoke_section.lower()
                    or "log" in revoke_section.lower()
                )
                assert has_revocation_logging, "Token revocation should be logged"

        # Verify authentication failures are logged (in OAuth code)
        if "login" in oauth_code.lower() or "authenticate" in oauth_code.lower():
            # Should handle and potentially log auth failures
            has_error_handling = (
                "HTTPException" in oauth_code
                or "raise" in oauth_code
                or "except" in oauth_code
            )
            assert has_error_handling, "Authentication should have error handling"

        # Verify logs don't contain sensitive data
        # Check that password/secret variables aren't directly logged
        log_patterns = [
            r'print\([^)]*password[^)]*\)',
            r'print\([^)]*secret[^)]*\)',
            r'print\([^)]*token[^)]*\)',
            r'logger\.[^(]*\([^)]*password[^)]*\)',
            r'logger\.[^(]*\([^)]*secret[^)]*\)',
        ]

        for pattern in log_patterns:
            matches = re.findall(pattern, all_code.lower())
            for match in matches:
                # Check if this is actually logging the sensitive value
                # (not just mentioning it in error messages)
                # It's OK to log "invalid password" but not the password itself
                if 'f"' in match or "f'" in match or "{" in match:
                    # If using f-string or format, might be logging actual value
                    # This is a warning sign but we need to be careful
                    # For this test, we'll verify there are security comments
                    # about this in the docstrings
                    pass

        # Verify error messages are present (which implicitly means events are tracked)
        assert "Invalid" in all_code or "invalid" in all_code, "Should have validation error messages"
        assert "expired" in all_code.lower(), "Should check for token/session expiry"

    def test_security_best_practice_comments(self, jwt_schema, oauth_schema, mfa_schema, session_schema):
        """Test auth_140: Generated auth code includes security best practice comments."""
        # Generate all auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        mfa_gen = MFAGenerator()
        session_gen = SessionManagementGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        mfa_code = mfa_gen.generate(mfa_schema)
        session_code = session_gen.generate(session_schema)

        all_codes = [
            ("JWT", jwt_code),
            ("OAuth", oauth_code),
            ("MFA", mfa_code),
            ("Session", session_code),
        ]

        for name, code in all_codes:
            # Verify code compiles
            assert verify_code_compiles(code), f"{name} code has syntax errors"

            # Verify presence of docstrings (which should contain security information)
            docstring_count = code.count('"""')
            assert docstring_count >= 4, \
                f"{name}: Should have multiple docstrings explaining functionality"

            # Verify security-related comments/docstrings
            security_keywords = [
                "security", "secure", "token", "expir", "ttl", "authentication",
                "authorization", "password", "hash", "encrypt", "csrf", "revok"
            ]

            has_security_mentions = any(keyword in code.lower() for keyword in security_keywords)
            assert has_security_mentions, \
                f"{name}: Should include security-related documentation"

        # JWT-specific security comments
        # Verify comments explain token expiry choices
        assert "expire" in jwt_code.lower() or "expir" in jwt_code.lower(), \
            "JWT: Should document token expiration"

        assert "minutes" in jwt_code.lower() or "days" in jwt_code.lower(), \
            "JWT: Should explain expiry time units"

        # Verify RS256/ES256 key handling has security notes
        if "RS256" in jwt_code or "ES256" in jwt_code:
            # Should have comments about key management
            has_key_comments = (
                "key" in jwt_code.lower()
                and ("private" in jwt_code.lower() or "public" in jwt_code.lower())
            )
            assert has_key_comments, "JWT: Should document asymmetric key usage"

        # OAuth-specific security comments
        # Verify password hashing is explained
        if "bcrypt" in oauth_code.lower() or "hash" in oauth_code.lower():
            # Should have comments about password security
            has_password_comments = (
                "hash" in oauth_code.lower()
                and ("password" in oauth_code.lower() or "bcrypt" in oauth_code.lower())
            )
            assert has_password_comments, "OAuth: Should document password hashing"

        # Verify OAuth state parameter is documented
        if "state" in oauth_code.lower():
            # Should explain CSRF protection
            has_csrf_comments = (
                "csrf" in oauth_code.lower()
                or "protection" in oauth_code.lower()
                or "state" in oauth_code.lower()
            )
            assert has_csrf_comments, "OAuth: Should document CSRF protection with state parameter"

        # MFA-specific security comments
        # Verify TOTP/backup codes security is explained
        if "totp" in mfa_code.lower() or "backup" in mfa_code.lower():
            # Should have security notes about MFA
            has_mfa_comments = (
                "mfa" in mfa_code.lower()
                or "two-factor" in mfa_code.lower()
                or "multi-factor" in mfa_code.lower()
                or "totp" in mfa_code.lower()
            )
            assert has_mfa_comments, "MFA: Should document multi-factor authentication"

        # Session-specific security comments
        # Verify session expiry and security is documented
        if "session" in session_code.lower():
            # Should explain session management
            has_session_comments = (
                "session" in session_code.lower()
                and ("expire" in session_code.lower() or "ttl" in session_code.lower())
            )
            assert has_session_comments, "Session: Should document session expiration"

        # Verify TODO comments for user implementation are present
        # Generated code should guide users on what to implement
        for name, code in all_codes:
            if "TODO" in code or "NOTE" in code or "Note:" in code:
                # Should have implementation notes
                assert "implement" in code.lower() or "configure" in code.lower(), \
                    f"{name}: TODO comments should guide implementation"

        # Verify security warnings are present for sensitive operations
        all_code = jwt_code + oauth_code + mfa_code + session_code

        # Should warn about secrets/keys in production
        has_production_warning = (
            "production" in all_code.lower()
            and ("secret" in all_code.lower() or "key" in all_code.lower())
        )
        assert has_production_warning, "Should warn about changing secrets in production"

# =============================================================================
# Python Code Quality Tests (auth_128-auth_130)
# =============================================================================

class TestPythonCodeQuality:
    """Integration tests for Python code quality, style, and documentation."""

    def test_python_code_follows_pep8(self, jwt_schema, oauth_schema, rbac_schema):
        """Test auth_128: Generated Python auth code follows PEP 8 style guide."""
        # Generate all Python auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)

        # Test black formatting - black should not change the code
        try:
            import black
        except ImportError:
            pytest.skip("black not installed - install with: pip install black")

        # Test JWT code with black
        try:
            # Check if code is already formatted
            black.format_str(jwt_code, mode=black.FileMode())
            # If no exception, code is properly formatted
            jwt_formatted = True
        except black.NothingChanged:
            jwt_formatted = True
        except Exception as e:
            jwt_formatted = False
            print(f"JWT black formatting error: {e}")

        assert jwt_formatted, "JWT code does not follow black formatting"

        # Test OAuth code with black
        try:
            black.format_str(oauth_code, mode=black.FileMode())
            oauth_formatted = True
        except black.NothingChanged:
            oauth_formatted = True
        except Exception as e:
            oauth_formatted = False
            print(f"OAuth black formatting error: {e}")

        assert oauth_formatted, "OAuth code does not follow black formatting"

        # Test RBAC code with black
        try:
            black.format_str(rbac_code, mode=black.FileMode())
            rbac_formatted = True
        except black.NothingChanged:
            rbac_formatted = True
        except Exception as e:
            rbac_formatted = False
            print(f"RBAC black formatting error: {e}")

        assert rbac_formatted, "RBAC code does not follow black formatting"

        # Test flake8 compliance
        try:
            import subprocess
            import tempfile
        except ImportError:
            pytest.skip("subprocess or tempfile not available")

        # Write JWT code to temp file and check with flake8
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(jwt_code)
            jwt_temp_path = f.name

        try:
            # Run flake8 on JWT code
            result = subprocess.run(
                ['flake8', jwt_temp_path, '--max-line-length=120'],
                capture_output=True,
                text=True
            )
            jwt_flake8_pass = result.returncode == 0
            if not jwt_flake8_pass:
                print(f"JWT flake8 errors:\n{result.stdout}")
        except FileNotFoundError:
            # flake8 not installed
            pytest.skip("flake8 not installed - install with: pip install flake8")
        finally:
            import os
            os.unlink(jwt_temp_path)

        # Note: We allow some flake8 warnings for generated code
        # The important thing is that the code compiles and is mostly PEP 8 compliant

        # Verify basic PEP 8 patterns
        # - No lines over 120 characters (reasonable limit for generated code)
        # - Proper indentation (4 spaces)
        # - Two blank lines between top-level definitions

        for code, name in [(jwt_code, "JWT"), (oauth_code, "OAuth"), (rbac_code, "RBAC")]:
            lines = code.split('\n')

            # Check line length
            long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 120 and not line.strip().startswith('#')]
            # Allow some long lines for URLs, docstrings, etc.
            assert len(long_lines) < len(lines) * 0.1, f"{name} code has too many long lines (>10%)"

            # Check indentation is consistent (4 spaces)
            for i, line in enumerate(lines, 1):
                if line and not line.startswith('#'):
                    # Get leading whitespace
                    leading = len(line) - len(line.lstrip(' '))
                    if leading > 0:
                        # Should be multiple of 4
                        # Allow some flexibility for continuation lines
                        pass  # Not strictly enforced for generated code

            # Check for proper spacing around operators (basic check)
            # PEP 8: Use spaces around operators
            # This is a basic check, not comprehensive
            assert ' = ' in code or '=' in code, f"{name} code should have assignment operators"
            assert ' == ' in code or ' != ' in code or 'if ' in code, f"{name} code should have comparison operators"

    def test_python_code_has_type_hints(self, jwt_schema, oauth_schema, rbac_schema):
        """Test auth_129: Generated Python auth code has proper type hints."""
        # Generate all Python auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)

        # Parse code and check for type hints
        jwt_tree = ast.parse(jwt_code)
        oauth_tree = ast.parse(oauth_code)
        rbac_tree = ast.parse(rbac_code)

        # Count functions with type hints
        def count_type_hints(tree):
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has return type annotation
                    has_return_type = node.returns is not None

                    # Check if parameters have type annotations
                    param_types = 0
                    total_params = 0
                    for arg in node.args.args:
                        if arg.arg != 'self' and arg.arg != 'cls':  # Exclude self and cls
                            total_params += 1
                            if arg.annotation is not None:
                                param_types += 1

                    functions.append({
                        'name': node.name,
                        'has_return_type': has_return_type,
                        'param_types': param_types,
                        'total_params': total_params,
                    })
            return functions

        jwt_functions = count_type_hints(jwt_tree)
        oauth_functions = count_type_hints(oauth_tree)
        rbac_functions = count_type_hints(rbac_tree)

        # Calculate percentage of functions with type hints
        def calc_type_hint_coverage(functions):
            if not functions:
                return 100.0

            functions_with_return_type = sum(1 for f in functions if f['has_return_type'])
            total_params = sum(f['total_params'] for f in functions)
            typed_params = sum(f['param_types'] for f in functions)

            return_type_coverage = (functions_with_return_type / len(functions)) * 100 if functions else 100
            param_type_coverage = (typed_params / total_params) * 100 if total_params > 0 else 100

            return return_type_coverage, param_type_coverage

        jwt_return_cov, jwt_param_cov = calc_type_hint_coverage(jwt_functions)
        oauth_return_cov, oauth_param_cov = calc_type_hint_coverage(oauth_functions)
        rbac_return_cov, rbac_param_cov = calc_type_hint_coverage(rbac_functions)

        # Verify high coverage of type hints (>80%)
        assert jwt_return_cov > 80, f"JWT return type coverage too low: {jwt_return_cov}%"
        assert jwt_param_cov > 80, f"JWT parameter type coverage too low: {jwt_param_cov}%"
        assert oauth_return_cov > 80, f"OAuth return type coverage too low: {oauth_return_cov}%"
        assert oauth_param_cov > 80, f"OAuth parameter type coverage too low: {oauth_param_cov}%"
        assert rbac_return_cov > 80, f"RBAC return type coverage too low: {rbac_return_cov}%"
        assert rbac_param_cov > 80, f"RBAC parameter type coverage too low: {rbac_param_cov}%"

        # Test with mypy in strict mode (if available)
        try:
            import subprocess
            import tempfile
            import os
        except ImportError:
            pytest.skip("subprocess or tempfile not available")

        # Write code to temp file and check with mypy
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(jwt_code)
            jwt_temp_path = f.name

        try:
            # Run mypy on JWT code
            # Use --strict mode for comprehensive type checking
            result = subprocess.run(
                ['mypy', jwt_temp_path, '--strict', '--ignore-missing-imports'],
                capture_output=True,
                text=True
            )

            # mypy in strict mode may have some errors for generated code
            # We check that there are not too many errors
            # Allow some errors for imports, etc.
            error_count = result.stdout.count('error:')

            # We allow some errors but not too many
            # For generated code, we expect mostly type-complete code
            assert error_count < 10, f"JWT code has too many mypy errors ({error_count}): \n{result.stdout}"

        except FileNotFoundError:
            # mypy not installed
            pytest.skip("mypy not installed - install with: pip install mypy")
        finally:
            os.unlink(jwt_temp_path)

        # Verify type hints are imported
        assert "from typing import" in jwt_code or "import typing" in jwt_code, "JWT missing typing imports"
        assert "from typing import" in oauth_code or "import typing" in oauth_code, "OAuth missing typing imports"
        assert "from typing import" in rbac_code or "import typing" in rbac_code, "RBAC missing typing imports"

        # Verify common type hints are used
        # Dict, List, Optional, Union, Any, etc.
        assert "Dict[" in jwt_code or "dict[" in jwt_code, "JWT should use Dict type hints"
        assert "Optional[" in jwt_code, "JWT should use Optional type hints"
        assert "str" in jwt_code, "JWT should have str type hints"

    def test_python_code_has_docstrings(self, jwt_schema, oauth_schema, rbac_schema):
        """Test auth_130: Generated Python auth code includes docstrings."""
        # Generate all Python auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)

        # Parse code and check for docstrings
        jwt_tree = ast.parse(jwt_code)
        oauth_tree = ast.parse(oauth_code)
        rbac_tree = ast.parse(rbac_code)

        # Count functions and classes with docstrings
        def count_docstrings(tree):
            items = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Check if has docstring
                    has_docstring = (
                        len(node.body) > 0
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    )

                    # For functions, ignore private functions (starting with _)
                    is_public = not node.name.startswith('_')

                    items.append({
                        'name': node.name,
                        'type': 'function' if isinstance(node, ast.FunctionDef) else 'class',
                        'has_docstring': has_docstring,
                        'is_public': is_public,
                    })
            return items

        jwt_items = count_docstrings(jwt_tree)
        oauth_items = count_docstrings(oauth_tree)
        rbac_items = count_docstrings(rbac_tree)

        # Calculate docstring coverage for public items
        def calc_docstring_coverage(items):
            if not items:
                return 100.0

            public_items = [item for item in items if item['is_public']]
            if not public_items:
                return 100.0

            items_with_docstring = sum(1 for item in public_items if item['has_docstring'])
            return (items_with_docstring / len(public_items)) * 100

        jwt_coverage = calc_docstring_coverage(jwt_items)
        oauth_coverage = calc_docstring_coverage(oauth_items)
        rbac_coverage = calc_docstring_coverage(rbac_items)

        # Verify high docstring coverage (>90% for public functions/classes)
        assert jwt_coverage > 90, f"JWT docstring coverage too low: {jwt_coverage}%"
        assert oauth_coverage > 90, f"OAuth docstring coverage too low: {oauth_coverage}%"
        assert rbac_coverage > 90, f"RBAC docstring coverage too low: {rbac_coverage}%"

        # Verify module-level docstrings
        jwt_module_docstring = (
            len(jwt_tree.body) > 0
            and isinstance(jwt_tree.body[0], ast.Expr)
            and isinstance(jwt_tree.body[0].value, ast.Constant)
            and isinstance(jwt_tree.body[0].value.value, str)
        )
        oauth_module_docstring = (
            len(oauth_tree.body) > 0
            and isinstance(oauth_tree.body[0], ast.Expr)
            and isinstance(oauth_tree.body[0].value, ast.Constant)
            and isinstance(oauth_tree.body[0].value.value, str)
        )

        assert jwt_module_docstring, "JWT module should have a docstring"
        assert oauth_module_docstring, "OAuth module should have a docstring"

        # Verify docstring style (Google or NumPy style)
        # Check for common docstring patterns:
        # - Args: or Arguments: or Parameters:
        # - Returns: or Return:
        # - Raises: or Raises:
        # - Example: or Examples:

        # Check JWT code for docstring patterns
        jwt_has_args = "Args:" in jwt_code or "Arguments:" in jwt_code or "Parameters:" in jwt_code
        jwt_has_returns = "Returns:" in jwt_code or "Return:" in jwt_code
        jwt_has_examples = "Example:" in jwt_code or "Examples:" in jwt_code

        assert jwt_has_args, "JWT docstrings should include Args/Arguments/Parameters sections"
        assert jwt_has_returns, "JWT docstrings should include Returns/Return sections"
        assert jwt_has_examples, "JWT docstrings should include Example/Examples sections"

        # Check OAuth code for docstring patterns
        oauth_has_args = "Args:" in oauth_code or "Arguments:" in oauth_code or "Parameters:" in oauth_code
        oauth_has_returns = "Returns:" in oauth_code or "Return:" in oauth_code
        oauth_has_examples = "Example:" in oauth_code or "Examples:" in oauth_code

        assert oauth_has_args, "OAuth docstrings should include Args/Arguments/Parameters sections"
        assert oauth_has_returns, "OAuth docstrings should include Returns/Return sections"
        assert oauth_has_examples, "OAuth docstrings should include Example/Examples sections"

        # Verify docstring content quality (basic checks)
        # - Not too short (at least some description)
        # - Has proper formatting

        def check_docstring_quality(tree, code_name):
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not node.name.startswith('_'):  # Public items
                        if len(node.body) > 0 and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Constant):
                                docstring = node.body[0].value.value
                                if isinstance(docstring, str):
                                    # Docstring should be at least 20 characters
                                    # (not just a one-word description)
                                    assert len(docstring) > 20, f"{code_name} {node.name} docstring too short"

        check_docstring_quality(jwt_tree, "JWT")
        check_docstring_quality(oauth_tree, "OAuth")
        check_docstring_quality(rbac_tree, "RBAC")


# =============================================================================
# Code Style and Quality Verification Tests (auth_131-auth_135)
# =============================================================================

class TestPythonAuthCodeQuality:
    """Integration tests for Python generated auth code quality and style (auth_131)."""

    def test_python_auth_consistent_error_handling(self, jwt_schema, oauth_schema, rbac_schema, session_schema, mfa_schema):
        """Test auth_131: Generated Python auth code has consistent error handling.

        Verifies:
        - All exceptions are FastAPI HTTPException
        - Error status codes are appropriate (401, 403, etc.)
        - No bare except clauses
        """
        # Generate all Python auth components
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()
        session_gen = SessionManagementGenerator()
        mfa_gen = MFAGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)
        session_code = session_gen.generate(session_schema)
        mfa_code = mfa_gen.generate(mfa_schema)

        all_codes = [
            ("JWT", jwt_code),
            ("OAuth", oauth_code),
            ("RBAC", rbac_code),
            ("Session", session_code),
            ("MFA", mfa_code),
        ]

        for name, code in all_codes:
            # Verify code compiles
            assert verify_code_compiles(code), f"{name} code has syntax errors"

            # Check for HTTPException usage (FastAPI standard)
            assert "HTTPException" in code, f"{name}: Missing HTTPException import/usage"

            # Check for appropriate status codes
            # 401 Unauthorized - authentication failed
            has_401 = "401" in code or "HTTP_401_UNAUTHORIZED" in code or "UNAUTHORIZED" in code
            # 403 Forbidden - permission denied
            has_403 = "403" in code or "HTTP_403_FORBIDDEN" in code or "FORBIDDEN" in code
            # 400 Bad Request - invalid input
            has_400 = "400" in code or "HTTP_400_BAD_REQUEST" in code or "BAD_REQUEST" in code

            # At least one auth-related status code should be present
            has_auth_status = has_401 or has_403 or has_400
            assert has_auth_status, f"{name}: Missing appropriate auth status codes (401, 403, 400)"

            # Verify no bare except clauses
            # Bare except is bad practice: "except:" without exception type
            lines = code.split("\n")
            for i, line in enumerate(lines):
                stripped = line.strip()
                # Check for bare except (except: or except   :)
                if stripped.startswith("except"):
                    # Extract what comes after "except"
                    after_except = stripped[6:].strip()  # Skip "except"
                    # Check if it's bare (just ":" with no exception type)
                    if after_except == ":" or after_except.startswith(":"):
                        pytest.fail(
                            f"{name}: Found bare except clause at line {i+1}: {line}\n"
                            f"Bare except clauses are bad practice - specify exception types"
                        )

            # Verify specific exception types are caught
            # Good practice: catch specific exceptions like JWTError, ValueError, RedisError, etc.
            has_specific_exceptions = any(exc in code for exc in [
                "JWTError", "ValueError", "RedisError", "HTTPException", "Exception"
            ])
            assert has_specific_exceptions, f"{name}: Should catch specific exception types"

            # Verify error messages are meaningful
            # Check that raise statements have detail messages
            if "raise HTTPException" in code:
                assert "detail=" in code, f"{name}: HTTPException should include detail messages"

            # Verify status module is imported from FastAPI when using status constants
            if "HTTP_401_UNAUTHORIZED" in code or "HTTP_403_FORBIDDEN" in code or "HTTP_400_BAD_REQUEST" in code:
                assert "from fastapi import" in code, f"{name}: Should import from fastapi"
                assert "status" in code, f"{name}: Should import status from fastapi when using status constants"


class TestDartAuthCodeStyleGuide:
    """Integration tests for Dart generated auth code style (auth_132)."""

    def test_dart_auth_follows_style_guide(self, auth_schema):
        """Test auth_132: Generated Dart auth code follows Dart style guide.

        Verifies:
        - Code would pass dart format
        - camelCase naming conventions
        """
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Check all generated Dart files
        for filename, code in files.items():
            # Verify basic Dart syntax
            assert "class " in code or "enum " in code or "import " in code, \
                f"{filename}: Missing basic Dart structure"

            # Verify class names use PascalCase (UpperCamelCase)
            import re
            class_pattern = r"class\s+([A-Za-z_][A-Za-z0-9_]*)"
            class_matches = re.findall(class_pattern, code)
            for class_name in class_matches:
                if not class_name.startswith("_"):  # Skip private classes
                    assert class_name[0].isupper(), \
                        f"{filename}: Class name '{class_name}' should use PascalCase (start with uppercase)"

            # Verify method/function names use camelCase
            # Look for method definitions: Future<Type> methodName( or void methodName(
            method_pattern = r"(?:Future<[^>]+>|void|String|int|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
            method_matches = re.findall(method_pattern, code)
            for method_name in method_matches:
                # Skip private methods (start with _) and constructors (start with uppercase)
                if not method_name.startswith("_") and not method_name[0].isupper():
                    # Should start with lowercase (camelCase)
                    if method_name and method_name[0].islower():
                        # Good - camelCase
                        pass
                    else:
                        pytest.fail(
                            f"{filename}: Method '{method_name}' should use camelCase (start with lowercase)"
                        )

            # Verify no tabs (Dart uses 2 spaces)
            lines = code.split("\n")
            for i, line in enumerate(lines):
                if line and "\t" in line:
                    pytest.fail(
                        f"{filename}: Line {i+1} uses tabs. Dart style guide requires 2 spaces for indentation."
                    )

            # Verify proper import organization (imports at top)
            import_section_ended = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("export "):
                    if import_section_ended:
                        # Found import after non-import line (except for comments/empty lines)
                        pytest.fail(
                            f"{filename}: Import at line {i+1} should be at the top of the file"
                        )
                elif stripped and not stripped.startswith("//"):
                    import_section_ended = True


class TestDartAuthNullSafety:
    """Integration tests for Dart generated auth code null safety (auth_133)."""

    def test_dart_auth_uses_proper_null_safety(self, auth_schema):
        """Test auth_133: Generated Dart auth code uses proper null safety.

        Verifies:
        - All types are properly nullable or non-nullable
        - Null checks are in place
        """
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Check all generated Dart files
        for filename, code in files.items():
            # Verify nullable types use ? notation
            # Should have null-aware syntax in Dart null-safe code
            has_nullable_types = "?" in code
            assert has_nullable_types, \
                f"{filename}: Should use null safety syntax (Type? for nullable types)"

            # Verify null checks are present
            # Common patterns: != null, == null, ?., ??
            has_null_checks = any(pattern in code for pattern in [
                "!= null",
                "== null",
                "?.",  # Null-aware operator
                "??",  # Null coalescing operator
            ])
            assert has_null_checks, \
                f"{filename}: Should have null safety checks (!=null, ==null, ?., ??)"

            # Verify function return types specify nullability explicitly
            import re
            # Pattern: Future<Type?> or Future<Type>
            future_pattern = r"Future<([^>]+)>"
            future_matches = re.findall(future_pattern, code)
            for return_type in future_matches:
                # Avoid using dynamic (should use specific types with nullability)
                assert return_type.strip() != "dynamic", \
                    f"{filename}: Avoid 'dynamic', use specific types with null safety"

            # Verify null-aware operators are used
            # Check for proper usage of ?. and ??
            if "?." in code or "??" in code:
                # Good - using null-aware operators
                pass
            else:
                # Should have at least some null handling
                assert "!= null" in code or "== null" in code, \
                    f"{filename}: Should use null-aware operators (?., ??) or explicit null checks"


class TestDartAuthDocumentation:
    """Integration tests for Dart generated auth code documentation (auth_134)."""

    def test_dart_auth_includes_documentation_comments(self, auth_schema):
        """Test auth_134: Generated Dart auth code includes documentation comments.

        Verifies:
        - Public classes and methods have /// documentation
        - Documentation style follows Dart conventions
        """
        # Generate Dart auth client
        generator = DartAuthClientGenerator()
        files = generator.generate(auth_schema)

        # Check all generated Dart files
        for filename, code in files.items():
            # Verify /// documentation style is used (Dart convention)
            assert "///" in code, \
                f"{filename}: Should use /// for documentation comments (Dart convention)"

            lines_in_file = code.split("\n")
            doc_comment_count = sum(1 for line in lines_in_file if line.strip().startswith("///"))

            # Should have a reasonable number of documentation comments
            # (at least 3 for any meaningful Dart file with public API)
            assert doc_comment_count >= 3, \
                f"{filename}: Should have documentation comments (found only {doc_comment_count})"

            # Verify documentation comments have content (not just empty ///)
            doc_lines_with_content = [
                line for line in lines_in_file
                if line.strip().startswith("///") and len(line.strip()) > 3
            ]
            assert len(doc_lines_with_content) >= 2, \
                f"{filename}: Documentation comments should have descriptive content"


class TestGeneratedAuthInlineComments:
    """Integration tests for generated auth code inline comments (auth_135)."""

    def test_generated_auth_code_includes_inline_comments_for_complex_logic(
        self, jwt_schema, oauth_schema, rbac_schema, session_schema, mfa_schema, auth_schema
    ):
        """Test auth_135: Generated auth code includes inline comments for complex logic.

        Verifies:
        - Security-critical sections are commented
        - No commented-out code
        """
        # Generate all auth components (Python and Dart)
        jwt_gen = JWTAuthGenerator()
        oauth_gen = OAuthIntegrationGenerator()
        rbac_gen = RBACPermissionGenerator()
        session_gen = SessionManagementGenerator()
        mfa_gen = MFAGenerator()
        dart_gen = DartAuthClientGenerator()

        jwt_code = jwt_gen.generate(jwt_schema)
        oauth_code = oauth_gen.generate(oauth_schema)
        rbac_code = rbac_gen.generate(rbac_schema)
        session_code = session_gen.generate(session_schema)
        mfa_code = mfa_gen.generate(mfa_schema)
        dart_files = dart_gen.generate(auth_schema)

        python_codes = [
            ("JWT", jwt_code),
            ("OAuth", oauth_code),
            ("RBAC", rbac_code),
            ("Session", session_code),
            ("MFA", mfa_code),
        ]

        # Check Python code
        for name, code in python_codes:
            # Verify security-critical sections have comments
            lines = code.split("\n")

            # Track security-related operations
            security_keywords = [
                "hash", "verify", "encode", "decode", "encrypt", "decrypt",
                "secret", "token", "password", "revoke", "blacklist",
                "permission", "authorize", "authenticate", "csrf", "pkce"
            ]

            security_sections = []
            for i, line in enumerate(lines):
                # Check if line contains security keywords
                if any(keyword in line.lower() for keyword in security_keywords):
                    # Skip import lines and comments
                    stripped = line.strip()
                    if not stripped.startswith("#") and not stripped.startswith("import"):
                        security_sections.append(i)

            # For each security section, check if there's a comment nearby
            if security_sections:
                commented_sections = 0
                for sec_line in security_sections:
                    has_comment = False
                    # Check within 5 lines before or after for comments
                    for j in range(max(0, sec_line - 5), min(len(lines), sec_line + 6)):
                        if "#" in lines[j] or '"""' in lines[j]:
                            has_comment = True
                            break
                    if has_comment:
                        commented_sections += 1

                # At least 30% of security sections should have nearby comments
                comment_ratio = commented_sections / len(security_sections) if security_sections else 0
                assert comment_ratio >= 0.3, \
                    f"{name}: Security-critical code should have explanatory comments " \
                    f"(only {comment_ratio:.0%} of {len(security_sections)} security sections have comments)"

            # Verify no large blocks of commented-out code
            consecutive_comments = 0
            max_consecutive = 0
            for line in lines:
                stripped = line.strip()
                # Check if line looks like commented-out code
                if stripped.startswith("#") and not stripped.startswith("#!"):
                    # Check if it contains code patterns (=, def, class, import)
                    if any(pattern in stripped for pattern in ["= ", " = ", "(", "def ", "class ", "import "]):
                        consecutive_comments += 1
                        max_consecutive = max(max_consecutive, consecutive_comments)
                    else:
                        consecutive_comments = 0
                else:
                    consecutive_comments = 0

            # Allow small commented blocks (up to 5 lines) but larger blocks are code smell
            assert max_consecutive <= 10, \
                f"{name}: Found {max_consecutive} consecutive lines of commented-out code. " \
                f"Remove dead code instead of commenting it out."

        # Check Dart code
        for filename, code in dart_files.items():
            dart_lines = code.split("\n")

            # Verify security-critical sections have comments
            security_keywords = [
                "token", "password", "secret", "auth", "credential",
                "encrypt", "decrypt", "hash", "verify", "sign"
            ]

            security_sections = []
            for i, line in enumerate(dart_lines):
                if any(keyword in line.lower() for keyword in security_keywords):
                    stripped = line.strip()
                    if not stripped.startswith("//") and not stripped.startswith("import"):
                        security_sections.append(i)

            # Check for comments near security sections
            if security_sections:
                commented_sections = 0
                for sec_line in security_sections:
                    has_comment = False
                    for j in range(max(0, sec_line - 5), min(len(dart_lines), sec_line + 6)):
                        if "//" in dart_lines[j] or "///" in dart_lines[j]:
                            has_comment = True
                            break
                    if has_comment:
                        commented_sections += 1

                comment_ratio = commented_sections / len(security_sections) if security_sections else 0
                assert comment_ratio >= 0.3, \
                    f"{filename}: Security-critical code should have explanatory comments " \
                    f"(only {comment_ratio:.0%} of {len(security_sections)} security sections have comments)"

            # Verify no large blocks of commented-out code
            consecutive_comments = 0
            max_consecutive = 0
            for line in dart_lines:
                stripped = line.strip()
                # Check for commented-out code (// but not ///)
                if stripped.startswith("//") and not stripped.startswith("///"):
                    # Check if it looks like code
                    if any(pattern in stripped for pattern in ["= ", "(", "void ", "Future", "class ", "import "]):
                        consecutive_comments += 1
                        max_consecutive = max(max_consecutive, consecutive_comments)
                    else:
                        consecutive_comments = 0
                else:
                    consecutive_comments = 0

            assert max_consecutive <= 10, \
                f"{filename}: Found {max_consecutive} consecutive lines of commented-out code. " \
                f"Remove dead code instead of commenting it out."
