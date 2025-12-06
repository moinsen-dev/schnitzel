"""Flutter app main.dart generator for Schnitzel schemas.

Generates the main.dart entry point for Flutter applications with:
- MaterialApp.router setup with go_router
- Theme configuration
- App initialization
- MultiRepositoryProvider for BLoC pattern
"""

import re
from datetime import datetime
from pathlib import Path

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema


class FlutterAppMainGenerator:
    """Generates main.dart entry point for Flutter applications."""

    def __init__(self):
        """Initialize the Flutter app main generator."""
        pass

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase.

        Args:
            name: The name to convert (may be snake_case)

        Returns:
            PascalCase version of the name
        """
        if '_' not in name and '-' not in name:
            return name[0].upper() + name[1:] if name else name

        parts = name.replace('-', '_').split('_')
        return ''.join(part.capitalize() for part in parts)

    def _to_title_case(self, name: str) -> str:
        """Convert snake_case to Title Case (with spaces).

        Args:
            name: The name to convert

        Returns:
            Title Case version with spaces
        """
        parts = name.replace('-', '_').split('_')
        return ' '.join(part.capitalize() for part in parts)

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case.

        Args:
            name: The name to convert

        Returns:
            snake_case version of the name
        """
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_crud_models(self, schema: SchnitzelSchema) -> list[str]:
        """Get list of model names that have CRUD enabled.

        Args:
            schema: The Schnitzel schema

        Returns:
            List of model names with crud: true
        """
        crud_models = []
        if schema.models:
            for model_name, model in schema.models.items():
                if model.crud:
                    crud_models.append(model_name)
        return crud_models

    def generate(self, schema: SchnitzelSchema) -> str:
        """Generate main.dart content for a Flutter app.

        Args:
            schema: The Schnitzel schema

        Returns:
            Generated main.dart code as a string
        """
        # Get app name from schema meta or default
        app_name = "My App"
        package_name = "app"
        if schema.meta:
            app_name = self._to_title_case(schema.meta.name)
            package_name = schema.meta.name.lower().replace('-', '_')

        # Get shared package name
        shared_package = f"{package_name}_shared"

        # Generate import for router
        app_class_name = self._to_pascal_case(package_name)

        # Get CRUD models for repository providers
        crud_models = self._get_crud_models(schema)

        # Build repository imports and providers
        repo_imports = ""
        repo_providers = ""
        if crud_models:
            repo_imports = f"import 'repositories/repositories.dart';\n"
            repo_providers = self._generate_repository_providers(crud_models)

        # Build the MaterialApp with or without providers
        if crud_models:
            app_content = self._generate_app_with_providers(
                app_name, app_class_name, repo_providers
            )
        else:
            app_content = self._generate_simple_app(app_name, app_class_name)

        return f'''import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:{shared_package}/generated/api_client.dart';
import 'package:dio/dio.dart';
import 'router.dart';
{repo_imports}
void main() {{
  runApp(const {app_class_name}App());
}}

{app_content}

/// API Client singleton for the app.
/// Configure the base URL to match your backend server.
class ApiClientProvider {{
  static ApiClient? _instance;

  static ApiClient get instance {{
    _instance ??= ApiClient(
      Dio(BaseOptions(
        baseUrl: 'http://localhost:8000',
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
      )),
    );
    return _instance!;
  }}

  /// Initialize with custom configuration.
  static void initialize({{
    required String baseUrl,
    String? token,
  }}) {{
    _instance = ApiClient(
      Dio(BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
      )),
      token: token,
    );
  }}
}}
'''

    def _generate_repository_providers(self, crud_models: list[str]) -> str:
        """Generate RepositoryProvider list for MultiRepositoryProvider.

        Args:
            crud_models: List of model names with CRUD enabled

        Returns:
            Dart code for repository providers
        """
        providers = []
        for model_name in crud_models:
            pascal_name = self._to_pascal_case(model_name)
            providers.append(
                f"        RepositoryProvider<{pascal_name}Repository>(\n"
                f"          create: (_) => {pascal_name}RepositoryImpl(\n"
                f"            apiClient: ApiClientProvider.instance,\n"
                f"          ),\n"
                f"        ),"
            )
        return "\n".join(providers)

    def _generate_app_with_providers(
        self, app_name: str, app_class_name: str, repo_providers: str
    ) -> str:
        """Generate app class with MultiRepositoryProvider.

        Args:
            app_name: Display name for the app
            app_class_name: PascalCase class name
            repo_providers: Generated repository providers code

        Returns:
            Dart code for the app class with providers
        """
        return f'''class {app_class_name}App extends StatelessWidget {{
  const {app_class_name}App({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MultiRepositoryProvider(
      providers: [
{repo_providers}
      ],
      child: MaterialApp.router(
        title: '{app_name}',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.deepPurple,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
        themeMode: ThemeMode.system,
        routerConfig: router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }}
}}'''

    def _generate_simple_app(self, app_name: str, app_class_name: str) -> str:
        """Generate simple app class without providers.

        Args:
            app_name: Display name for the app
            app_class_name: PascalCase class name

        Returns:
            Dart code for a simple app class
        """
        return f'''class {app_class_name}App extends StatelessWidget {{
  const {app_class_name}App({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp.router(
      title: '{app_name}',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      themeMode: ThemeMode.system,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }}
}}'''

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate main.dart and write it to a file.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where main.dart should be written (apps/{name}/lib/)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to main.dart file, size in bytes)
        """
        output_path = Path(output_dir)

        # Generate the main.dart code
        main_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        full_code = header + main_code

        # Calculate file path and size
        main_file = output_path / "main.dart"
        file_size = len(full_code.encode("utf-8"))

        if dry_run:
            return main_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        main_file.write_text(full_code, encoding="utf-8")

        return main_file, file_size

    def generate_widget_test(self, schema: SchnitzelSchema) -> str:
        """Generate a working widget test file.

        Args:
            schema: The Schnitzel schema

        Returns:
            Generated widget_test.dart code as a string
        """
        # Get app name from schema meta
        package_name = "app"
        app_name = "My App"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')
            app_name = self._to_title_case(schema.meta.name)

        app_class_name = self._to_pascal_case(package_name)

        return f'''import 'package:flutter_test/flutter_test.dart';
import 'package:{package_name}/main.dart';

void main() {{
  testWidgets('App loads home screen smoke test', (WidgetTester tester) async {{
    // Build our app and trigger a frame.
    await tester.pumpWidget(const {app_class_name}App());
    await tester.pumpAndSettle();

    // Verify that we see the home screen title
    expect(find.text('{app_name}'), findsWidgets);
  }});
}}
'''

    def generate_widget_test_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """Generate widget_test.dart and write it to a file.

        Args:
            schema: The Schnitzel schema
            output_dir: Directory where widget_test.dart should be written (apps/{name}/test/)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to widget_test.dart file, size in bytes)
        """
        output_path = Path(output_dir)

        # Generate the test code
        test_code = self.generate_widget_test(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""// Generated by Schnitzel Framework v{__version__}
// DO NOT EDIT - This file is auto-generated
// Generated at: {timestamp}
// Source: {schema_source}

"""

        full_code = header + test_code

        # Calculate file path and size
        test_file = output_path / "widget_test.dart"
        file_size = len(full_code.encode("utf-8"))

        if dry_run:
            return test_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        test_file.write_text(full_code, encoding="utf-8")

        return test_file, file_size
