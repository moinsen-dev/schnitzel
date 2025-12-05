"""Integration tests for Session Management Generator (auth_034-auth_040).

Tests for:
- auth_034: Session management generator file exists with correct structure
- auth_035: Session management template exists
- auth_036: Session generator creates Redis-based session store
- auth_037: Session generator creates session with unique session ID
- auth_038: Session generator stores user data in session
- auth_039: Session generator implements session expiry
- auth_040: Session generator supports sliding expiration
"""

import pytest
from pathlib import Path
from schnitzel.schema.models import SchnitzelSchema, AuthConfig, SessionConfig
from schnitzel.generators.python.auth.sessions import SessionManagementGenerator


class TestSessionGeneratorStructure:
    """Tests for auth_034: Session management generator file exists with correct structure."""

    def test_session_generator_class_exists(self):
        """Test that SessionManagementGenerator class exists."""
        from schnitzel.generators.python.auth.sessions import SessionManagementGenerator
        assert SessionManagementGenerator is not None

    def test_session_generator_has_generate_method(self):
        """Test that generator has generate method."""
        generator = SessionManagementGenerator()
        assert hasattr(generator, 'generate')
        assert callable(generator.generate)

    def test_session_generator_has_generate_to_file_method(self):
        """Test that generator has generate_to_file method."""
        generator = SessionManagementGenerator()
        assert hasattr(generator, 'generate_to_file')
        assert callable(generator.generate_to_file)

    def test_session_generator_has_extract_session_config_method(self):
        """Test that generator has _extract_session_config method."""
        generator = SessionManagementGenerator()
        assert hasattr(generator, '_extract_session_config')
        assert callable(generator._extract_session_config)

    def test_session_generator_is_exported_from_auth_module(self):
        """Test that SessionManagementGenerator is exported from auth module."""
        from schnitzel.generators.python.auth import SessionManagementGenerator
        assert SessionManagementGenerator is not None


class TestSessionTemplate:
    """Tests for auth_035: Session management template exists."""

    def test_session_template_file_exists(self):
        """Test that sessions.py.j2 template file exists."""
        template_path = Path(__file__).parent.parent.parent / "schnitzel-cli" / "src" / "schnitzel" / "templates" / "python" / "auth" / "sessions.py.j2"
        # Alternative path for running from project root
        if not template_path.exists():
            template_path = Path("schnitzel-cli/src/schnitzel/templates/python/auth/sessions.py.j2")
        if not template_path.exists():
            template_path = Path("src/schnitzel/templates/python/auth/sessions.py.j2")

        assert template_path.exists(), f"Template file not found at {template_path}"

    def test_template_can_be_loaded(self):
        """Test that template can be loaded by Jinja2."""
        generator = SessionManagementGenerator()
        template = generator.env.get_template("auth/sessions.py.j2")
        assert template is not None

    def test_template_has_session_store_class(self):
        """Test that template defines SessionStore class."""
        generator = SessionManagementGenerator()
        template = generator.env.get_template("auth/sessions.py.j2")
        content = template.render(session_config={})
        assert "class SessionStore:" in content

    def test_template_has_session_config_class(self):
        """Test that template defines SessionConfig class."""
        generator = SessionManagementGenerator()
        template = generator.env.get_template("auth/sessions.py.j2")
        content = template.render(session_config={})
        assert "class SessionConfig:" in content


