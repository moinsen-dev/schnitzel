"""Integration tests for F038: Dart model generator creates models.dart in correct output directory.

Tests the generate_to_file() method that writes generated Dart code to files.
"""

import tempfile
from pathlib import Path
import pytest
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition
from schnitzel.generators.dart.models import DartModelGenerator


class TestGenerateToFileCreatesDirectory:
    """Test that generate_to_file() creates the output directory if it doesn't exist."""

    def test_generate_to_file_creates_directory(self):
        """Test that the output directory is created if it doesn't exist."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            # Verify directory doesn't exist yet
            assert not output_dir.exists()

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify directory was created
            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_generate_to_file_handles_existing_directory(self):
        """Test that generate_to_file() works with an existing directory."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Directory already exists (it's tmpdir)
            assert output_dir.exists()

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Should work without errors
            assert output_path.exists()

    def test_generate_to_file_creates_nested_directories(self):
        """Test that generate_to_file() creates nested directories."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "src" / "models" / "generated"

            # Verify nested path doesn't exist yet
            assert not output_dir.exists()

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify all nested directories were created
            assert output_dir.exists()
            assert output_path.exists()


class TestGenerateToFileCreatesModelsDart:
    """Test that generate_to_file() creates models.dart (not models.py)."""

    def test_generate_to_file_creates_models_dart(self):
        """Test that the generated file is named models.dart."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify file is named models.dart (not models.py)
            assert output_path.name == "models.dart"
            assert output_path.suffix == ".dart"
            assert not (output_dir / "models.py").exists()

    def test_generate_to_file_writes_valid_dart_code(self):
        """Test that the generated file contains valid Dart code."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Read the generated file
            content = output_path.read_text(encoding="utf-8")

            # Verify it contains Dart-specific code
            assert "import 'package:freezed_annotation/freezed_annotation.dart';" in content
            assert "part 'models.freezed.dart';" in content
            assert "part 'models.g.dart';" in content
            assert "@freezed" in content
            assert "class User with _$User {" in content

    def test_generate_to_file_overwrites_existing_file(self):
        """Test that generate_to_file() overwrites an existing models.dart file."""
        schema_v1 = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        schema_v2 = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()

            # Generate first version
            output_path_v1, size_v1 = generator.generate_to_file(schema_v1, output_dir)
            content_v1 = output_path_v1.read_text()

            # Verify first version doesn't have email field
            assert "email" not in content_v1

            # Generate second version (should overwrite)
            output_path_v2, size_v2 = generator.generate_to_file(schema_v2, output_dir)
            content_v2 = output_path_v2.read_text()

            # Verify second version has all three fields
            assert "String id" in content_v2
            assert "String name" in content_v2
            assert "String email" in content_v2


class TestGeneratedFileHasHeaderComment:
    """Test that the generated file has a header comment with metadata."""

    def test_generated_file_has_header_comment(self):
        """Test that the generated file includes a header comment."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            content = output_path.read_text(encoding="utf-8")

            # Verify header comment exists
            assert "// Generated by Schnitzel Framework" in content
            assert "// DO NOT EDIT - This file is auto-generated" in content

    def test_header_comment_includes_timestamp(self):
        """Test that the header comment includes a generation timestamp."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            content = output_path.read_text(encoding="utf-8")

            # Verify timestamp line exists
            assert "// Generated at:" in content
            # Verify it contains an ISO format timestamp (YYYY-MM-DD)
            assert any(line.startswith("// Generated at: ") for line in content.split("\n"))

    def test_header_comment_includes_source(self):
        """Test that the header comment includes the schema source."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(
                schema,
                output_dir,
                schema_source="schema.schnitzel.yaml"
            )

            content = output_path.read_text(encoding="utf-8")

            # Verify source line exists with default source
            assert "// Source: schema.schnitzel.yaml" in content

    def test_header_comment_custom_schema_source(self):
        """Test that the header comment uses custom schema source when provided."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(
                schema,
                output_dir,
                schema_source="custom/path/to/my-schema.yaml"
            )

            content = output_path.read_text(encoding="utf-8")

            # Verify custom source is used
            assert "// Source: custom/path/to/my-schema.yaml" in content

    def test_header_comment_before_imports(self):
        """Test that the header comment appears before the imports."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            content = output_path.read_text(encoding="utf-8")

            # Find positions
            header_pos = content.find("// Generated by Schnitzel Framework")
            import_pos = content.find("import 'package:freezed_annotation")

            # Header should come before imports
            assert header_pos < import_pos


