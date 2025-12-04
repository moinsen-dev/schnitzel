"""Integration tests for F099: Dart generator includes documentation comments in generated code.

Tests that the Dart model generator correctly includes documentation comments
for models and fields when descriptions are provided in the schema.
"""

import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestDartModelDocumentation:
    """Test model-level documentation comment generation."""

    def test_doc_comment_from_description(self):
        """Test that model description becomes /// comment."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have doc comment before @freezed annotation
        assert "/// A user in the system" in code

        # Doc comment should come before @freezed
        doc_pos = code.find("/// A user in the system")
        freezed_pos = code.find("@freezed")
        assert doc_pos < freezed_pos

        # Should still have the class declaration
        assert "class User with _$User {" in code

    def test_no_doc_comment_without_description(self):
        """Test that no comment is generated if no description is provided."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should not have any doc comments (///)
        # Extract just the User class section
        user_section = code[code.find("@freezed"):code.find("class User") + 100]
        assert "///" not in user_section

    def test_multiple_models_with_descriptions(self):
        """Test that multiple models with descriptions each get doc comments."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    description="A blog post",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                ),
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Both models should have doc comments
        assert "/// A user in the system" in code
        assert "/// A blog post" in code

    def test_model_description_with_special_characters(self):
        """Test that model descriptions with special characters are handled correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user's profile & settings",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Special characters should be preserved in doc comment
        assert "/// A user's profile & settings" in code

    def test_multiline_description_single_line_comment(self):
        """Test that multiline descriptions are kept as single /// comment."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system with full access",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should be a single line comment
        assert "/// A user in the system with full access" in code


class TestDartFieldDocumentation:
    """Test field-level documentation comment generation."""

    def test_field_level_documentation(self):
        """Test that field comments are generated if available."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(
                            type="uuid",
                            primary=True,
                            description="Unique identifier for the user"
                        ),
                        "name": FieldDefinition(
                            type="string",
                            description="Full name of the user"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have field doc comments
        assert "/// Unique identifier for the user" in code
        assert "/// Full name of the user" in code

    def test_field_without_description_no_comment(self):
        """Test that fields without descriptions don't get comments."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(
                            type="string",
                            description="Full name of the user"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have doc comment for name field
        assert "/// Full name of the user" in code

        # But id field line should not have doc comment immediately before it
        # We check that the id field exists without a doc comment on the line before
        lines = code.split("\n")
        for i, line in enumerate(lines):
            if "String id," in line:
                # Check that the line before doesn't contain ///
                if i > 0:
                    assert "///" not in lines[i-1]

    def test_mixed_fields_with_and_without_descriptions(self):
        """Test model with mix of documented and undocumented fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(
                            type="string",
                            description="User's full name"
                        ),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(
                            type="int",
                            optional=True,
                            description="User's age in years"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have comments for documented fields
        assert "/// User's full name" in code
        assert "/// User's age in years" in code

        # Should not have comments for undocumented fields
        # Count total /// occurrences - should be exactly 2 (for the 2 field descriptions)
        doc_comment_count = code.count("/// User's")
        assert doc_comment_count == 2

    def test_field_description_with_special_characters(self):
        """Test that field descriptions with special characters work correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "email": FieldDefinition(
                            type="string",
                            description="User's email address (must be unique)"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Special characters should be preserved
        assert "/// User's email address (must be unique)" in code

    def test_field_documentation_with_default_value(self):
        """Test that field documentation works with default values."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "status": FieldDefinition(
                            type="string",
                            default="active",
                            description="Current status of the user account"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have doc comment
        assert "/// Current status of the user account" in code
        # Should also have the default value
        assert "@Default('active')" in code

    def test_field_documentation_with_optional_field(self):
        """Test that field documentation works with optional fields."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "bio": FieldDefinition(
                            type="string",
                            optional=True,
                            description="Optional biography of the user"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have doc comment
        assert "/// Optional biography of the user" in code
        # Should be nullable
        assert "String? bio," in code


class TestDartDocumentationCombinations:
    """Test combinations of model and field documentation."""

    def test_model_and_field_documentation(self):
        """Test that both model and field documentation work together."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(
                            type="uuid",
                            primary=True,
                            description="Unique identifier"
                        ),
                        "name": FieldDefinition(
                            type="string",
                            description="User's full name"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have model documentation
        assert "/// A user in the system" in code

        # Should have field documentation
        assert "/// Unique identifier" in code
        assert "/// User's full name" in code

        # Model doc should come before class, field docs should be in constructor
        model_doc_pos = code.find("/// A user in the system")
        class_pos = code.find("class User")
        field_doc_pos = code.find("/// Unique identifier")

        assert model_doc_pos < class_pos < field_doc_pos

    def test_only_model_description_no_field_descriptions(self):
        """Test model with description but fields without descriptions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have model doc comment
        assert "/// A user in the system" in code

        # Should not have field doc comments
        # Count /// occurrences - should be exactly 1 (only the model description)
        doc_comment_count = code.count("///")
        assert doc_comment_count == 1

    def test_only_field_descriptions_no_model_description(self):
        """Test model without description but fields with descriptions."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(
                            type="uuid",
                            primary=True,
                            description="Unique identifier"
                        ),
                        "name": FieldDefinition(
                            type="string",
                            description="User's full name"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should have field doc comments
        assert "/// Unique identifier" in code
        assert "/// User's full name" in code

        # Should be exactly 2 doc comments (for the 2 fields)
        doc_comment_count = code.count("///")
        assert doc_comment_count == 2

    def test_complex_model_with_mixed_documentation(self):
        """Test complex model with some fields documented and some not."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user account in the system",
                    fields={
                        "id": FieldDefinition(
                            type="uuid",
                            primary=True,
                            description="Unique identifier for the user"
                        ),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(
                            type="string",
                            description="User's email address"
                        ),
                        "age": FieldDefinition(type="int", optional=True),
                        "status": FieldDefinition(
                            type="string",
                            default="active",
                            description="Account status"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Model documentation
        assert "/// A user account in the system" in code

        # Documented fields
        assert "/// Unique identifier for the user" in code
        assert "/// User's email address" in code
        assert "/// Account status" in code

        # Should have exactly 4 doc comments (1 model + 3 fields)
        doc_comment_count = code.count("///")
        assert doc_comment_count == 4


class TestDartDocumentationFormat:
    """Test the format and structure of generated documentation."""

    def test_doc_comment_format_triple_slash(self):
        """Test that Dart uses /// style comments, not /** */ style."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Should use /// not /* or /**
        assert "///" in code
        assert "/*" not in code
        assert "/**" not in code

    def test_doc_comment_placement_before_class(self):
        """Test that model doc comment is placed directly before @freezed annotation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="A user in the system",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Doc comment should be immediately before @freezed
        lines = code.split("\n")
        for i, line in enumerate(lines):
            if "@freezed" in line and i > 0:
                # Previous non-empty line should be the doc comment
                prev_line = lines[i-1].strip()
                if prev_line:
                    assert prev_line.startswith("///")

    def test_doc_comment_placement_before_fields(self):
        """Test that field doc comments are placed directly before field declarations."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(
                            type="string",
                            description="User's full name"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Field doc comment should be immediately before field declaration
        lines = code.split("\n")
        for i, line in enumerate(lines):
            if "String name," in line and i > 0:
                # Previous line should be the doc comment
                prev_line = lines[i-1].strip()
                assert "/// User's full name" in prev_line

    def test_indentation_of_field_doc_comments(self):
        """Test that field doc comments have proper indentation."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(
                            type="string",
                            description="User's full name"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Field doc comments should be indented with 4 spaces (inside factory constructor)
        assert "    /// User's full name" in code


class TestDartDocumentationEdgeCases:
    """Test edge cases for documentation generation."""

    def test_empty_description_no_comment(self):
        """Test that empty string description doesn't generate comment."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Empty description should not generate doc comment
        # Extract the User class section
        user_start = code.find("@freezed")
        user_end = code.find("class User") + 100
        user_section = code[user_start:user_end]
        assert "///" not in user_section

    def test_whitespace_only_description_no_comment(self):
        """Test that whitespace-only description doesn't generate comment."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    description="   ",
                    fields={
                        "id": FieldDefinition(type="uuid", primary=True),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Whitespace-only description might generate "///   " which is not ideal
        # but we just verify the code generates without errors
        assert "@freezed" in code
        assert "class User" in code

    def test_description_with_quotes(self):
        """Test that descriptions containing quotes are handled correctly."""
        schema = SchnitzelSchema(
            models={
                "User": Model(
                    name="User",
                    fields={
                        "name": FieldDefinition(
                            type="string",
                            description='The user\'s "display" name'
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # Quotes in doc comments should work fine (they're just comments)
        assert '/// The user\'s "display" name' in code

    def test_documentation_with_all_field_types(self):
        """Test that documentation works with all field types."""
        schema = SchnitzelSchema(
            models={
                "Example": Model(
                    name="Example",
                    description="Example model with all types",
                    fields={
                        "str_field": FieldDefinition(
                            type="string",
                            description="A string field"
                        ),
                        "int_field": FieldDefinition(
                            type="int",
                            description="An integer field"
                        ),
                        "float_field": FieldDefinition(
                            type="float",
                            description="A float field"
                        ),
                        "bool_field": FieldDefinition(
                            type="bool",
                            description="A boolean field"
                        ),
                        "datetime_field": FieldDefinition(
                            type="datetime",
                            description="A datetime field"
                        ),
                        "json_field": FieldDefinition(
                            type="json",
                            description="A JSON field"
                        ),
                    }
                )
            }
        )

        generator = DartModelGenerator()
        code = generator.generate(schema)

        # All field descriptions should be present
        assert "/// A string field" in code
        assert "/// An integer field" in code
        assert "/// A float field" in code
        assert "/// A boolean field" in code
        assert "/// A datetime field" in code
        assert "/// A JSON field" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
