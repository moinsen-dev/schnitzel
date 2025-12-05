"""Python authentication generators.

These generators create authentication utilities from Schnitzel schemas.
They are automatically invoked by the CLI generate command when auth configuration
is present in the schema.

CLI Usage:
    # Generate all auth files based on schema configuration
    schnitzel generate --target auth

    # Generate all project files including auth
    schnitzel generate --target all

    # Generate only Python backend including auth
    schnitzel generate --target python

Auth Components:
    - JWT: Token generation and verification (requires auth.jwt in schema)
    - OAuth: OAuth2 provider integration (requires auth.providers in schema)
    - RBAC: Role-based access control (requires roles in schema)
    - Sessions: Redis-based session management (requires auth.session in schema)
    - MFA: Multi-factor authentication (requires auth.mfa.enabled in schema)

Generated Files:
    All auth files are generated to: backend/app/generated/auth/
    - jwt.py: JWT token utilities
    - oauth.py: OAuth provider integration
    - rbac.py: Role and permission management
    - sessions.py: Session storage and management
    - mfa.py: TOTP and backup code utilities
"""

from .jwt import JWTAuthGenerator
from .mfa import MFAGenerator
from .oauth import OAuthIntegrationGenerator
from .rbac import RBACPermissionGenerator
from .sessions import SessionManagementGenerator
from .migrations import AuthMigrationGenerator

__all__ = [
    "JWTAuthGenerator",
    "MFAGenerator",
    "OAuthIntegrationGenerator",
    "RBACPermissionGenerator",
    "SessionManagementGenerator",
    "AuthMigrationGenerator",
]
