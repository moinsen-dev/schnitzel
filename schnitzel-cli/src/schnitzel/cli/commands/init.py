"""Init command for scaffolding new Schnitzel projects."""

from pathlib import Path
import subprocess
import typer
from rich.console import Console
from schnitzel.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def _is_quiet_mode() -> bool:
    """Check if quiet mode is enabled via CLI.

    Returns:
        bool: True if quiet mode is enabled
    """
    from schnitzel.cli import is_quiet_mode
    return is_quiet_mode()


def _is_flutter_installed() -> bool:
    """Check if Flutter is installed and available in PATH.

    Returns:
        bool: True if Flutter is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["flutter", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _get_schema_template(template: str, project_name: str = "my_app") -> str:
    """Get the schema template content based on template type.

    Args:
        template: Template type ('minimal' or 'full')
        project_name: Name of the project (used for meta section)

    Returns:
        str: Schema template content
    """
    # Sanitize project name for use in schema
    sanitized_name = _sanitize_dart_package_name(project_name)

    if template == "full":
        return f"""schnitzel: 1.0.0

meta:
  name: "{sanitized_name}"
  version: "1.0.0"
  org: "com.example"
  description: "{project_name} application"

models:
  User:
    description: A user in the system
    crud: true
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
      bio:
        type: text
        optional: true
      is_active:
        type: bool
        default: true
      created_at:
        type: datetime
        auto: create
    relations:
      posts:
        type: hasMany
        model: Post
      comments:
        type: hasMany
        model: Comment

  Post:
    description: A blog post
    crud: true
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      author_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      comments:
        type: hasMany
        model: Comment

  Comment:
    description: A comment on a post
    crud: true
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: text
      author_id:
        type: uuid
      post_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
      post:
        type: belongsTo
        model: Post
        foreign_key: post_id
"""
    else:  # minimal (default)
        return f"""# Schnitzel Schema Definition
# Define your data models here

schnitzel: "1.0"

meta:
  name: "{sanitized_name}"
  version: "1.0.0"
  org: "com.example"
  description: "{project_name} application"

models: {{}}
"""


def _is_uv_installed() -> bool:
    """Check if uv is installed and available in PATH.

    Returns:
        bool: True if uv is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _sanitize_dart_package_name(name: str) -> str:
    """Sanitize a project name to be a valid Dart package name.

    Dart package names must:
    - Consist of lowercase words separated by underscores
    - Use only basic Latin letters and Arabic digits
    - Not start with a digit
    - Not be a reserved word

    Args:
        name: Original project name (may contain path components)

    Returns:
        str: Sanitized package name suitable for Dart
    """
    # Extract just the final component if it's a path
    base_name = Path(name).name

    # Replace hyphens and spaces with underscores
    sanitized = base_name.replace("-", "_").replace(" ", "_")

    # Convert to lowercase
    sanitized = sanitized.lower()

    # Remove any characters that aren't alphanumeric or underscore
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")

    # Ensure it doesn't start with a digit
    if sanitized and sanitized[0].isdigit():
        sanitized = f"app_{sanitized}"

    # If empty or just underscores, provide a default
    if not sanitized or sanitized.strip("_") == "":
        sanitized = "flutter_app"

    return sanitized


def _sanitize_python_package_name(name: str) -> str:
    """Sanitize a project name to be a valid Python package name.

    Python package names must:
    - Use only lowercase letters, numbers, and underscores
    - Not start with a number
    - Follow PEP 503 naming conventions

    Args:
        name: Original project name (may contain path components)

    Returns:
        str: Sanitized package name suitable for Python
    """
    # Extract just the final component if it's a path
    base_name = Path(name).name

    # Replace hyphens and spaces with underscores
    sanitized = base_name.replace("-", "_").replace(" ", "_")

    # Convert to lowercase
    sanitized = sanitized.lower()

    # Remove any characters that aren't alphanumeric or underscore
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")

    # Ensure it doesn't start with a digit
    if sanitized and sanitized[0].isdigit():
        sanitized = f"app_{sanitized}"

    # If empty or just underscores, provide a default
    if not sanitized or sanitized.strip("_") == "":
        sanitized = "backend_app"

    return sanitized


