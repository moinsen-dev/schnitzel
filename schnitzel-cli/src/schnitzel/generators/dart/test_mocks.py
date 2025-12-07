"""Dart test mocks generator for Schnitzel schemas.

Generates Mockito mock annotations and Fake repository implementations for testing.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema


class DartMocksGenerator:
    """Generates Dart test mocks and fake repositories for testing."""

    def __init__(self):
        """Initialize the mocks generator."""
        pass

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        if '_' not in name and '-' not in name:
            return name[0].upper() + name[1:] if name else name
        parts = name.replace('-', '_').split('_')
        return ''.join(part.capitalize() for part in parts)

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        if '_' not in name:
            return name
        parts = name.split('_')
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])

    def _pluralize(self, name: str) -> str:
        """Simple pluralization."""
        if name.endswith('y') and len(name) > 1 and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return name + 'es'
        else:
            return name + 's'

    def _get_crud_models(self, schema: SchnitzelSchema) -> Dict[str, Any]:
        """Get models that have crud enabled."""
        crud_models = {}
        if schema.models:
            for model_name, model in schema.models.items():
                if model.crud:
                    crud_models[model_name] = model
        return crud_models

    def generate_mockito_mocks(self, schema: SchnitzelSchema) -> str:
        """Generate Mockito @GenerateMocks annotation file.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dart code with @GenerateMocks annotation
        """
        crud_models = self._get_crud_models(schema)

        if not crud_models:
            return "// No CRUD models found in schema\n"

        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')

        # Generate repository class names
        repo_classes = [f"{self._to_pascal_case(model_name)}Repository"
                       for model_name in crud_models.keys()]

        # Build imports
        code = f'''import 'package:mockito/annotations.dart';
import 'package:{package_name}/repositories/repositories.dart';

@GenerateMocks([{', '.join(repo_classes)}])
void main() {{}}
'''

        return code

    def generate_fake_repository(self, model_name: str, schema: SchnitzelSchema) -> str:
        """Generate a Fake repository implementation for testing.

        Args:
            model_name: Name of the model (e.g., "User")
            schema: The Schnitzel schema

        Returns:
            Dart code for fake repository implementation
        """
        snake_name = self._to_snake_case(model_name)
        pascal_name = self._to_pascal_case(model_name)
        plural_name = self._pluralize(snake_name)

        return f'''/// Fake implementation of {pascal_name}Repository for testing.
///
/// Uses an in-memory list to simulate repository operations.
class Fake{pascal_name}Repository implements {pascal_name}Repository {{
  final List<{pascal_name}> _items = [];

  @override
  Future<List<{pascal_name}>> getAll({{
    int page = 1,
    int pageSize = 20,
    Map<String, dynamic>? filters,
    String? sortBy,
    String? sortOrder,
  }}) async {{
    return List.unmodifiable(_items);
  }}

  @override
  Future<{pascal_name}> getById(String id) async {{
    return _items.firstWhere((item) => item.id == id);
  }}

  @override
  Future<{pascal_name}> create({pascal_name} item) async {{
    _items.add(item);
    return item;
  }}

  @override
  Future<{pascal_name}> update({pascal_name} item) async {{
    final index = _items.indexWhere((i) => i.id == item.id);
    if (index >= 0) _items[index] = item;
    return item;
  }}

  @override
  Future<void> delete(String id) async {{
    _items.removeWhere((item) => item.id == id);
  }}

  @override
  Future<List<{pascal_name}>> getAllFromCache() async => List.unmodifiable(_items);

  @override
  Future<void> updateCache(List<{pascal_name}> items) async {{
    _items.clear();
    _items.addAll(items);
  }}
}}
'''

    def generate_all_fake_repositories(self, schema: SchnitzelSchema) -> str:
        """Generate fake repositories for all CRUD models.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dart code with all fake repository implementations
        """
        crud_models = self._get_crud_models(schema)

        if not crud_models:
            return "// No CRUD models found in schema\n"

        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
        shared_package = f"{package_name}_shared"

        # Generate imports
        code = f'''import 'package:{shared_package}/models/models.dart';
import 'package:{package_name}/repositories/repositories.dart';

'''

        # Generate each fake repository
        for model_name in crud_models:
            code += self.generate_fake_repository(model_name, schema)
            code += "\n"

        return code

    def generate_mocks_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate mocks.dart file with @GenerateMocks annotation.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where file should be written
            schema_source: Name of source schema for docs
            dry_run: If True, don't write file

        Returns:
            Tuple of (file path, file size in bytes)
        """
        output_path = Path(output_dir)
        file_path = output_path / "mocks.dart"

        # Generate content
        content = self.generate_mockito_mocks(schema)

        # Add header
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""
        full_content = header + content
        file_size = len(full_content.encode("utf-8"))

        if not dry_run:
            output_path.mkdir(parents=True, exist_ok=True)
            file_path.write_text(full_content, encoding="utf-8")

        return file_path, file_size

    def generate_fakes_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate fakes.dart file with fake repository implementations.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where file should be written
            schema_source: Name of source schema for docs
            dry_run: If True, don't write file

        Returns:
            Tuple of (file path, file size in bytes)
        """
        output_path = Path(output_dir)
        file_path = output_path / "fakes.dart"

        # Generate content
        content = self.generate_all_fake_repositories(schema)

        # Add header
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""
        full_content = header + content
        file_size = len(full_content.encode("utf-8"))

        if not dry_run:
            output_path.mkdir(parents=True, exist_ok=True)
            file_path.write_text(full_content, encoding="utf-8")

        return file_path, file_size
