"""Flutter app pubspec.yaml updater for Schnitzel schemas.

Updates the app's pubspec.yaml to add required dependencies:
- Reference to shared package
- dio for HTTP client
- go_router for navigation
- flutter_bloc for state management
- equatable for value equality in BLoC states

Dev dependencies for testing:
- faker for generating fake test data
- mockito for mocking in tests
- build_runner for code generation
"""

from datetime import datetime
from pathlib import Path
import yaml

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema


class FlutterAppPubspecGenerator:
    """Updates app pubspec.yaml with required dependencies."""

    def __init__(self):
        """Initialize the Flutter app pubspec generator."""
        pass

    def update_pubspec(
        self,
        schema: SchnitzelSchema,
        app_dir: str | Path,
        dry_run: bool = False,
    ) -> tuple[Path, bool]:
        """Update app's pubspec.yaml with required dependencies.

        Args:
            schema: The Schnitzel schema
            app_dir: Directory of the Flutter app (apps/{name}/)
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to pubspec.yaml, whether changes were made)
        """
        app_path = Path(app_dir)
        pubspec_file = app_path / "pubspec.yaml"

        if not pubspec_file.exists():
            return pubspec_file, False

        # Get package name from schema
        package_name = "app"
        if schema.meta:
            package_name = schema.meta.name.lower().replace('-', '_')

        shared_package = f"{package_name}_shared"

        # Read existing pubspec
        content = pubspec_file.read_text(encoding="utf-8")

        # Parse YAML
        pubspec = yaml.safe_load(content)

        if 'dependencies' not in pubspec:
            pubspec['dependencies'] = {}

        deps = pubspec['dependencies']
        changes_made = False

        # Add dio dependency if not present
        if 'dio' not in deps:
            deps['dio'] = '^5.9.0'
            changes_made = True

        # Add flutter_bloc for state management
        if 'flutter_bloc' not in deps:
            deps['flutter_bloc'] = '^9.0.0'
            changes_made = True

        # Add equatable for value equality in BLoC states
        if 'equatable' not in deps:
            deps['equatable'] = '^2.0.7'
            changes_made = True

        # Add shared package dependency if not present
        if shared_package not in deps:
            deps[shared_package] = {
                'path': f'../../packages/shared'
            }
            changes_made = True

        # Add dev_dependencies for testing
        if 'dev_dependencies' not in pubspec:
            pubspec['dev_dependencies'] = {}

        dev_deps = pubspec['dev_dependencies']

        # Add faker for test factories
        if 'faker' not in dev_deps:
            dev_deps['faker'] = '^2.2.0'
            changes_made = True

        # Add mockito for mocks
        if 'mockito' not in dev_deps:
            dev_deps['mockito'] = '^5.4.5'
            changes_made = True

        # Add build_runner for mockito code generation
        if 'build_runner' not in dev_deps:
            dev_deps['build_runner'] = '^2.4.15'
            changes_made = True

        if dry_run:
            return pubspec_file, changes_made

        if changes_made:
            # Write back preserving order by manual construction
            # This avoids yaml.dump reordering the file
            new_content = self._insert_dependencies(content, shared_package)
            pubspec_file.write_text(new_content, encoding="utf-8")

        return pubspec_file, changes_made

    def _insert_dependencies(self, content: str, shared_package: str) -> str:
        """Insert dependencies into pubspec.yaml content preserving format.

        Args:
            content: Original pubspec.yaml content
            shared_package: Name of the shared package

        Returns:
            Modified content with dependencies added
        """
        lines = content.split('\n')
        result_lines = []
        in_dependencies = False
        in_dev_dependencies = False
        dependencies_added = False
        dev_dependencies_added = False
        dio_exists = 'dio:' in content
        flutter_bloc_exists = 'flutter_bloc:' in content
        equatable_exists = 'equatable:' in content
        shared_exists = f'{shared_package}:' in content
        faker_exists = 'faker:' in content
        mockito_exists = 'mockito:' in content
        build_runner_exists = 'build_runner:' in content
        has_dev_dependencies = 'dev_dependencies:' in content

        for i, line in enumerate(lines):
            result_lines.append(line)

            # Check if we're entering dependencies section
            if line.strip() == 'dependencies:':
                in_dependencies = True
                continue

            # Check if we're entering dev_dependencies section
            if line.strip() == 'dev_dependencies:':
                in_dev_dependencies = True
                in_dependencies = False
                continue

            # Add our dependencies after first dependency in the section
            if in_dependencies and not dependencies_added:
                # Look for first dependency (indented line with something after :)
                if line.startswith('  ') and ':' in line and not line.strip().startswith('#'):
                    # This is the first dependency, add ours after flutter sdk block
                    # Check if this is flutter: sdk: flutter block
                    if 'flutter:' in line and i + 1 < len(lines) and 'sdk: flutter' in lines[i + 1]:
                        continue  # Wait for after the sdk line

                    # If we see "sdk: flutter", add our deps after this
                    if 'sdk: flutter' in line:
                        if not dio_exists:
                            result_lines.append('  dio: ^5.9.0')
                        if not flutter_bloc_exists:
                            result_lines.append('  flutter_bloc: ^9.0.0')
                        if not equatable_exists:
                            result_lines.append('  equatable: ^2.0.7')
                        if not shared_exists:
                            result_lines.append(f'  {shared_package}:')
                            result_lines.append('    path: ../../packages/shared')
                        dependencies_added = True
                        in_dependencies = False

            # Add dev dependencies after first dev dependency
            if in_dev_dependencies and not dev_dependencies_added:
                if line.startswith('  ') and ':' in line and not line.strip().startswith('#'):
                    # Check for flutter_test sdk line
                    if 'sdk: flutter' in line:
                        if not faker_exists:
                            result_lines.append('  faker: ^2.2.0')
                        if not mockito_exists:
                            result_lines.append('  mockito: ^5.4.5')
                        if not build_runner_exists:
                            result_lines.append('  build_runner: ^2.4.15')
                        dev_dependencies_added = True
                        in_dev_dependencies = False

            # Exit dependencies when we hit another top-level key
            if in_dependencies and line and not line.startswith(' ') and not line.startswith('#') and ':' in line:
                in_dependencies = False
            if in_dev_dependencies and line and not line.startswith(' ') and not line.startswith('#') and ':' in line:
                in_dev_dependencies = False

        # If dev_dependencies section didn't exist, add it at the end before flutter section
        if not has_dev_dependencies and not dev_dependencies_added:
            # Find where to insert dev_dependencies (before flutter: or at end)
            insert_pos = len(result_lines)
            for i, line in enumerate(result_lines):
                if line.strip() == 'flutter:':
                    insert_pos = i
                    break

            dev_deps_lines = [
                '',
                'dev_dependencies:',
                '  flutter_test:',
                '    sdk: flutter',
            ]
            if not faker_exists:
                dev_deps_lines.append('  faker: ^2.2.0')
            if not mockito_exists:
                dev_deps_lines.append('  mockito: ^5.4.5')
            if not build_runner_exists:
                dev_deps_lines.append('  build_runner: ^2.4.15')

            result_lines = result_lines[:insert_pos] + dev_deps_lines + result_lines[insert_pos:]

        return '\n'.join(result_lines)

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        app_dir: str | Path,
        dry_run: bool = False,
    ) -> tuple[Path, bool]:
        """Alias for update_pubspec for consistency with other generators.

        Args:
            schema: The Schnitzel schema
            app_dir: Directory of the Flutter app
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to pubspec.yaml, whether changes were made)
        """
        return self.update_pubspec(schema, app_dir, dry_run)
