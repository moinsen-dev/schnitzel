"""Dart Repository generator for Schnitzel schemas.

Generates repository interfaces and implementations for BLoC pattern.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, DART_TYPE_MAP


class DartRepositoryGenerator:
    """Generates Dart repository classes for BLoC pattern."""

    def __init__(self):
        """Initialize the repository generator."""
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

    def generate_repository(self, model_name: str, schema: SchnitzelSchema) -> str:
        """Generate repository interface and implementation for a model.

        Args:
            model_name: Name of the model (e.g., "User")
            schema: The Schnitzel schema

        Returns:
            Dart repository code
        """
        snake_name = self._to_snake_case(model_name)
        pascal_name = self._to_pascal_case(model_name)
        plural_name = self._pluralize(snake_name)
        plural_pascal = self._to_pascal_case(plural_name)

        # Get package name for imports
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
        shared_package = f"{package_name}_shared"

        return f'''import 'package:{shared_package}/models/models.dart';
import 'package:{shared_package}/generated/api_client.dart';

/// Repository interface for {pascal_name} operations.
///
/// This abstraction allows for easy testing and swapping implementations.
abstract class {pascal_name}Repository {{
  /// Get all {plural_name} with optional pagination, filtering, and sorting.
  Future<List<{pascal_name}>> getAll({{
    int page = 1,
    int pageSize = 20,
    Map<String, dynamic>? filters,
    String? sortBy,
    String? sortOrder,
  }});

  /// Get a single {snake_name} by ID.
  Future<{pascal_name}> getById(String id);

  /// Create a new {snake_name}.
  Future<{pascal_name}> create({pascal_name} item);

  /// Update an existing {snake_name}.
  Future<{pascal_name}> update({pascal_name} item);

  /// Delete a {snake_name} by ID.
  Future<void> delete(String id);

  /// Get all {plural_name} from local cache.
  Future<List<{pascal_name}>> getAllFromCache();

  /// Update local cache with items.
  Future<void> updateCache(List<{pascal_name}> items);
}}

/// API implementation of {pascal_name}Repository.
///
/// Uses the generated API client for network operations.
class {pascal_name}RepositoryImpl implements {pascal_name}Repository {{
  final ApiClient apiClient;

  /// Local cache for offline support
  List<{pascal_name}> _cache = [];

  {pascal_name}RepositoryImpl({{required this.apiClient}});

  @override
  Future<List<{pascal_name}>> getAll({{
    int page = 1,
    int pageSize = 20,
    Map<String, dynamic>? filters,
    String? sortBy,
    String? sortOrder,
  }}) async {{
    final items = await apiClient.list{plural_pascal}(
      page: page,
      limit: pageSize,
    );
    return items;
  }}

  @override
  Future<{pascal_name}> getById(String id) async {{
    return await apiClient.get{pascal_name}(id);
  }}

  @override
  Future<{pascal_name}> create({pascal_name} item) async {{
    final created = await apiClient.create{pascal_name}(item);
    _cache.add(created);
    return created;
  }}

  @override
  Future<{pascal_name}> update({pascal_name} item) async {{
    final updated = await apiClient.update{pascal_name}(item.id, item);
    final index = _cache.indexWhere((i) => i.id == updated.id);
    if (index >= 0) {{
      _cache[index] = updated;
    }}
    return updated;
  }}

  @override
  Future<void> delete(String id) async {{
    await apiClient.delete{pascal_name}(id);
    _cache.removeWhere((item) => item.id == id);
  }}

  @override
  Future<List<{pascal_name}>> getAllFromCache() async {{
    return List.unmodifiable(_cache);
  }}

  @override
  Future<void> updateCache(List<{pascal_name}> items) async {{
    _cache = List.from(items);
  }}
}}
'''

    def generate_all_repositories(self, schema: SchnitzelSchema) -> str:
        """Generate repositories for all CRUD models.

        Args:
            schema: The Schnitzel schema

        Returns:
            Dart code with all repository classes
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
import 'package:{shared_package}/generated/api_client.dart';

'''

        # Generate each repository
        for model_name in crud_models:
            code += self._generate_repository_class(model_name, schema)
            code += "\n"

        return code

    def _generate_repository_class(self, model_name: str, schema: SchnitzelSchema) -> str:
        """Generate repository class without imports (for combined file)."""
        snake_name = self._to_snake_case(model_name)
        pascal_name = self._to_pascal_case(model_name)
        plural_name = self._pluralize(snake_name)
        plural_pascal = self._to_pascal_case(plural_name)

        return f'''/// Repository interface for {pascal_name} operations.
abstract class {pascal_name}Repository {{
  Future<List<{pascal_name}>> getAll({{
    int page = 1,
    int pageSize = 20,
    Map<String, dynamic>? filters,
    String? sortBy,
    String? sortOrder,
  }});
  Future<{pascal_name}> getById(String id);
  Future<{pascal_name}> create({pascal_name} item);
  Future<{pascal_name}> update({pascal_name} item);
  Future<void> delete(String id);
  Future<List<{pascal_name}>> getAllFromCache();
  Future<void> updateCache(List<{pascal_name}> items);
}}

/// API implementation of {pascal_name}Repository.
class {pascal_name}RepositoryImpl implements {pascal_name}Repository {{
  final ApiClient apiClient;
  List<{pascal_name}> _cache = [];

  {pascal_name}RepositoryImpl({{required this.apiClient}});

  @override
  Future<List<{pascal_name}>> getAll({{
    int page = 1,
    int pageSize = 20,
    Map<String, dynamic>? filters,
    String? sortBy,
    String? sortOrder,
  }}) async {{
    return await apiClient.list{plural_pascal}(page: page, limit: pageSize);
  }}

  @override
  Future<{pascal_name}> getById(String id) async {{
    return await apiClient.get{pascal_name}(id);
  }}

  @override
  Future<{pascal_name}> create({pascal_name} item) async {{
    final created = await apiClient.create{pascal_name}(item);
    _cache.add(created);
    return created;
  }}

  @override
  Future<{pascal_name}> update({pascal_name} item) async {{
    final updated = await apiClient.update{pascal_name}(item.id, item);
    final index = _cache.indexWhere((i) => i.id == updated.id);
    if (index >= 0) _cache[index] = updated;
    return updated;
  }}

  @override
  Future<void> delete(String id) async {{
    await apiClient.delete{pascal_name}(id);
    _cache.removeWhere((item) => item.id == id);
  }}

  @override
  Future<List<{pascal_name}>> getAllFromCache() async => List.unmodifiable(_cache);

  @override
  Future<void> updateCache(List<{pascal_name}> items) async {{
    _cache = List.from(items);
  }}
}}
'''

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate repositories file and write to disk.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where file should be written
            schema_source: Name of source schema for docs
            dry_run: If True, don't write file

        Returns:
            Tuple of (file path, file size in bytes)
        """
        output_path = Path(output_dir)
        file_path = output_path / "repositories.dart"

        # Generate content
        content = self.generate_all_repositories(schema)

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