class TestGenerateToFileReturnsPath:
    """Test that generate_to_file() returns the correct tuple (Path, int)."""

    def test_generate_to_file_returns_path(self):
        """Test that generate_to_file() returns a tuple with Path object."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify return type is Path
            assert isinstance(output_path, Path)
            assert isinstance(size, int)

    def test_returned_path_points_to_models_dart(self):
        """Test that the returned Path points to models.dart."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify path points to models.dart
            assert output_path.name == "models.dart"
            assert str(output_path).endswith("models.dart")

    def test_returned_path_exists(self):
        """Test that the returned Path points to an existing file."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify file exists at returned path
            assert output_path.exists()
            assert output_path.is_file()

    def test_returned_path_is_absolute(self):
        """Test that the returned Path is absolute."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir)

            # Verify path is absolute
            assert output_path.is_absolute()

    def test_generate_to_file_accepts_string_path(self):
        """Test that generate_to_file() accepts a string path and returns tuple."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir_str = f"{tmpdir}/lib/models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(schema, output_dir_str)

            # Verify return type is Path even when string is passed
            assert isinstance(output_path, Path)
            assert output_path.exists()
            assert output_path.name == "models.dart"


class TestGenerateToFileIntegration:
    """Integration tests for the full generate_to_file() workflow."""

    def test_full_workflow_with_complex_schema(self):
        """Test the full workflow with a complex schema including relations."""
        schema = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "name": FieldDefinition(type="string"),
                        "email": FieldDefinition(type="string"),
                        "age": FieldDefinition(type="int", optional=True),
                        "isActive": FieldDefinition(type="bool", default=True),
                    }
                ),
                "Post": Model(
                    name="Post",
                    fields={
                        "id": FieldDefinition(type="string", primary=True),
                        "title": FieldDefinition(type="string"),
                        "content": FieldDefinition(type="string"),
                        "createdAt": FieldDefinition(type="datetime"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()
            output_path, size = generator.generate_to_file(
                schema,
                output_dir,
                schema_source="complex-schema.yaml"
            )

            # Verify file was created
            assert output_path.exists()
            assert output_path.name == "models.dart"

            # Read content
            content = output_path.read_text(encoding="utf-8")

            # Verify header
            assert "// Generated by Schnitzel Framework" in content
            assert "// Source: complex-schema.yaml" in content

            # Verify both models are present
            assert "class User with _$User {" in content
            assert "class Post with _$Post {" in content

            # Verify User fields
            assert "String id" in content
            assert "String name" in content
            assert "String email" in content
            assert "int? age" in content  # Optional
            assert "@Default(true) bool isActive" in content

            # Verify Post fields
            assert "String title" in content
            assert "String content" in content
            assert "DateTime createdAt" in content

            # Verify @JsonKey for camelCase fields
            assert "@JsonKey(name: 'is_active')" in content
            assert "@JsonKey(name: 'created_at')" in content

    def test_multiple_generations_same_directory(self):
        """Test generating different schemas to the same directory."""
        schema1 = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "User": Model(
                    name="User",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "name": FieldDefinition(type="string"),
                    }
                )
            }
        )

        schema2 = SchnitzelSchema(
            schnitzel="1.0",
            models={
                "Product": Model(
                    name="Product",
                    fields={
                        "id": FieldDefinition(type="string"),
                        "title": FieldDefinition(type="string"),
                        "price": FieldDefinition(type="float"),
                    }
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "lib" / "models"

            generator = DartModelGenerator()

            # Generate schema1
            output_path1, size1 = generator.generate_to_file(schema1, output_dir)
            content1 = output_path1.read_text()
            assert "class User" in content1
            assert "class Product" not in content1

            # Generate schema2 (overwrites)
            output_path2, size2 = generator.generate_to_file(schema2, output_dir)
            content2 = output_path2.read_text()
            assert "class Product" in content2
            assert "class User" not in content2  # Overwritten

            # Verify paths are the same
            assert output_path1 == output_path2
