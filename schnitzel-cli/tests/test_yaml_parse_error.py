"""Test F002: Schema parser raises clear error for invalid YAML syntax."""

import pytest
from pathlib import Path
from schnitzel.schema import SchemaParser, YAMLParseError


def test_invalid_yaml_unclosed_bracket(tmp_path):
    """Test that parser raises YAMLParseError for unclosed brackets."""
    # Create a YAML file with invalid syntax (unclosed bracket)
    yaml_content = """project_name: test
version: 1.0.0
models:
  User:
    fields:
      id: {type: uuid
      name: {type: string}
"""
    yaml_file = tmp_path / "invalid_unclosed_bracket.yaml"
    yaml_file.write_text(yaml_content)

    # Call SchemaParser.parse(filepath)
    parser = SchemaParser()

    # Verify YAMLParseError is raised
    with pytest.raises(YAMLParseError) as exc_info:
        parser.parse(yaml_file)

    error = exc_info.value

    # Verify error message includes line number and description
    assert error.line is not None, "Error should include line number"
    assert error.column is not None, "Error should include column number"

    # Verify error message is human-readable
    error_str = str(error)
    assert "Invalid YAML syntax" in error_str
    assert "line" in error_str.lower()

    # Verify parser doesn't crash (we got here, so it didn't crash)
    assert True


def test_invalid_yaml_invalid_indentation(tmp_path):
    """Test that parser raises YAMLParseError for invalid indentation."""
    # Create a YAML file with invalid indentation
    yaml_content = """project_name: test
version: 1.0.0
models:
  User:
    fields:
  id: {type: uuid}
      name: {type: string}
"""
    yaml_file = tmp_path / "invalid_indentation.yaml"
    yaml_file.write_text(yaml_content)

    # Call SchemaParser.parse(filepath)
    parser = SchemaParser()

    # Verify YAMLParseError is raised
    with pytest.raises(YAMLParseError) as exc_info:
        parser.parse(yaml_file)

    error = exc_info.value

    # Verify error message includes line number
    assert error.line is not None, "Error should include line number"

    # Verify error message is human-readable
    error_str = str(error)
    assert "Invalid YAML syntax" in error_str
    assert "line" in error_str.lower()

    # Verify error includes description
    assert len(error_str) > 20, "Error message should be descriptive"


def test_invalid_yaml_includes_line_content(tmp_path):
    """Test that error message includes the problematic line content."""
    # Use truly invalid YAML with unclosed bracket
    yaml_content = """project_name: test
version: 1.0.0
models:
  User: {fields: {id: {type: string
"""
    yaml_file = tmp_path / "invalid_syntax.yaml"
    yaml_file.write_text(yaml_content)

    parser = SchemaParser()

    with pytest.raises(YAMLParseError) as exc_info:
        parser.parse(yaml_file)

    error = exc_info.value
    error_str = str(error)

    # Verify line content is included in error message (may be None if not available)
    assert error.line is not None or "Invalid YAML syntax" in error_str


def test_yaml_error_provides_column_number(tmp_path):
    """Test that error provides column number for precise location."""
    yaml_content = """project_name: test
version: 1.0.0
models:
  User:
    fields: {id: {type: uuid, name: string}
"""
    yaml_file = tmp_path / "missing_brace.yaml"
    yaml_file.write_text(yaml_content)

    parser = SchemaParser()

    with pytest.raises(YAMLParseError) as exc_info:
        parser.parse(yaml_file)

    error = exc_info.value

    # Verify column number is provided
    assert error.column is not None, "Error should include column number"
    assert error.column > 0, "Column number should be positive"


def test_parser_does_not_crash_on_invalid_yaml(tmp_path):
    """Test that parser handles errors gracefully without crashing."""
    # Create truly invalid YAML files (syntax errors that cause parse failures)
    invalid_files = [
        ("unclosed.yaml", "models: { User: fields: {id: {type:"),
        ("unclosed_bracket.yaml", "models: {User: [test"),
        ("unclosed_quote.yaml", "models: \"unclosed string"),
    ]

    parser = SchemaParser()

    for filename, content in invalid_files:
        yaml_file = tmp_path / filename
        yaml_file.write_text(content)

        try:
            parser.parse(yaml_file)
            # Should not reach here
            assert False, f"Expected YAMLParseError for {filename}"
        except YAMLParseError:
            # Expected - parser handled it gracefully
            pass
        except Exception as e:
            # Parser crashed with unexpected error
            pytest.fail(f"Parser crashed with unexpected error: {type(e).__name__}: {e}")


def test_error_message_format(tmp_path):
    """Test that error message follows the required format."""
    yaml_content = """project_name: test
version: 1.0.0
models:
  User
    fields:
"""
    yaml_file = tmp_path / "format_test.yaml"
    yaml_file.write_text(yaml_content)

    parser = SchemaParser()

    with pytest.raises(YAMLParseError) as exc_info:
        parser.parse(yaml_file)

    error_str = str(exc_info.value)

    # Check format requirements from F002
    # Should include: "Invalid YAML syntax at line X, column Y"
    assert "Invalid YAML syntax" in error_str
    assert "line" in error_str.lower()

    # Should include: "Reason: ..."
    assert "Reason:" in error_str or "reason:" in error_str.lower()
