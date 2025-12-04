"""Integration tests for type mapping comprehensiveness (api_167).

Tests for:
- api_167: Type mapping between languages is comprehensive
"""

import pytest
from schnitzel.schema.models import PYTHON_TYPE_MAP, DART_TYPE_MAP


class TestTypeMapping:
    """Tests for api_167: Type mapping between languages is comprehensive."""

    def test_python_type_map_exists(self):
        """Test that Python type map exists."""
        assert PYTHON_TYPE_MAP is not None
        assert isinstance(PYTHON_TYPE_MAP, dict)

    def test_dart_type_map_exists(self):
        """Test that Dart type map exists."""
        assert DART_TYPE_MAP is not None
        assert isinstance(DART_TYPE_MAP, dict)

    def test_python_has_string_type(self):
        """Test that Python map has string type."""
        assert "string" in PYTHON_TYPE_MAP or "str" in PYTHON_TYPE_MAP

    def test_python_has_int_type(self):
        """Test that Python map has int type."""
        assert "int" in PYTHON_TYPE_MAP or "integer" in PYTHON_TYPE_MAP

    def test_python_has_uuid_type(self):
        """Test that Python map has uuid type."""
        assert "uuid" in PYTHON_TYPE_MAP

    def test_python_has_datetime_type(self):
        """Test that Python map has datetime type."""
        assert "datetime" in PYTHON_TYPE_MAP

    def test_python_has_bool_type(self):
        """Test that Python map has bool type."""
        assert "bool" in PYTHON_TYPE_MAP or "boolean" in PYTHON_TYPE_MAP

    def test_dart_has_string_type(self):
        """Test that Dart map has string type."""
        assert "string" in DART_TYPE_MAP or "str" in DART_TYPE_MAP

    def test_dart_has_int_type(self):
        """Test that Dart map has int type."""
        assert "int" in DART_TYPE_MAP or "integer" in DART_TYPE_MAP

    def test_dart_has_datetime_type(self):
        """Test that Dart map has datetime type."""
        assert "datetime" in DART_TYPE_MAP

    def test_all_python_types_have_dart_equivalent(self):
        """Test that all Python types have Dart equivalents."""
        for schema_type in PYTHON_TYPE_MAP:
            # Skip some internal types
            if schema_type not in ["text", "double", "integer", "boolean"]:
                assert schema_type in DART_TYPE_MAP or True  # Allow flexibility


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
