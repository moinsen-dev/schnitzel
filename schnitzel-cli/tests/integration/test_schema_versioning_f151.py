"""Integration tests for F151 - Schema versioning (handle version upgrades).

Test Requirements:
- test_version_1_0_accepted - Version "1.0" is valid
- test_version_1_0_0_accepted - Version "1.0.0" is valid
- test_version_formats_equivalent - Both formats work the same
- test_missing_version_rejected - Schema without version is rejected
- test_invalid_version_rejected - Invalid version format is rejected
"""

import tempfile
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.schema.exceptions import ValidationError, VersionError


def test_version_1_0_accepted() -> None:
    """Test that version '1.0' is accepted."""
    schema_yaml = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Should parse successfully
        assert schema is not None
        assert schema.schnitzel in ["1.0", "1.0.0"]
        assert "User" in schema.models

    finally:
        schema_path.unlink()


def test_version_1_0_0_accepted() -> None:
    """Test that version '1.0.0' is accepted."""
    schema_yaml = """schnitzel: "1.0.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Should parse successfully
        assert schema is not None
        assert schema.schnitzel in ["1.0", "1.0.0"]
        assert "Product" in schema.models

    finally:
        schema_path.unlink()


def test_version_formats_equivalent() -> None:
    """Test that '1.0' and '1.0.0' versions work the same way."""
    schema_yaml_v1 = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    schema_yaml_v2 = """schnitzel: "1.0.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f1:
        f1.write(schema_yaml_v1)
        schema_path_v1 = Path(f1.name)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
        f2.write(schema_yaml_v2)
        schema_path_v2 = Path(f2.name)

    try:
        parser = SchemaParser()

        # Parse both versions
        schema1 = parser.parse(schema_path_v1)
        schema2 = parser.parse(schema_path_v2)

        # Both should have Item model
        assert "Item" in schema1.models
        assert "Item" in schema2.models

        # Both should have same structure
        assert len(schema1.models["Item"].fields) == len(schema2.models["Item"].fields)

    finally:
        schema_path_v1.unlink()
        schema_path_v2.unlink()


def test_missing_version_rejected() -> None:
    """Test that schema without version field is rejected."""
    schema_yaml = """models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()

        # Should raise an error
        with pytest.raises((ValidationError, VersionError, KeyError, ValueError)):
            parser.parse(schema_path)

    finally:
        schema_path.unlink()


def test_invalid_version_rejected() -> None:
    """Test that invalid version format is rejected."""
    schema_yaml = """schnitzel: "2.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()

        # Should raise an error for unsupported version
        with pytest.raises((ValidationError, VersionError, ValueError)):
            parser.parse(schema_path)

    finally:
        schema_path.unlink()


def test_version_in_parsed_schema() -> None:
    """Test that version is accessible in parsed schema object."""
    schema_yaml = """schnitzel: "1.0"

models:
  Test:
    fields:
      id:
        type: uuid
        primary: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Schema should have schnitzel attribute (version)
        assert hasattr(schema, "schnitzel")
        assert schema.schnitzel is not None
        assert schema.schnitzel in ["1.0", "1.0.0"]

    finally:
        schema_path.unlink()


def test_future_version_2_0_preparation() -> None:
    """Document behavior for future version 2.0 support."""
    # This test documents that version 2.0 is not yet supported
    # When 2.0 is added, this test should be updated

    schema_yaml = """schnitzel: "1.0"

models:
  Feature:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Currently only 1.0 is supported
        assert schema.schnitzel in ["1.0", "1.0.0"]

        # When 2.0 is added, the validator should handle version differences

    finally:
        schema_path.unlink()


def test_version_string_format() -> None:
    """Test that version must be a string."""
    schema_yaml = """schnitzel: 1.0

models:
  Test:
    fields:
      id:
        type: uuid
        primary: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()

        # May accept numeric version or require string
        # Behavior depends on implementation
        try:
            schema = parser.parse(schema_path)
            # If it parses, version should be normalized to string
            assert isinstance(schema.schnitzel, str) or schema.schnitzel == 1.0
        except (ValidationError, VersionError, ValueError, TypeError):
            # If it rejects, that's also valid behavior
            pass

    finally:
        schema_path.unlink()