def _generate_pyproject_toml(project_name: str) -> str:
    """Generate pyproject.toml content for FastAPI backend.

    Args:
        project_name: Base name for the project

    Returns:
        str: pyproject.toml content with FastAPI dependencies
    """
    # Sanitize the project name to be a valid Python package name
    sanitized_name = _sanitize_python_package_name(project_name)
    # Use base name for description (human-readable)
    display_name = Path(project_name).name
    return f"""[project]
name = "{sanitized_name}-backend"
version = "0.1.0"
description = "FastAPI backend for {display_name}"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.0",
    "prometheus-client>=0.19.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""


def _create_workspace_pubspec(project_path: Path, project_name: str) -> None:
    """Create workspace pubspec.yaml for Flutter multi-package project.

    Args:
        project_path: Path to the project root directory
        project_name: Base name for the project
    """
    # Sanitize project name for Dart package naming rules
    workspace_name = _sanitize_dart_package_name(project_name)

    # Create pubspec.yaml content with new apps/ structure
    pubspec_content = f"""name: {workspace_name}_workspace
description: Schnitzel project workspace

environment:
  sdk: '>=3.5.0 <4.0.0'

workspace:
  - apps/{workspace_name}
  - packages/shared
"""

    # Write pubspec.yaml to project root
    pubspec_file = project_path / "pubspec.yaml"
    pubspec_file.write_text(pubspec_content)
    if not _is_quiet_mode():
        console.print("[green]✓ Workspace pubspec.yaml created[/green]")


def _run_flutter_pub_add(packages_dir: Path, packages: list[str], dev: bool = False) -> bool:
    """Run flutter pub add to add dependencies.

    Args:
        packages_dir: Path to the Flutter package directory
        packages: List of package names to add
        dev: If True, add as dev dependencies

    Returns:
        bool: True if all packages were added successfully
    """
    if not packages:
        return True

    try:
        cmd = ["flutter", "pub", "add"]
        if dev:
            cmd.append("--dev")
        cmd.extend(packages)

        result = subprocess.run(
            cmd,
            cwd=packages_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _add_resolution_workspace(package_dir: Path) -> None:
    """Add resolution: workspace to a pubspec.yaml for Dart workspace support.

    This is required for packages that are part of a Dart/Flutter workspace
    (SDK >= 3.5.0). Without this, 'flutter pub get' at workspace root will fail.

    Args:
        package_dir: Path to the package directory containing pubspec.yaml
    """
    pubspec_file = package_dir / "pubspec.yaml"
    if not pubspec_file.exists():
        return

    content = pubspec_file.read_text(encoding="utf-8")

    # Check if resolution: workspace already exists
    if "resolution:" in content:
        return

    # Insert resolution: workspace after the environment section ends
    # Environment section ends when we find a new top-level key (not indented)
    lines = content.split("\n")
    new_lines = []
    in_environment = False
    resolution_added = False

    for i, line in enumerate(lines):
        # Check if this is a new top-level key after environment section
        if in_environment and not resolution_added:
            # Top-level key starts with letter/underscore and has no leading spaces
            if line and not line.startswith(" ") and not line.startswith("#"):
                # This is the next section, insert resolution before it
                new_lines.append("")
                new_lines.append("resolution: workspace")
                resolution_added = True
                in_environment = False

        new_lines.append(line)

        # Track when we enter environment section
        if line.strip() == "environment:":
            in_environment = True

    # If file ends while still in environment, add at end
    if in_environment and not resolution_added:
        new_lines.append("")
        new_lines.append("resolution: workspace")
        resolution_added = True

    if resolution_added:
        pubspec_file.write_text("\n".join(new_lines), encoding="utf-8")


def _create_flutter_app(apps_dir: Path, project_name: str, org: str = "com.example") -> bool:
    """Create Flutter application in apps/{name} directory.

    Creates a real Flutter app (not a package) with the specified organization.

    Args:
        apps_dir: Path to apps/{project_name} directory
        project_name: Base name for the Flutter project
        org: Organization identifier for Flutter (e.g., 'com.example', 'dev.moinsen')

    Returns:
        bool: True if Flutter app was created successfully, False otherwise
    """
    try:
        # Sanitize project name for Dart package naming rules
        dart_package_name = _sanitize_dart_package_name(project_name)

        # Step 1: Run flutter create (real app, not package)
        # flutter create appName --org com.example --project-name app_name
        result = subprocess.run(
            [
                "flutter", "create",
                str(apps_dir),
                "--org", org,
                "--project-name", dart_package_name
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"flutter create failed: {result.stderr}")
            return False

        # Step 2: Add runtime dependencies with flutter pub add
        # Note: Must be done BEFORE adding resolution: workspace
        runtime_deps = [
            "freezed_annotation",
            "json_annotation",
            "go_router",  # For navigation
        ]
        if not _is_quiet_mode():
            console.print("  [dim]Adding app dependencies (Freezed, go_router)...[/dim]")

        if not _run_flutter_pub_add(apps_dir, runtime_deps, dev=False):
            console.print("  [yellow]Warning: Could not add some runtime dependencies[/yellow]")

        # Step 3: Add dev dependencies with flutter pub add --dev
        dev_deps = [
            "build_runner",
            "freezed",
            "json_serializable",
        ]

        if not _run_flutter_pub_add(apps_dir, dev_deps, dev=True):
            console.print("  [yellow]Warning: Could not add some dev dependencies[/yellow]")

        # Step 4: Add resolution: workspace AFTER dependencies are added
        _add_resolution_workspace(apps_dir)

        return True

    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        logger.error(f"Error creating Flutter app: {e}")
        return False


def _create_flutter_shared(packages_dir: Path, project_name: str) -> bool:
    """Create Flutter shared package in packages/shared directory with Dio and Freezed.

    Args:
        packages_dir: Path to packages/shared directory
        project_name: Base name for the Flutter project

    Returns:
        bool: True if Flutter package was created successfully, False otherwise
    """
    try:
        # Sanitize project name for Dart package naming rules
        dart_package_name = _sanitize_dart_package_name(project_name)

        # Step 1: Run flutter create --template=package
        result = subprocess.run(
            [
                "flutter", "create",
                str(packages_dir),
                "--template=package",
                "--project-name", f"{dart_package_name}_shared"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return False

        # Step 2: Add runtime dependencies (Dio for API client, Freezed for models)
        # Note: Must be done BEFORE adding resolution: workspace
        runtime_deps = [
            "dio",
            "dio_cache_interceptor",
            "freezed_annotation",
            "json_annotation",
        ]
        if not _is_quiet_mode():
            console.print("  [dim]Adding shared package dependencies (Dio, Freezed)...[/dim]")

        if not _run_flutter_pub_add(packages_dir, runtime_deps, dev=False):
            console.print("  [yellow]Warning: Could not add some runtime dependencies to shared package[/yellow]")

        # Step 3: Add dev dependencies with flutter pub add --dev
        dev_deps = [
            "build_runner",
            "freezed",
            "json_serializable",
        ]

        if not _run_flutter_pub_add(packages_dir, dev_deps, dev=True):
            console.print("  [yellow]Warning: Could not add some dev dependencies to shared package[/yellow]")

        # Step 4: Add resolution: workspace AFTER dependencies are added
        _add_resolution_workspace(packages_dir)

        return True

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def _create_backend_app(backend_dir: Path, project_name: str) -> bool:
    """Create Python backend app using uv init.

    Args:
        backend_dir: Path to backend/app directory
        project_name: Base name for the project (used for pyproject.toml)

    Returns:
        bool: True if backend app was created successfully, False otherwise
    """
    try:
        # Run uv init in the backend/app directory
        result = subprocess.run(
            ["uv", "init", str(backend_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )

        uv_init_succeeded = result.returncode == 0

        # Ensure backend directory exists (in case uv init didn't create it)
        backend_dir.mkdir(parents=True, exist_ok=True)

        # Generate pyproject.toml with FastAPI dependencies
        # This happens regardless of whether uv init succeeded or failed
        pyproject_path = backend_dir / "pyproject.toml"
        pyproject_content = _generate_pyproject_toml(project_name)
        pyproject_path.write_text(pyproject_content)

        return uv_init_succeeded

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def init_command(
    project_name: str = typer.Argument(
        ...,
        help="Name of the project to create"
    ),
    with_flutter: bool = typer.Option(
        True,
        "--with-flutter/--no-flutter",
        help="Create Flutter package in packages/app using flutter create"
    ),
    with_backend: bool = typer.Option(
        True,
        "--with-backend/--no-backend",
        help="Initialize Python backend with uv init"
    ),
    template: str = typer.Option(
        "minimal",
        "--template",
        "-t",
        help="Template to use for schema.schnitzel.yaml (choices: minimal, full)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing directory if it exists"
    )
) -> None:
    """Initialize a new Schnitzel project with directory structure.

    Creates a new project directory with the following structure:
    - schema.schnitzel.yaml: Schema definition file
    - apps/{name}/: Flutter application directory (real app with Android/iOS)
    - packages/shared/: Shared Flutter package for models and API client
    - backend/app/: FastAPI backend directory
    - docker-compose.yaml: Docker compose configuration

    Args:
        project_name: Name of the project to create
        with_flutter: Whether to create a Flutter app using flutter create
        with_backend: Whether to initialize Python backend using uv init
        template: Template to use for schema.schnitzel.yaml (minimal or full)
        force: Overwrite existing directory if it exists
    """
    # Validate template choice
    if template not in ["minimal", "full"]:
        console.print(f"[red]Error: Invalid template '{template}'. Choose 'minimal' or 'full'[/red]")
        raise typer.Exit(code=1)

    # Create project root directory
    project_path = Path.cwd() / project_name

    if project_path.exists():
        if not force:
            console.print(f"[red]Error: Directory '{project_name}' already exists[/red]")
            raise typer.Exit(code=1)
        else:
            # Remove existing path (file or directory) when --force is used
            import shutil
            console.print(f"[yellow]Warning: Removing existing directory '{project_name}'[/yellow]")
            if project_path.is_dir():
                shutil.rmtree(project_path)
            else:
                project_path.unlink()

    try:
        logger.debug(f"Initializing project: {project_name}")
        logger.debug(f"Project options: with_flutter={with_flutter}, with_backend={with_backend}, template={template}, force={force}")
        logger.debug(f"Project path: {project_path.absolute()}")

        if not _is_quiet_mode():
            console.print(f"\n[bold blue]Creating project: {project_name}[/bold blue]")
            if template == "full":
                console.print(f"[dim]Using full template with example models[/dim]")
            console.print()  # Empty line for better formatting

        # Create project directory
        logger.debug(f"Creating project directory: {project_path}")
        project_path.mkdir(parents=True, exist_ok=False)

        # Sanitize project name for Dart package naming rules
        dart_package_name = _sanitize_dart_package_name(project_name)

        # Create apps/{name} directory (Flutter app or placeholder)
        apps_dir = project_path / "apps" / dart_package_name
        logger.debug(f"Apps directory: {apps_dir}")

        # Handle Flutter app creation
        flutter_app_created = False
        if with_flutter:
            # Check if Flutter is installed
            if not _is_flutter_installed():
                console.print("[red]Error: Flutter is required but not installed[/red]")
                console.print("[dim]Install Flutter: https://flutter.dev/docs/get-started/install[/dim]")
                console.print("[dim]Or use --no-flutter to skip Flutter setup[/dim]")
                raise typer.Exit(code=1)

            # Default org - will be read from schema if specified later
            # For init, we use default; user can customize in schema.schnitzel.yaml
            org = "com.example"

            # Create Flutter app (real app, not package) in apps/{name}/
            flutter_app_created = _create_flutter_app(apps_dir, project_name, org=org)
            if not flutter_app_created:
                console.print("[red]Error: flutter create failed[/red]")
                console.print("[dim]Check Flutter installation with: flutter doctor[/dim]")
                raise typer.Exit(code=1)

            if not _is_quiet_mode():
                console.print(f"  [green]✓ Created apps/{dart_package_name}/ (Flutter app)[/green]")

            # Create packages/shared Flutter package for shared models and API client
            shared_dir = project_path / "packages" / "shared"
            flutter_shared_created = _create_flutter_shared(shared_dir, project_name)
            if not flutter_shared_created:
                console.print("[red]Error: flutter create --template=package failed for shared package[/red]")
                console.print("[dim]Check Flutter installation with: flutter doctor[/dim]")
                raise typer.Exit(code=1)

            if not _is_quiet_mode():
                console.print("  [green]✓ Created packages/shared/ (Flutter package)[/green]")

            _create_workspace_pubspec(project_path, project_name)
        else:
            # No Flutter: create empty directory placeholders
            apps_dir.mkdir(parents=True, exist_ok=True)
            shared_dir = project_path / "packages" / "shared"
            shared_dir.mkdir(parents=True, exist_ok=True)
            if not _is_quiet_mode():
                console.print(f"  [green]✓ Created apps/{dart_package_name}/[/green]")
                console.print("  [green]✓ Created packages/shared/[/green]")

        # Create backend/app directory (FastAPI placeholder or actual uv project)
        backend_dir = project_path / "backend" / "app"

        # Handle backend creation
        backend_app_created = False
        if with_backend:
            # Check if uv is installed
            if not _is_uv_installed():
                console.print("[red]Error: uv is required but not installed[/red]")
                console.print("[dim]Install uv: https://github.com/astral-sh/uv[/dim]")
                console.print("[dim]Or use --no-backend to skip backend setup[/dim]")
                raise typer.Exit(code=1)

            # Create parent directory first
            backend_dir.parent.mkdir(parents=True, exist_ok=True)
            # Create backend app using uv init
            backend_app_created = _create_backend_app(backend_dir, project_name)
            if not backend_app_created:
                console.print("[red]Error: uv init failed[/red]")
                console.print("[dim]Check uv installation with: uv --version[/dim]")
                raise typer.Exit(code=1)

            if not _is_quiet_mode():
                console.print("  [green]✓ Created backend/app/ (Python project)[/green]")
        else:
            # No backend: create empty directory placeholder
            backend_dir.mkdir(parents=True, exist_ok=True)
            if not _is_quiet_mode():
                console.print("  [green]✓ Created backend/app/[/green]")

        # Create schema.schnitzel.yaml using selected template
        schema_file = project_path / "schema.schnitzel.yaml"
        schema_content = _get_schema_template(template, project_name)
        schema_file.write_text(schema_content)
        if not _is_quiet_mode():
            console.print("  [green]✓ Created schema.schnitzel.yaml[/green]")

        # Create docker-compose.yaml
        docker_compose_file = project_path / "docker-compose.yaml"
        docker_compose_content = """version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: schnitzel
      POSTGRES_PASSWORD: schnitzel
      POSTGRES_DB: schnitzel
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U schnitzel"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://schnitzel:schnitzel@db:5432/schnitzel
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
"""
        docker_compose_file.write_text(docker_compose_content)
        if not _is_quiet_mode():
            console.print("  [green]✓ Created docker-compose.yaml[/green]")

        # Create project README.md (F111)
        readme_file = project_path / "README.md"
        readme_content = f"""# {project_name}

