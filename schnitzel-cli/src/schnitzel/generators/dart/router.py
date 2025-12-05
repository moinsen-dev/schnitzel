"""Flutter go_router generator for Schnitzel schemas.

Generates router.dart with go_router configuration for:
- Home screen route
- CRUD routes for each model (list, detail, form)
- Navigation structure
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema


class FlutterRouterGenerator:
    """Generates go_router configuration for Flutter applications."""

    def __init__(self):
        """Initialize the Flutter router generator."""
        pass

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        if '_' not in name and '-' not in name:
            return name[0].upper() + name[1:] if name else name
        parts = name.replace('-', '_').split('_')
        return ''.join(part.capitalize() for part in parts)

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _pluralize(self, name: str) -> str:
        """Simple pluralization for route names."""
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

    def generate(self, schema: SchnitzelSchema) -> str:
        """Generate router.dart content with go_router configuration.

        Args:
            schema: The Schnitzel schema

        Returns:
            Generated router.dart code as a string
        """
        crud_models = self._get_crud_models(schema)

        # Build imports for screens
        imports = ["import 'package:flutter/material.dart';"]
        imports.append("import 'package:go_router/go_router.dart';")
        imports.append("import 'screens/home_screen.dart';")

        # Import screens for each CRUD model
        for model_name in crud_models:
            snake_name = self._to_snake_case(model_name)
            imports.append(f"import 'screens/{snake_name}_list_screen.dart';")
            imports.append(f"import 'screens/{snake_name}_detail_screen.dart';")
            imports.append(f"import 'screens/{snake_name}_form_screen.dart';")

        imports_code = '\n'.join(sorted(set(imports)))

        # Build routes
        routes = []

        # Home route
        routes.append("""    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),""")

        # CRUD routes for each model
        for model_name in crud_models:
            snake_name = self._to_snake_case(model_name)
            plural_name = self._pluralize(snake_name)
            pascal_name = self._to_pascal_case(model_name)

            # List route
            routes.append(f"""    GoRoute(
      path: '/{plural_name}',
      builder: (context, state) => const {pascal_name}ListScreen(),
    ),""")

            # Detail route (with id parameter)
            routes.append(f"""    GoRoute(
      path: '/{plural_name}/:id',
      builder: (context, state) {{
        final id = state.pathParameters['id']!;
        return {pascal_name}DetailScreen(id: id);
      }},
    ),""")

            # Create route
            routes.append(f"""    GoRoute(
      path: '/{plural_name}/new',
      builder: (context, state) => const {pascal_name}FormScreen(),
    ),""")

            # Edit route
            routes.append(f"""    GoRoute(
      path: '/{plural_name}/:id/edit',
      builder: (context, state) {{
        final id = state.pathParameters['id']!;
        return {pascal_name}FormScreen(id: id);
      }},
    ),""")

        routes_code = '\n'.join(routes)

        return f'''{imports_code}

/// App router configuration using go_router.
final GoRouter router = GoRouter(
  initialLocation: '/',
  routes: [
{routes_code}
  ],
  errorBuilder: (context, state) => Scaffold(
    appBar: AppBar(title: const Text('Error')),
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            'Page not found',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text('Path: ${{state.uri.path}}'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.go('/'),
            child: const Text('Go Home'),
          ),
        ],
      ),
    ),
  ),
);
'''

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate router.dart and write it to a file.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where router.dart should be written (apps/{name}/lib/)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to router.dart file, size in bytes)
        """
        output_path = Path(output_dir)

        # Generate the router.dart code
        router_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        full_code = header + router_code

        # Calculate file path and size
        router_file = output_path / "router.dart"
        file_size = len(full_code.encode("utf-8"))

        if dry_run:
            return router_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        router_file.write_text(full_code, encoding="utf-8")

        return router_file, file_size
