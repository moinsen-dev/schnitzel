"""Integration tests for validate command JSON output (api_104).

Tests for:
- api_104: Validate command produces JSON output for CI/CD
"""

import pytest
import json
import tempfile
from pathlib import Path
from schnitzel.schema import SchemaParser, SchemaValidator, ValidationResult


class TestValidateJsonOutput:
    """Tests for api_104: Validate command produces JSON output for CI/CD."""

    def test_validation_result_to_dict(self):
        """Test that ValidationResult can be converted to dict."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=["Warning 1"],
            unique_fields={"User": ["email"]}
        )

        as_dict = result.model_dump()

        assert isinstance(as_dict, dict)
        assert as_dict["valid"] == True
        assert as_dict["errors"] == []
        assert as_dict["warnings"] == ["Warning 1"]
        assert as_dict["unique_fields"]["User"] == ["email"]

    def test_validation_result_json_serializable(self):
        """Test that ValidationResult is JSON serializable."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=["Warning 1", "Warning 2"],
            unique_fields={"User": ["email", "username"]}
        )

        # Should not raise
        json_str = json.dumps(result.model_dump())

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["valid"] == True
        assert len(parsed["warnings"]) == 2

    def test_failed_validation_json_output(self):
        """Test JSON output for failed validation."""
        result = ValidationResult.failure(
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )

        json_output = result.model_dump()

        assert json_output["valid"] == False
        assert len(json_output["errors"]) == 2
        assert len(json_output["warnings"]) == 1

    def test_json_output_includes_summary(self):
        """Test that JSON output can include summary data."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            unique_fields={"User": ["email"], "Product": ["sku"]}
        )

        output = result.model_dump()

        # Should include unique fields (part of summary)
        assert "unique_fields" in output
        assert len(output["unique_fields"]) == 2

    def test_validation_result_from_validator(self):
        """Test that validator produces serializable results."""
        # Create a simple schema
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
version: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
""")
            f.flush()

            parser = SchemaParser()
            schema = parser.parse(Path(f.name))

            validator = SchemaValidator()
            result = validator.validate(schema)

            # Should be JSON serializable
            json_output = json.dumps(result.model_dump())
            parsed = json.loads(json_output)

            assert "valid" in parsed
            assert "errors" in parsed
            assert "warnings" in parsed

    def test_json_output_error_format(self):
        """Test that errors are properly formatted in JSON."""
        result = ValidationResult.failure(
            errors=[
                "Field 'name' in model 'User' has invalid type 'invalid_type'",
                "Model 'BadModel' name does not follow PascalCase"
            ]
        )

        output = result.model_dump()

        assert isinstance(output["errors"], list)
        assert all(isinstance(e, str) for e in output["errors"])
        assert len(output["errors"]) == 2

    def test_json_output_warning_format(self):
        """Test that warnings are properly formatted in JSON."""
        result = ValidationResult.success(
            warnings=[
                "Field 'userName' should be 'user_name' (snake_case)",
                "Model 'userProfile' should be 'UserProfile' (PascalCase)"
            ]
        )

        output = result.model_dump()

        assert isinstance(output["warnings"], list)
        assert all(isinstance(w, str) for w in output["warnings"])
        assert len(output["warnings"]) == 2

    def test_empty_validation_result(self):
        """Test JSON output for empty/clean validation."""
        result = ValidationResult.success()

        output = result.model_dump()

        assert output["valid"] == True
        assert output["errors"] == []
        assert output["warnings"] == []
        assert output["unique_fields"] == {}

    def test_json_output_for_ci_cd_parsing(self):
        """Test that JSON output can be parsed by typical CI/CD tools."""
        result = ValidationResult(
            valid=False,
            errors=["Critical error"],
            warnings=["Non-critical warning"],
            unique_fields={}
        )

        json_str = json.dumps(result.model_dump())

        # Parse like a CI/CD tool would
        data = json.loads(json_str)

        # Common CI/CD checks
        if not data["valid"]:
            error_count = len(data["errors"])
            assert error_count > 0

        warning_count = len(data["warnings"])
        assert warning_count == 1

    def test_json_output_structure_consistency(self):
        """Test that JSON output has consistent structure."""
        valid_result = ValidationResult.success(warnings=["warn"])
        invalid_result = ValidationResult.failure(errors=["err"])

        valid_output = valid_result.model_dump()
        invalid_output = invalid_result.model_dump()

        # Both should have same keys
        assert set(valid_output.keys()) == set(invalid_output.keys())
        assert "valid" in valid_output
        assert "errors" in valid_output
        assert "warnings" in valid_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