A Schnitzel project with full-stack code generation for Flutter and FastAPI.

## Getting Started

### Prerequisites

- [Flutter](https://flutter.dev/docs/get-started/install) (for mobile/web development)
- [Python 3.11+](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/get-docker/) (for running PostgreSQL)
- [Schnitzel CLI](https://github.com/your-org/schnitzel)

### Quick Start

1. **Edit your schema**
   ```bash
   # Edit the schema definition
   nano schema.schnitzel.yaml
   ```

2. **Generate code**
   ```bash
   # Generate backend and frontend models
   schnitzel generate
   ```

3. **Start the database**
   ```bash
   # Start PostgreSQL with Docker Compose
   docker-compose up -d db
   ```

4. **Run the backend**
   ```bash
   cd backend/app
   # Install dependencies
   pip install -e .
   # Run migrations (if applicable)
   # alembic upgrade head
   # Start the server
   uvicorn main:app --reload
   ```

5. **Run the Flutter app**
   ```bash
   cd apps/{dart_package_name}
   # Get dependencies
   flutter pub get
   # Run the app
   flutter run
   ```

## Project Structure

```
{project_name}/
├── schema.schnitzel.yaml    # Your data model definitions
├── docker-compose.yaml      # Docker services configuration
├── pubspec.yaml             # Flutter workspace configuration
├── apps/                    # Flutter applications
│   └── {dart_package_name}/ # Main Flutter app (with Android/iOS)
│       └── lib/
│           └── main.dart    # App entry point
├── packages/                # Shared Flutter packages
│   └── shared/              # Shared models and API client
│       └── lib/
│           └── generated/   # Generated Dart models
└── backend/                 # FastAPI backend
    └── app/
        └── generated/       # Generated Python models
```

## Next Steps

- Define your models in `schema.schnitzel.yaml`
- Run `schnitzel generate` to create backend and frontend code
- Customize the generated code as needed
- Build your application logic

## Documentation

- [Schnitzel Documentation](https://github.com/your-org/schnitzel/wiki)
- [Schema Reference](https://github.com/your-org/schnitzel/wiki/Schema-Reference)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)

## License

This project was generated with Schnitzel CLI.
"""
        readme_file.write_text(readme_content)
        if not _is_quiet_mode():
            console.print("  [green]✓ Created README.md[/green]")

        # Create .gitignore
        gitignore_file = project_path / ".gitignore"
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
venv/
.venv/
ENV/
env/
.env

# Dart / Flutter
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
.pub-cache/
.pub/
build/
*.freezed.dart
*.g.dart

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Database
*.db
*.sqlite
*.sqlite3

# Docker
.docker/
docker-compose.override.yaml

# Generated files
backend/app/generated/
packages/shared/lib/generated/
apps/*/lib/generated/

# Logs
*.log
logs/
"""
        gitignore_file.write_text(gitignore_content)
        if not _is_quiet_mode():
            console.print("  [green]✓ Created .gitignore[/green]")

        # Create placeholder README files
        # Only create apps README if Flutter app wasn't created (Flutter creates its own README)
        if not flutter_app_created:
            apps_readme = apps_dir / "README.md"
            apps_readme.write_text("# Flutter App\n\nFlutter application will be generated here.\n")

        # Only create backend README if backend wasn't initialized with uv (uv creates its own files)
        if not backend_app_created:
            backend_readme = backend_dir / "README.md"
            backend_readme.write_text("# FastAPI Backend\n\nFastAPI backend will be generated here.\n")

        if not _is_quiet_mode():
            console.print(f"\n[bold green]✓ Project created successfully![/bold green]")
            console.print(f"\n  [bold]Next steps:[/bold]")
            console.print(f"    1. cd {project_name}")
            console.print(f"    2. Edit schema.schnitzel.yaml")
            console.print(f"    3. Run: schnitzel generate")
        else:
            # In quiet mode, just show OK
            console.print("OK")

    except Exception as e:
        console.print(f"[red]Error creating project:[/red] {e}")
        # Clean up on failure
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)
        raise typer.Exit(code=1)