class TestRedisSessionStore:
    """Tests for auth_036: Session generator creates Redis-based session store."""

    def test_generates_redis_based_session_store(self):
        """Test session store generation with Redis backend."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(
                    storage="redis",
                    expiry=3600,
                    sliding_window=True,
                    multi_device=True
                )
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify Redis-based session store components
        assert "class SessionStore:" in code
        assert "from redis import Redis" in code
        assert "redis_client: Optional[Redis]" in code
        assert 'storage: str = "redis"' in code
        assert "self.redis = Redis(" in code

    def test_session_store_has_redis_initialization(self):
        """Test that SessionStore has Redis initialization parameters."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Check Redis initialization parameters
        assert "redis_host: str" in code
        assert "redis_port: int" in code
        assert "redis_db: int" in code
        assert "redis_password: Optional[str]" in code

    def test_session_store_uses_redis_operations(self):
        """Test that SessionStore uses Redis operations."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Check Redis operations
        assert "self.redis.setex" in code
        assert "self.redis.get" in code
        assert "self.redis.delete" in code
        assert "self.redis.expire" in code


class TestUniqueSessionID:
    """Tests for auth_037: Session generator creates session with unique session ID."""

    def test_generates_unique_session_id_using_secrets(self):
        """Test session ID generation using secrets.token_urlsafe."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify secrets.token_urlsafe is used
        assert "import secrets" in code
        assert "secrets.token_urlsafe" in code
        assert "session_id = secrets.token_urlsafe(32)" in code

    def test_create_session_returns_session_id(self):
        """Test that create_session method returns session ID."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify create_session returns session_id
        assert "def create_session(" in code
        assert "return session_id" in code

    def test_session_key_format(self):
        """Test that session keys use correct format."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify session key format
        assert "_get_session_key" in code
        assert 'f"session:{session_id}"' in code


class TestSessionDataStorage:
    """Tests for auth_038: Session generator stores user data in session."""

    def test_stores_user_id_in_session(self):
        """Test that user_id is stored in session data."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify user_id is stored
        assert '"user_id": user_id' in code

    def test_stores_additional_session_data(self):
        """Test that additional data can be stored in session."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify additional data handling
        assert "data: Optional[Dict[str, Any]]" in code
        assert "session_data.update(data)" in code

    def test_stores_timestamps_in_session(self):
        """Test that timestamps are stored in session."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify timestamp fields
        assert '"created_at"' in code
        assert '"last_accessed"' in code
        assert "datetime.utcnow().isoformat()" in code

    def test_session_data_stored_as_json(self):
        """Test that session data is serialized as JSON."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify JSON serialization
        assert "import json" in code
        assert "json.dumps(session_data)" in code
        assert "json.loads(session_json)" in code


class TestSessionExpiry:
    """Tests for auth_039: Session generator implements session expiry."""

    def test_session_expiry_configuration(self):
        """Test that session expiry is configurable."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(
                    storage="redis",
                    expiry=1800  # 30 minutes
                )
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify expiry configuration
        assert "expiry: int = 1800" in code

    def test_session_uses_redis_ttl(self):
        """Test that session uses Redis TTL for expiry."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", expiry=3600)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify Redis TTL usage
        assert "self.redis.setex(key, ttl," in code
        assert "ttl = self.redis.ttl(key)" in code

    def test_remember_me_extended_duration(self):
        """Test that remember_me extends session duration."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(
                    storage="redis",
                    expiry=3600,
                    remember_me_duration=2592000  # 30 days
                )
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify remember_me configuration
        assert "remember_me: bool" in code
        assert "remember_me_duration: int = 2592000" in code
        assert "if remember_me and session_config.remember_me_duration:" in code

    def test_default_expiry_is_one_hour(self):
        """Test that default expiry is 3600 seconds (1 hour)."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify default expiry
        assert "expiry: int = 3600" in code


class TestSlidingExpiration:
    """Tests for auth_040: Session generator supports sliding expiration."""

    def test_sliding_window_configuration(self):
        """Test that sliding_window is configurable."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(
                    storage="redis",
                    sliding_window=True
                )
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify sliding_window configuration
        assert "sliding_window: bool = true" in code or "sliding_window: bool = True" in code

    def test_refresh_session_method_exists(self):
        """Test that refresh_session method exists."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", sliding_window=True)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify refresh_session method
        assert "def refresh_session(self, session_id: str) -> bool:" in code
        assert "self.redis.expire(key, session_config.expiry)" in code

    def test_get_session_refreshes_ttl_when_sliding_enabled(self):
        """Test that get_session refreshes TTL when sliding is enabled."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", sliding_window=True)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify get_session calls refresh_session
        assert "if session_config.sliding_window:" in code
        assert "self.refresh_session(session_id)" in code

    def test_sliding_window_disabled_preserves_ttl(self):
        """Test that TTL is preserved when sliding_window is disabled."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", sliding_window=False)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify sliding_window=false configuration
        assert "sliding_window: bool = false" in code or "sliding_window: bool = False" in code


