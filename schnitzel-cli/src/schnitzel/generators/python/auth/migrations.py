"""Auth migration generator for user table authentication fields.

Generates Alembic migration scripts to add authentication-related columns to user tables.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from jinja2 import Environment, PackageLoader, select_autoescape

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema


class AuthMigrationGenerator:
    """Generates database migrations for authentication fields."""

    def __init__(self):
        """Initialize the auth migration generator."""
        self.env = Environment(
            loader=PackageLoader('schnitzel', 'templates/python'),
            autoescape=select_autoescape(),
        )

    def generate(self, schema: SchnitzelSchema, revision_id: str = None) -> str:
        """
        Generate authentication migration script.

        Generates an Alembic migration that adds authentication columns to the user table:
        - password_hash: bcrypt password hash (nullable for OAuth-only users)
        - mfa_secret: TOTP secret for MFA (nullable)
        - mfa_enabled: Boolean flag for MFA status
        - role: User role for RBAC
        - created_at: Timestamp
        - updated_at: Timestamp with auto-update

        Also creates oauth_providers table for linking OAuth accounts:
        - id: Primary key
        - user_id: Foreign key to users table
        - provider: OAuth provider name (google, apple, etc.)
        - provider_user_id: User ID from provider
        - created_at: Timestamp

        Args:
            schema: The Schnitzel schema to generate migration from
            revision_id: Optional revision ID for the migration (auto-generated if not provided)

        Returns:
            Generated Alembic migration script as a string
        """
        # Extract migration configuration
        migration_config = self._extract_migration_config(schema, revision_id)

        # Load and render template
        template = self.env.get_template("auth/migration.py.j2")
        rendered = template.render(**migration_config)
        return rendered

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        revision_id: str = None,
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """
        Generate auth migration and write it to a file.

        Creates the output directory if it doesn't exist and writes the migration
        to a timestamped file in Alembic format: {revision}_{description}.py

        Args:
            schema: The Schnitzel schema to generate migration from
            output_dir: Directory where migration should be written (e.g., alembic/versions)
            revision_id: Optional revision ID for the migration (auto-generated if not provided)
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to migration file, size in bytes)

        Example:
            >>> generator = AuthMigrationGenerator()
            >>> output_path, size = generator.generate_to_file(
            ...     schema,
            ...     "backend/alembic/versions"
            ... )
            >>> print(f"Migration written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the migration code
        migration_code = self.generate(schema, revision_id)

        # Generate revision ID if not provided
        if revision_id is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            revision_id = f"auth_{timestamp}"

        # Calculate file path
        migration_file = output_path / f"{revision_id}_add_auth_fields.py"
        file_size = len(migration_code.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return migration_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Warn if file already exists
        if migration_file.exists():
            print(f"Warning: Overwriting existing migration: {migration_file}")

        migration_file.write_text(migration_code, encoding="utf-8")

        return migration_file, file_size

    def _extract_migration_config(self, schema: SchnitzelSchema, revision_id: str = None) -> Dict[str, Any]:
        """Extract migration configuration from schema.

        Analyzes the schema to determine which auth columns are needed based on:
        - auth.providers: Determines if password_hash is needed
        - auth.mfa: Determines if MFA columns are needed
        - roles: Determines if role column is needed

        Args:
            schema: The Schnitzel schema
            revision_id: Optional revision ID

        Returns:
            Dictionary with migration configuration
        """
        # Generate revision ID if not provided
        if revision_id is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            revision_id = f"auth_{timestamp}"

        config = {
            "revision": revision_id,
            "down_revision": None,  # Will be filled by Alembic
            "has_password_auth": False,
            "has_oauth": False,
            "has_mfa": False,
            "has_rbac": False,
            "user_table_name": "users",  # Default, could be customized
            "oauth_providers": [],
        }

        # Check if auth is configured
        if schema.auth:
            auth_config = schema.auth

            # Check for email/password authentication
            if hasattr(auth_config, "providers") and auth_config.providers:
                config["has_password_auth"] = "email_password" in auth_config.providers

                # Extract OAuth providers
                oauth_provider_list = []
                if "google" in auth_config.providers:
                    oauth_provider_list.append("google")
                if "apple" in auth_config.providers:
                    oauth_provider_list.append("apple")
                if "microsoft" in auth_config.providers:
                    oauth_provider_list.append("microsoft")
                if "github" in auth_config.providers:
                    oauth_provider_list.append("github")

                config["has_oauth"] = len(oauth_provider_list) > 0
                config["oauth_providers"] = oauth_provider_list

            # Check for MFA
            if hasattr(auth_config, "mfa") and auth_config.mfa:
                config["has_mfa"] = auth_config.mfa.enabled

        # Check for RBAC
        if schema.roles:
            config["has_rbac"] = True

        return config
