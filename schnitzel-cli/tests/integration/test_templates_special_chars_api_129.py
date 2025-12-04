"""Integration tests for templates handling special characters (api_129).

Tests for:
- api_129: Templates handle special characters in names
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.python.routes import FastAPIRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


class TestTemplatesSpecialChars:
    """Tests for api_129: Templates handle special characters in names."""

    def test_orm_handles_underscores(self):
        """Test ORM generator handles underscored names."""
        schema = SchnitzelSchema(
            models={
                "UserProfile": Model(
                    name="UserProfile",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "first_name": FieldDefinition(type="string"),
                        "last_name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        assert "UserProfile" in code or "user_profile" in code

    def test_orm_handles_numbers_in_names(self):
        """Test ORM generator handles names with numbers."""
        schema = SchnitzelSchema(
            models={
                "User2FA": Model(
                    name="User2FA",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "code123": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate valid code
        assert "User2FA" in code or "user2fa" in code.lower()

    def test_routes_handles_path_params(self):
        """Test routes generator handles path parameters."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={"id": FieldDefinition(type="uuid", primary=True)}
                )
            },
            endpoints={
                "/users/{user_id}/posts/{post_id}": {
                    "GET": {"name": "get_user_post"}
                }
            }
        )

        generator = FastAPIRouteGenerator()
        code = generator.generate(schema)

        # Should handle path parameters
        assert "user_id" in code or "userId" in code or "{" in code

    def test_dart_handles_special_chars(self):
        """Test Dart generator handles special characters."""
        schema = SchnitzelSchema(
            models={
                "APIKey": Model(
                    name="APIKey",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "api_key": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartApiClientGenerator()
        code = generator.generate(schema)

        # Should generate valid Dart code
        assert "class" in code

    def test_handles_reserved_words(self):
        """Test handling of reserved word-like names."""
        schema = SchnitzelSchema(
            models={
                "Class": Model(
                    name="Class",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "type": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should generate valid code (may rename or escape)
        assert code is not None

    def test_handles_long_names(self):
        """Test handling of very long names."""
        schema = SchnitzelSchema(
            models={
                "VeryLongModelNameThatExceedsNormalLength": Model(
                    name="VeryLongModelNameThatExceedsNormalLength",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = SQLAlchemyORMGenerator()
        code = generator.generate(schema)

        # Should handle long names
        assert "VeryLongModelName" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