class TestMultiDeviceSupport:
    """Tests for multi-device session support."""

    def test_multi_device_configuration(self):
        """Test that multi_device is configurable."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", multi_device=True)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify multi_device configuration
        assert "multi_device: bool = true" in code or "multi_device: bool = True" in code

    def test_get_user_sessions_method_exists(self):
        """Test that get_user_sessions method exists."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", multi_device=True)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify get_user_sessions method
        assert "def get_user_sessions(self, user_id: str) -> list[str]:" in code
        assert 'self.redis.scan_iter("session:*")' in code

    def test_delete_user_sessions_method_exists(self):
        """Test that delete_user_sessions method exists."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis", multi_device=True)
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify delete_user_sessions method
        assert "def delete_user_sessions(self, user_id: str) -> int:" in code


class TestSessionStoreOperations:
    """Tests for session store CRUD operations."""

    def test_update_session_method_exists(self):
        """Test that update_session method exists."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify update_session method
        assert "def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:" in code

    def test_delete_session_method_exists(self):
        """Test that delete_session method exists."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        code = generator.generate(schema)

        # Verify delete_session method
        assert "def delete_session(self, session_id: str) -> bool:" in code
        assert "self.redis.delete(key)" in code


class TestGenerateToFile:
    """Tests for generate_to_file method."""

    def test_generate_to_file_creates_file(self, tmp_path):
        """Test that generate_to_file creates the sessions.py file."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        output_path, size = generator.generate_to_file(schema, tmp_path)

        assert output_path.exists()
        assert output_path.name == "sessions.py"
        assert size > 0

    def test_generate_to_file_includes_header(self, tmp_path):
        """Test that generated file includes header comment."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        output_path, size = generator.generate_to_file(schema, tmp_path)

        content = output_path.read_text()
        assert "Generated by Schnitzel Framework" in content
        assert "DO NOT EDIT - This file is auto-generated" in content

    def test_generate_to_file_dry_run(self, tmp_path):
        """Test that dry_run does not create file."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="redis")
            )
        )

        generator = SessionManagementGenerator()
        output_path, size = generator.generate_to_file(schema, tmp_path, dry_run=True)

        assert not output_path.exists()
        assert size > 0  # Size is still calculated


class TestConfigurationExtraction:
    """Tests for configuration extraction from schema."""

    def test_extracts_storage_backend(self):
        """Test that storage backend is extracted correctly."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(storage="memory")
            )
        )

        generator = SessionManagementGenerator()
        config = generator._extract_session_config(schema)

        assert config["storage"] == "memory"

    def test_extracts_expiry_duration(self):
        """Test that expiry duration is extracted correctly."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(expiry=7200)
            )
        )

        generator = SessionManagementGenerator()
        config = generator._extract_session_config(schema)

        assert config["expiry"] == 7200

    def test_extracts_sliding_window_flag(self):
        """Test that sliding_window flag is extracted correctly."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(sliding_window=False)
            )
        )

        generator = SessionManagementGenerator()
        config = generator._extract_session_config(schema)

        assert config["sliding_window"] is False

    def test_extracts_multi_device_flag(self):
        """Test that multi_device flag is extracted correctly."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(multi_device=False)
            )
        )

        generator = SessionManagementGenerator()
        config = generator._extract_session_config(schema)

        assert config["multi_device"] is False

    def test_extracts_remember_me_duration(self):
        """Test that remember_me_duration is extracted correctly."""
        schema = SchnitzelSchema(
            auth=AuthConfig(
                session=SessionConfig(remember_me_duration=604800)
            )
        )

        generator = SessionManagementGenerator()
        config = generator._extract_session_config(schema)

        assert config["remember_me_duration"] == 604800

    def test_defaults_when_no_auth_config(self):
        """Test that defaults are used when no auth config is provided."""
        schema = SchnitzelSchema()

        generator = SessionManagementGenerator()
        config = generator._extract_session_config(schema)

        assert config["storage"] == "redis"
        assert config["expiry"] == 3600
        assert config["sliding_window"] is True
        assert config["multi_device"] is True
        assert config["remember_me_duration"] is None
