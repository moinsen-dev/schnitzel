"""Alembic migration generator for Schnitzel schemas.

Generates database migrations by comparing schema models to the current database state.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict

from schnitzel.schema.models import FieldDefinition, Model, SchnitzelSchema


# SQLAlchemy type mapping for migration generation
SQLALCHEMY_MIGRATION_TYPE_MAP = {
    "string": "sa.String()",
    "str": "sa.String()",
    "text": "sa.Text()",
    "uuid": "sa.UUID()",
    "int": "sa.Integer()",
    "integer": "sa.Integer()",
    "float": "sa.Float()",
    "double": "sa.Float()",
    "bool": "sa.Boolean()",
    "boolean": "sa.Boolean()",
    "datetime": "sa.DateTime()",
    "date": "sa.Date()",
    "json": "sa.JSON()",
    "bytes": "sa.LargeBinary()",
}


class SchemaSnapshot:
    """Represents a snapshot of a schema at a point in time for migration tracking."""

    def __init__(self, schema: SchnitzelSchema):
        """Initialize snapshot from schema.

        Args:
            schema: The schema to snapshot
        """
        self.timestamp = datetime.now().isoformat()
        self.models = self._serialize_models(schema.models)

    def _serialize_models(self, models: Dict[str, Model]) -> Dict[str, Any]:
        """Serialize models to JSON-serializable format.

        Args:
            models: Models to serialize

        Returns:
            Serialized models
        """
        result = {}
        for model_name, model in models.items():
            result[model_name] = {
                "name": model.name,
                "description": model.description,
                "fields": {
                    field_name: field.model_dump()
                    for field_name, field in model.fields.items()
                },
                "relations": (
                    {
                        rel_name: rel.model_dump()
                        for rel_name, rel in model.relations.items()
                    }
                    if model.relations
                    else None
                ),
                "indexes": model.indexes,
            }
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "timestamp": self.timestamp,
            "models": self.models,
        }

    def save(self, path: Path) -> None:
        """Save snapshot to file.

        Args:
            path: Path to save to
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "SchemaSnapshot":
        """Load snapshot from file.

        Args:
            path: Path to load from

        Returns:
            SchemaSnapshot instance
        """
        with open(path, 'r') as f:
            data = json.load(f)

        # Create a dummy schema to reconstruct from
        from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation

        models_dict = {}
        for model_name, model_data in data.get("models", {}).items():
            fields = {
                field_name: FieldDefinition(**field_data)
                for field_name, field_data in model_data.get("fields", {}).items()
            }

            relations = None
            if model_data.get("relations"):
                relations = {
                    rel_name: Relation(**rel_data)
                    for rel_name, rel_data in model_data["relations"].items()
                }

            model = Model(
                name=model_data["name"],
                description=model_data.get("description"),
                fields=fields,
                relations=relations,
                indexes=model_data.get("indexes"),
            )
            models_dict[model_name] = model

        schema = SchnitzelSchema(models=models_dict)
        snapshot = cls(schema)
        snapshot.timestamp = data["timestamp"]
        return snapshot


class SchemaDiff:
    """Represents differences between two schema snapshots."""

    def __init__(self, old: Optional[SchemaSnapshot], new: SchemaSnapshot, rename_hints: Optional[Dict[str, Any]] = None):
        """Calculate differences.

        Args:
            old: Previous snapshot (None for initial)
            new: Current snapshot
            rename_hints: Optional hints for detecting renames, e.g.:
                {
                    "tables": {"OldName": "NewName"},
                    "columns": {"ModelName": {"old_col": "new_col"}}
                }
        """
        self.added_models: Dict[str, Dict[str, Any]] = {}
        self.removed_models: Dict[str, Dict[str, Any]] = {}
        self.added_columns: Dict[str, Dict[str, Any]] = {}
        self.removed_columns: Dict[str, Dict[str, Any]] = {}
        self.changed_columns: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.renamed_tables: Dict[str, str] = {}  # old_name -> new_name
        self.renamed_columns: Dict[str, Dict[str, str]] = {}  # model -> {old_col -> new_col}
        self.nullable_changes: Dict[str, Dict[str, Dict[str, bool]]] = {}  # model -> {col -> {old, new}}
        self.unique_changes: Dict[str, Dict[str, Dict[str, bool]]] = {}  # model -> {col -> {old, new}}
        self.index_changes: Dict[str, Dict[str, Dict[str, bool]]] = {}  # model -> {col -> {old, new}}
        self.default_changes: Dict[str, Dict[str, Dict[str, Any]]] = {}  # model -> {col -> {old, new}}

        rename_hints = rename_hints or {}

        if old is None:
            # Initial migration - all models are new
            self.added_models = new.models
        else:
            # Get rename hints
            table_renames = rename_hints.get("tables", {})
            column_renames = rename_hints.get("columns", {})

            # Find model differences
            old_models = set(old.models.keys())
            new_models = set(new.models.keys())

            # Detect table renames from hints
            for old_name, new_name in table_renames.items():
                if old_name in old_models and new_name in new_models:
                    self.renamed_tables[old_name] = new_name
                    # Remove from added/removed since it's a rename
                    old_models.discard(old_name)
                    new_models.discard(new_name)

            # Added models (excluding renamed)
            for model_name in new_models - old_models:
                if model_name not in self.renamed_tables.values():
                    self.added_models[model_name] = new.models[model_name]

            # Removed models (excluding renamed)
            for model_name in old_models - new_models:
                if model_name not in self.renamed_tables:
                    self.removed_models[model_name] = old.models[model_name]

            # Check for column changes in existing models (and renamed models)
            models_to_check = list(old_models & new_models)
            # Add renamed tables to check (map old to new)
            for old_name, new_name in self.renamed_tables.items():
                models_to_check.append((old_name, new_name))

            for model_item in models_to_check:
                if isinstance(model_item, tuple):
                    old_model_name, new_model_name = model_item
                else:
                    old_model_name = new_model_name = model_item

                old_fields = set(old.models[old_model_name]["fields"].keys())
                new_fields = set(new.models[new_model_name]["fields"].keys())

                # Get column rename hints for this model
                model_col_renames = column_renames.get(new_model_name, {})

                # Detect column renames from hints
                for old_col, new_col in model_col_renames.items():
                    if old_col in old_fields and new_col in new_fields:
                        if new_model_name not in self.renamed_columns:
                            self.renamed_columns[new_model_name] = {}
                        self.renamed_columns[new_model_name][old_col] = new_col
                        old_fields.discard(old_col)
                        new_fields.discard(new_col)

                # Added columns (excluding renamed)
                added = new_fields - old_fields
                renamed_new_cols = set(self.renamed_columns.get(new_model_name, {}).values())
                added = added - renamed_new_cols
                if added:
                    self.added_columns[new_model_name] = {
                        field: new.models[new_model_name]["fields"][field]
                        for field in added
                    }

                # Removed columns (excluding renamed)
                removed = old_fields - new_fields
                renamed_old_cols = set(self.renamed_columns.get(new_model_name, {}).keys())
                removed = removed - renamed_old_cols
                if removed:
                    self.removed_columns[new_model_name] = {
                        field: old.models[old_model_name]["fields"][field]
                        for field in removed
                    }

                # Changed columns (type changes and nullable changes in existing columns)
                common_fields = old_fields & new_fields
                for field_name in common_fields:
                    old_field = old.models[old_model_name]["fields"][field_name]
                    new_field = new.models[new_model_name]["fields"][field_name]

                    # Check if the type has changed
                    if old_field.get("type") != new_field.get("type"):
                        if new_model_name not in self.changed_columns:
                            self.changed_columns[new_model_name] = {}
                        self.changed_columns[new_model_name][field_name] = {
                            "old": old_field,
                            "new": new_field,
                        }

                    # Check if nullable has changed
                    old_nullable = old_field.get("optional", False)
                    new_nullable = new_field.get("optional", False)
                    if old_nullable != new_nullable:
                        if new_model_name not in self.nullable_changes:
                            self.nullable_changes[new_model_name] = {}
                        self.nullable_changes[new_model_name][field_name] = {
                            "old": old_nullable,
                            "new": new_nullable,
                        }

                    # Check if unique constraint has changed
                    old_unique = old_field.get("unique", False)
                    new_unique = new_field.get("unique", False)
                    if old_unique != new_unique:
                        if new_model_name not in self.unique_changes:
                            self.unique_changes[new_model_name] = {}
                        self.unique_changes[new_model_name][field_name] = {
                            "old": old_unique,
                            "new": new_unique,
                        }

                    # Check if index has changed
                    old_index = old_field.get("index", False)
                    new_index = new_field.get("index", False)
                    if old_index != new_index:
                        if new_model_name not in self.index_changes:
                            self.index_changes[new_model_name] = {}
                        self.index_changes[new_model_name][field_name] = {
                            "old": old_index,
                            "new": new_index,
                        }

                    # Check if default value has changed
                    old_default = old_field.get("default")
                    new_default = new_field.get("default")
                    if old_default != new_default:
                        if new_model_name not in self.default_changes:
                            self.default_changes[new_model_name] = {}
                        self.default_changes[new_model_name][field_name] = {
                            "old": old_default,
                            "new": new_default,
                        }

    def is_empty(self) -> bool:
        """Check if there are no changes.

        Returns:
            True if no changes
        """
        return (
            not self.added_models
            and not self.removed_models
            and not self.added_columns
            and not self.removed_columns
            and not self.changed_columns
            and not self.renamed_tables
            and not self.renamed_columns
            and not self.nullable_changes
            and not self.unique_changes
            and not self.index_changes
            and not self.default_changes
        )

    def has_changes(self) -> bool:
        """Check if there are any changes.

        Returns:
            True if there are changes
        """
        return not self.is_empty()


class AlembicMigrationGenerator:
    """Generates Alembic migrations from Schnitzel schemas."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the Alembic migration generator.

        Args:
            project_root: Root directory of the project (for snapshot storage)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.snapshots_dir = self.project_root / ".schnitzel" / "snapshots"

    def get_latest_snapshot(self) -> Optional[SchemaSnapshot]:
        """Get the most recent schema snapshot.

        Returns:
            Latest snapshot or None if no snapshots exist
        """
        if not self.snapshots_dir.exists():
            return None

        snapshots = sorted(self.snapshots_dir.glob("*.json"))
        if not snapshots:
            return None

        return SchemaSnapshot.load(snapshots[-1])

    def save_snapshot(self, schema: SchnitzelSchema, name: str) -> Path:
        """Save a schema snapshot.

        Args:
            schema: Schema to snapshot
            name: Name for the snapshot

        Returns:
            Path to saved snapshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"{timestamp}_{self._sanitize_filename(name)}.json"
        snapshot_path = self.snapshots_dir / snapshot_filename

        snapshot = SchemaSnapshot(schema)
        snapshot.save(snapshot_path)

        return snapshot_path

    def generate_diff_migration(
        self,
        schema: SchnitzelSchema,
        migration_name: str,
        down_revision: str | None = None,
    ) -> str:
        """Generate a migration by comparing current schema with the latest snapshot.

        Args:
            schema: Current schema
            migration_name: Migration name
            down_revision: Previous migration revision

        Returns:
            Generated migration code

        Raises:
            ValueError: If no changes detected
        """
        # Get previous snapshot
        old_snapshot = self.get_latest_snapshot()
        new_snapshot = SchemaSnapshot(schema)

        # Calculate diff
        diff = SchemaDiff(old_snapshot, new_snapshot)

        if diff.is_empty():
            raise ValueError("No schema changes detected")

        # Generate revision ID
        revision_id = self._generate_revision_id(migration_name)
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate upgrade and downgrade operations from diff
        upgrade_ops = self._generate_diff_upgrade_operations(diff)
        downgrade_ops = self._generate_diff_downgrade_operations(diff)

        # Build migration file
        return self._build_migration_file(
            migration_name=migration_name,
            revision_id=revision_id,
            down_revision=down_revision,
            create_date=create_date,
            upgrade_ops=upgrade_ops,
            downgrade_ops=downgrade_ops,
        )

    def generate_initial_migration(
        self,
        schema: SchnitzelSchema,
        migration_name: str,
        down_revision: str | None = None,
    ) -> str:
        """
        Generate an initial Alembic migration from a schema.

        Args:
            schema: The Schnitzel schema to generate migration from
            migration_name: Name/description of the migration
            down_revision: Previous migration revision ID (None for initial)

        Returns:
            Generated migration code as a string
        """
        # Generate revision ID (8-character hash based on timestamp and name)
        revision_id = self._generate_revision_id(migration_name)

        # Build migration metadata
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate upgrade operations (CREATE TABLE statements)
        upgrade_ops = self._generate_upgrade_operations(schema)

        # Generate downgrade operations (DROP TABLE statements in reverse order)
        downgrade_ops = self._generate_downgrade_operations(schema)

        # Build the migration file
        migration_code = self._build_migration_file(
            migration_name=migration_name,
            revision_id=revision_id,
            down_revision=down_revision,
            create_date=create_date,
            upgrade_ops=upgrade_ops,
            downgrade_ops=downgrade_ops,
        )

        return migration_code

    def generate_migration_to_file(
        self,
        schema: SchnitzelSchema,
        migration_name: str,
        migrations_dir: str | Path,
        down_revision: str | None = None,
    ) -> tuple[Path, str]:
        """
        Generate a migration file and write it to disk.

        Args:
            schema: The Schnitzel schema to generate migration from
            migration_name: Name/description of the migration
            migrations_dir: Directory where migrations should be written
            down_revision: Previous migration revision ID (None for initial)

        Returns:
            Tuple of (Path to migration file, revision ID)
        """
        # Generate the migration code
        migration_code = self.generate_initial_migration(
            schema, migration_name, down_revision
        )

        # Extract revision ID from the generated code
        revision_match = re.search(r"revision = ['\"]([^'\"]+)['\"]", migration_code)
        revision_id = revision_match.group(1) if revision_match else "unknown"

        # Convert to Path object
        migrations_path = Path(migrations_dir)

        # Create migrations directory if it doesn't exist
        migrations_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with revision ID and migration name
        # Format: {revision_id}_{sanitized_name}.py
        sanitized_name = self._sanitize_filename(migration_name)
        filename = f"{revision_id}_{sanitized_name}.py"
        migration_file = migrations_path / filename

        # Write the migration file
        migration_file.write_text(migration_code, encoding="utf-8")

        return migration_file, revision_id

    def _generate_revision_id(self, migration_name: str) -> str:
        """Generate a short revision ID based on timestamp and migration name.

        Args:
            migration_name: Name of the migration

        Returns:
            8-character revision ID
        """
        # Combine timestamp and name for uniqueness
        timestamp = datetime.now().isoformat()
        content = f"{timestamp}_{migration_name}"

        # Generate hash and take first 8 characters
        hash_obj = hashlib.sha256(content.encode("utf-8"))
        return hash_obj.hexdigest()[:8]

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize migration name for use in filename.

        Args:
            name: Migration name

        Returns:
            Sanitized filename-safe string
        """
        # Replace spaces with underscores
        sanitized = name.replace(" ", "_")
        # Remove any non-alphanumeric characters except underscores
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", sanitized)
        # Convert to lowercase
        return sanitized.lower()

    def _generate_upgrade_operations(self, schema: SchnitzelSchema) -> list[str]:
        """Generate upgrade operations (CREATE TABLE statements and CREATE INDEX statements).

        Args:
            schema: The schema to generate operations from

        Returns:
            List of operation code strings
        """
        operations = []

        # Sort models to handle dependencies (models with no foreign keys first)
        sorted_models = self._topological_sort_models(schema)

        # First, create all tables
        for model in sorted_models:
            create_table_op = self._generate_create_table(model)
            operations.append(create_table_op)

        # Then, create indexes for fields marked with index: true
        for model in sorted_models:
            index_ops = self._generate_indexes(model)
            operations.extend(index_ops)

        return operations

    def _generate_indexes(self, model: Model) -> list[str]:
        """Generate CREATE INDEX statements for fields marked with index: true.

        Args:
            model: The model to generate indexes for

        Returns:
            List of CREATE INDEX operation strings
        """
        operations = []
        table_name = self._get_table_name(model)

        for field_name, field_def in model.fields.items():
            # Skip primary key fields (they automatically get indexed)
            if field_def.primary:
                continue

            # Only create index if field has index: true
            if field_def.index:
                index_name = f"ix_{table_name}_{field_name}"
                index_op = f"    op.create_index('{index_name}', '{table_name}', ['{field_name}'])"
                operations.append(index_op)

        return operations

    def _generate_drop_indexes(self, model: Model) -> list[str]:
        """Generate DROP INDEX statements for indexes in downgrade.

        Args:
            model: The model to drop indexes for

        Returns:
            List of DROP INDEX operation strings
        """
        operations = []
        table_name = self._get_table_name(model)

        for field_name, field_def in model.fields.items():
            # Skip primary key fields
            if field_def.primary:
                continue

            # Only drop index if field has index: true
            if field_def.index:
                index_name = f"ix_{table_name}_{field_name}"
                drop_index_op = f"    op.drop_index('{index_name}', table_name='{table_name}')"
                operations.append(drop_index_op)

        return operations

    def _generate_downgrade_operations(self, schema: SchnitzelSchema) -> list[str]:
        """Generate downgrade operations (DROP INDEX and DROP TABLE statements).

        Args:
            schema: The schema to generate operations from

        Returns:
            List of operation code strings (in reverse order)
        """
        operations = []

        # Drop tables in reverse order to respect foreign key constraints
        sorted_models = self._topological_sort_models(schema)

        # First, drop indexes (in reverse order)
        for model in reversed(sorted_models):
            drop_index_ops = self._generate_drop_indexes(model)
            operations.extend(drop_index_ops)

        # Then, drop tables
        for model in reversed(sorted_models):
            table_name = self._get_table_name(model)
            drop_op = f"    op.drop_table('{table_name}')"
            operations.append(drop_op)

        return operations

    def _topological_sort_models(self, schema: SchnitzelSchema) -> list[Model]:
        """Sort models in topological order based on relationships.

        Models with no dependencies come first, then models that depend on them.

        Args:
            schema: The schema containing models

        Returns:
            List of models in dependency order
        """
        # For now, simple implementation: models without belongsTo first
        models_without_fk = []
        models_with_fk = []

        for model in schema.models.values():
            has_belongs_to = False
            if model.relations:
                for relation in model.relations.values():
                    if relation.type == "belongsTo":
                        has_belongs_to = True
                        break

            if has_belongs_to:
                models_with_fk.append(model)
            else:
                models_without_fk.append(model)

        return models_without_fk + models_with_fk

    def _generate_create_table(self, model: Model) -> str:
        """Generate CREATE TABLE operation for a model.

        Args:
            model: The model to generate CREATE TABLE for

        Returns:
            CREATE TABLE operation code
        """
        table_name = self._get_table_name(model)
        lines = [f"    op.create_table('{table_name}',"]

        # Generate column definitions
        for field_name, field_def in model.fields.items():
            column_line = self._generate_column_definition(field_name, field_def)
            lines.append(f"        {column_line},")

        # Generate foreign key columns for belongsTo relationships
        if model.relations:
            for relation_name, relation_def in model.relations.items():
                if relation_def.type == "belongsTo":
                    fk_column = self._generate_foreign_key_column(
                        relation_name, relation_def
                    )
                    lines.append(f"        {fk_column},")

        # Add primary key constraint (assuming 'id' field or first primary field)
        primary_fields = [
            fname for fname, fdef in model.fields.items() if fdef.primary
        ]
        if primary_fields:
            pk_line = f"sa.PrimaryKeyConstraint('{primary_fields[0]}')"
            lines.append(f"        {pk_line}")

        lines.append("    )")

        return "\n".join(lines)

    def _generate_column_definition(
        self, field_name: str, field_def: FieldDefinition
    ) -> str:
        """Generate a column definition for migration.

        Args:
            field_name: Name of the field
            field_def: Field definition

        Returns:
            Column definition string
        """
        # Get SQLAlchemy type
        sa_type = self._get_sqlalchemy_migration_type(field_def)

        # Build nullable constraint
        # A field is nullable if it's explicitly optional
        # Otherwise it's not nullable if it's primary, required, has a default, or is auto-generated
        if field_def.optional:
            nullable = True
        elif field_def.primary or field_def.required or field_def.default is not None or field_def.auto:
            nullable = False
        else:
            # Default behavior for fields without explicit constraints
            nullable = True

        return f"sa.Column('{field_name}', {sa_type}, nullable={nullable})"

    def _generate_foreign_key_column(
        self, relation_name: str, relation_def: Any
    ) -> str:
        """Generate a foreign key column definition.

        Args:
            relation_name: Name of the relationship
            relation_def: Relation definition

        Returns:
            Foreign key column definition string
        """
        # Get FK column name
        if relation_def.foreign_key:
            fk_column_name = relation_def.foreign_key
        else:
            fk_column_name = self._to_snake_case(relation_name) + "_id"

        # Get target table name
        target_table = self._pluralize_table_name(relation_def.model)

        return f"sa.Column('{fk_column_name}', sa.UUID(), sa.ForeignKey('{target_table}.id'), nullable=True)"

    def _get_sqlalchemy_migration_type(self, field_def: FieldDefinition) -> str:
        """Get SQLAlchemy type for a field in migration format.

        Args:
            field_def: Field definition

        Returns:
            SQLAlchemy type string for migration
        """
        schema_type_lower = field_def.type.lower()

        # Handle string types with max_length
        if schema_type_lower in ("string", "str") and field_def.max_length:
            return f"sa.String({field_def.max_length})"

        # Standard type mapping
        return SQLALCHEMY_MIGRATION_TYPE_MAP.get(schema_type_lower, "sa.String()")

    def _get_table_name(self, model: Model) -> str:
        """Get the database table name for a model.

        Args:
            model: The model

        Returns:
            Table name (pluralized snake_case)
        """
        return self._pluralize_table_name(model.name)

    def _pluralize_table_name(self, model_name: str) -> str:
        """Convert model name to pluralized snake_case table name.

        Args:
            model_name: PascalCase model name

        Returns:
            Pluralized snake_case table name
        """
        # Convert to snake_case first
        snake = self._to_snake_case(model_name)

        # Simple pluralization rules
        if snake.endswith("y") and len(snake) > 1 and snake[-2] not in "aeiou":
            return snake[:-1] + "ies"
        elif snake.endswith("s") or snake.endswith("x") or snake.endswith("z"):
            return snake + "es"
        else:
            return snake + "s"

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case.

        Args:
            name: PascalCase name

        Returns:
            snake_case name
        """
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _format_default_value_for_sql(self, default_value: Any, field_type: str) -> str:
        """Format a default value for use in SQL statements.

        Args:
            default_value: The default value to format
            field_type: The field type

        Returns:
            SQL-formatted default value string
        """
        field_type_lower = field_type.lower()

        # Handle None/NULL
        if default_value is None:
            return "NULL"

        # Handle boolean values
        if field_type_lower in ("bool", "boolean"):
            return "TRUE" if default_value else "FALSE"

        # Handle numeric values
        if field_type_lower in ("int", "integer", "float", "double"):
            return str(default_value)

        # Handle string values - escape single quotes
        if field_type_lower in ("string", "str", "text"):
            escaped = str(default_value).replace("'", "''")
            return f"'{escaped}'"

        # Handle UUID - treat as string
        if field_type_lower == "uuid":
            return f"'{default_value}'"

        # Handle datetime - use SQL NOW() or specific timestamp
        if field_type_lower in ("datetime", "date"):
            if default_value in ("now", "NOW", "CURRENT_TIMESTAMP"):
                return "CURRENT_TIMESTAMP"
            return f"'{default_value}'"

        # Default: treat as string
        escaped = str(default_value).replace("'", "''")
        return f"'{escaped}'"

    def _format_server_default(self, default_value: Any) -> str:
        """Format a default value for use in server_default parameter.

        Args:
            default_value: The default value to format

        Returns:
            Formatted server_default string for Alembic
        """
        if default_value is None:
            return "None"

        # For booleans
        if isinstance(default_value, bool):
            return f"sa.text('{'TRUE' if default_value else 'FALSE'}')"

        # For numbers
        if isinstance(default_value, (int, float)):
            return f"sa.text('{default_value}')"

        # For strings
        if isinstance(default_value, str):
            # Escape single quotes
            escaped = default_value.replace("'", "''")
            return f"sa.text('{escaped}')"

        # Default case
        return f"sa.text('{str(default_value)}')"

    def generate_data_migration(
        self,
        migration_name: str,
        table_name: str,
        data_operations: list[Dict[str, Any]],
        down_revision: str | None = None,
    ) -> str:
        """Generate a data-only migration (no schema changes).

        Args:
            migration_name: Name/description of the migration
            table_name: Target table name
            data_operations: List of data operations, each with:
                - operation: 'insert' | 'update' | 'delete'
                - values: Dict of column -> value pairs (for insert/update)
                - where: WHERE clause condition (for update/delete)
            down_revision: Previous migration revision ID

        Returns:
            Generated migration code as a string

        Example:
            data_operations = [
                {
                    "operation": "update",
                    "values": {"status": "active"},
                    "where": "status IS NULL"
                },
                {
                    "operation": "insert",
                    "values": {"name": "admin", "role": "superuser"}
                }
            ]
        """
        # Generate revision ID
        revision_id = self._generate_revision_id(migration_name)
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate upgrade and downgrade operations
        upgrade_ops = []
        downgrade_ops = []

        for op_def in data_operations:
            operation = op_def.get("operation", "").lower()

            if operation == "insert":
                # Generate INSERT statement
                values = op_def.get("values", {})
                columns = ", ".join(values.keys())
                value_list = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values.values()])
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({value_list})"
                upgrade_ops.append(f"    op.execute(\"{sql}\")")

                # Downgrade: DELETE the inserted row
                where_clause = " AND ".join([f"{k} = " + (f"'{v}'" if isinstance(v, str) else str(v)) for k, v in values.items()])
                downgrade_sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                downgrade_ops.insert(0, f"    op.execute(\"{downgrade_sql}\")")

            elif operation == "update":
                # Generate UPDATE statement
                values = op_def.get("values", {})
                where = op_def.get("where", "1=1")
                set_clause = ", ".join([f"{k} = " + (f"'{v}'" if isinstance(v, str) else str(v)) for k, v in values.items()])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
                upgrade_ops.append(f"    op.execute(\"{sql}\")")

                # Downgrade: would need original values - for now, add comment
                downgrade_ops.insert(0, f"    # Manual intervention required: restore original values for UPDATE")
                downgrade_ops.insert(1, f"    pass")

            elif operation == "delete":
                # Generate DELETE statement
                where = op_def.get("where", "1=1")
                sql = f"DELETE FROM {table_name} WHERE {where}"
                upgrade_ops.append(f"    op.execute(\"{sql}\")")

                # Downgrade: cannot restore deleted data
                downgrade_ops.insert(0, f"    # Cannot restore deleted data")
                downgrade_ops.insert(1, f"    pass")

        # Build migration file
        return self._build_migration_file(
            migration_name=migration_name,
            revision_id=revision_id,
            down_revision=down_revision,
            create_date=create_date,
            upgrade_ops=upgrade_ops,
            downgrade_ops=downgrade_ops,
        )

    def _generate_indexes(self, model: Model) -> list[str]:
        """Generate CREATE INDEX statements for fields marked with index: true.

        Args:
            model: The model to generate indexes for

        Returns:
            List of CREATE INDEX operation strings
        """
        operations = []
        table_name = self._get_table_name(model)

        for field_name, field_def in model.fields.items():
            # Skip primary key fields (they automatically get indexed)
            if field_def.primary:
                continue

            # Only create index if field has index: true
            if field_def.index:
                index_name = f"ix_{table_name}_{field_name}"
                index_op = f"    op.create_index('{index_name}', '{table_name}', ['{field_name}'])"
                operations.append(index_op)

        return operations

    def _generate_drop_indexes(self, model: Model) -> list[str]:
        """Generate DROP INDEX statements for fields marked with index: true.

        Args:
            model: The model to generate DROP INDEX statements for

        Returns:
            List of DROP INDEX operation strings
        """
        operations = []
        table_name = self._get_table_name(model)

        for field_name, field_def in model.fields.items():
            # Skip primary key fields
            if field_def.primary:
                continue

            # Only drop index if field has index: true
            if field_def.index:
                index_name = f"ix_{table_name}_{field_name}"
                drop_index_op = f"    op.drop_index('{index_name}', table_name='{table_name}')"
                operations.append(drop_index_op)

        return operations

    def _generate_diff_upgrade_operations(self, diff: SchemaDiff) -> list[str]:
        """Generate upgrade operations from a schema diff.

        Args:
            diff: Schema differences

        Returns:
            List of upgrade operation strings
        """
        operations = []

        # Rename tables first (before any other table operations)
        for old_name, new_name in diff.renamed_tables.items():
            old_table = self._pluralize_table_name(old_name)
            new_table = self._pluralize_table_name(new_name)
            operations.append(f"    op.rename_table('{old_table}', '{new_table}')")

        # Create tables for new models
        for model_name, model_data in diff.added_models.items():
            # Reconstruct model for table generation
            from schnitzel.schema.models import Model, FieldDefinition

            fields = {
                field_name: FieldDefinition(**field_data)
                for field_name, field_data in model_data["fields"].items()
            }
            model = Model(name=model_data["name"], fields=fields)

            create_table_op = self._generate_create_table(model)
            operations.append(create_table_op)

        # Rename columns (before add/drop to preserve data)
        for model_name, col_renames in diff.renamed_columns.items():
            table_name = self._pluralize_table_name(model_name)
            for old_col, new_col in col_renames.items():
                operations.append(
                    f"    op.alter_column('{table_name}', '{old_col}', new_column_name='{new_col}')"
                )

        # Add columns to existing tables
        for model_name, fields_data in diff.added_columns.items():
            table_name = self._pluralize_table_name(model_name)

            for field_name, field_data in fields_data.items():
                from schnitzel.schema.models import FieldDefinition
                field_def = FieldDefinition(**field_data)

                col_type = self._get_sqlalchemy_migration_type(field_def)
                nullable = field_def.optional or not (field_def.required or field_def.primary)

                operations.append(
                    f"    op.add_column('{table_name}', "
                    f"sa.Column('{field_name}', {col_type}, nullable={nullable}))"
                )

                # Add data migration to populate default values if field has a default and is not nullable
                if field_def.default is not None and not nullable:
                    default_value = self._format_default_value_for_sql(field_def.default, field_def.type)
                    operations.append(
                        f"    # Data migration: populate default value for new column"
                    )
                    operations.append(
                        f"    op.execute(\"UPDATE {table_name} SET {field_name} = {default_value} WHERE {field_name} IS NULL\")"
                    )

        # Alter column types for changed columns
        for model_name, fields_data in diff.changed_columns.items():
            table_name = self._pluralize_table_name(model_name)

            for field_name, change_data in fields_data.items():
                from schnitzel.schema.models import FieldDefinition
                old_field_def = FieldDefinition(**change_data["old"])
                new_field_def = FieldDefinition(**change_data["new"])

                new_col_type = self._get_sqlalchemy_migration_type(new_field_def)
                nullable = new_field_def.optional or not (new_field_def.required or new_field_def.primary)

                # Add comment about potential data transformation need
                operations.append(
                    f"    # Type change: {old_field_def.type} -> {new_field_def.type}"
                )
                operations.append(
                    f"    # WARNING: You may need to add data transformation logic here"
                )
                operations.append(
                    f"    op.alter_column('{table_name}', '{field_name}', "
                    f"type_={new_col_type}, nullable={nullable})"
                )

        # Handle nullable changes (separate from type changes)
        for model_name, fields_data in diff.nullable_changes.items():
            # Skip if already handled in changed_columns
            if model_name in diff.changed_columns:
                existing_changed = diff.changed_columns[model_name]
                fields_data = {k: v for k, v in fields_data.items() if k not in existing_changed}

            if fields_data:
                table_name = self._pluralize_table_name(model_name)
                for field_name, nullable_info in fields_data.items():
                    new_nullable = nullable_info["new"]
                    operations.append(
                        f"    op.alter_column('{table_name}', '{field_name}', nullable={new_nullable})"
                    )

        # Handle default value changes
        for model_name, fields_data in diff.default_changes.items():
            table_name = self._pluralize_table_name(model_name)
            for field_name, default_info in fields_data.items():
                new_default = default_info["new"]
                # Format server_default value
                if new_default is None:
                    operations.append(
                        f"    op.alter_column('{table_name}', '{field_name}', server_default=None)"
                    )
                else:
                    # Convert Python value to SQL server_default format
                    server_default = self._format_server_default(new_default)
                    operations.append(
                        f"    op.alter_column('{table_name}', '{field_name}', server_default={server_default})"
                    )

        # Drop columns from existing tables
        for model_name, fields_data in diff.removed_columns.items():
            table_name = self._pluralize_table_name(model_name)

            for field_name in fields_data.keys():
                operations.append(
                    f"    op.drop_column('{table_name}', '{field_name}')"
                )

        # Drop tables for removed models
        for model_name in diff.removed_models.keys():
            table_name = self._pluralize_table_name(model_name)
            operations.append(f"    op.drop_table('{table_name}')")

        return operations

    def _generate_diff_downgrade_operations(self, diff: SchemaDiff) -> list[str]:
        """Generate downgrade operations from a schema diff (reverse of upgrade).

        Args:
            diff: Schema differences

        Returns:
            List of downgrade operation strings
        """
        operations = []

        # Recreate removed tables
        for model_name, model_data in diff.removed_models.items():
            from schnitzel.schema.models import Model, FieldDefinition

            fields = {
                field_name: FieldDefinition(**field_data)
                for field_name, field_data in model_data["fields"].items()
            }
            model = Model(name=model_data["name"], fields=fields)

            create_table_op = self._generate_create_table(model)
            operations.append(create_table_op)

        # Add back removed columns
        for model_name, fields_data in diff.removed_columns.items():
            table_name = self._pluralize_table_name(model_name)

            for field_name, field_data in fields_data.items():
                from schnitzel.schema.models import FieldDefinition
                field_def = FieldDefinition(**field_data)

                col_type = self._get_sqlalchemy_migration_type(field_def)
                nullable = field_def.optional or not (field_def.required or field_def.primary)

                operations.append(
                    f"    op.add_column('{table_name}', "
                    f"sa.Column('{field_name}', {col_type}, nullable={nullable}))"
                )

        # Revert nullable changes (before type changes)
        for model_name, fields_data in diff.nullable_changes.items():
            # Skip if already handled in changed_columns
            if model_name in diff.changed_columns:
                existing_changed = diff.changed_columns[model_name]
                fields_data = {k: v for k, v in fields_data.items() if k not in existing_changed}

            if fields_data:
                table_name = self._pluralize_table_name(model_name)
                for field_name, nullable_info in fields_data.items():
                    old_nullable = nullable_info["old"]
                    operations.append(
                        f"    op.alter_column('{table_name}', '{field_name}', nullable={old_nullable})"
                    )

        # Revert default value changes
        for model_name, fields_data in diff.default_changes.items():
            table_name = self._pluralize_table_name(model_name)
            for field_name, default_info in fields_data.items():
                old_default = default_info["old"]
                # Format server_default value
                if old_default is None:
                    operations.append(
                        f"    op.alter_column('{table_name}', '{field_name}', server_default=None)"
                    )
                else:
                    # Convert Python value to SQL server_default format
                    server_default = self._format_server_default(old_default)
                    operations.append(
                        f"    op.alter_column('{table_name}', '{field_name}', server_default={server_default})"
                    )

        # Revert column type changes for changed columns
        for model_name, fields_data in diff.changed_columns.items():
            table_name = self._pluralize_table_name(model_name)

            for field_name, change_data in fields_data.items():
                from schnitzel.schema.models import FieldDefinition
                old_field_def = FieldDefinition(**change_data["old"])

                old_col_type = self._get_sqlalchemy_migration_type(old_field_def)
                nullable = old_field_def.optional or not (old_field_def.required or old_field_def.primary)

                operations.append(
                    f"    op.alter_column('{table_name}', '{field_name}', "
                    f"type_={old_col_type}, nullable={nullable})"
                )

        # Revert column renames (reverse: new -> old)
        for model_name, col_renames in diff.renamed_columns.items():
            table_name = self._pluralize_table_name(model_name)
            for old_col, new_col in col_renames.items():
                operations.append(
                    f"    op.alter_column('{table_name}', '{new_col}', new_column_name='{old_col}')"
                )

        # Drop added columns
        for model_name, fields_data in diff.added_columns.items():
            table_name = self._pluralize_table_name(model_name)

            for field_name in fields_data.keys():
                operations.append(
                    f"    op.drop_column('{table_name}', '{field_name}')"
                )

        # Drop added tables
        for model_name in diff.added_models.keys():
            table_name = self._pluralize_table_name(model_name)
            operations.append(f"    op.drop_table('{table_name}')")

        # Revert table renames (reverse: new -> old) - do this last
        for old_name, new_name in diff.renamed_tables.items():
            old_table = self._pluralize_table_name(old_name)
            new_table = self._pluralize_table_name(new_name)
            operations.append(f"    op.rename_table('{new_table}', '{old_table}')")

        return operations

    def _build_migration_file(
        self,
        migration_name: str,
        revision_id: str,
        down_revision: str | None,
        create_date: str,
        upgrade_ops: list[str],
        downgrade_ops: list[str],
    ) -> str:
        """Build the complete migration file content.

        Args:
            migration_name: Migration name/description
            revision_id: Unique revision ID
            down_revision: Previous revision (None for initial)
            create_date: Creation timestamp
            upgrade_ops: List of upgrade operation strings
            downgrade_ops: List of downgrade operation strings

        Returns:
            Complete migration file content
        """
        # Format down_revision
        down_revision_str = f"'{down_revision}'" if down_revision else "None"

        # Build the migration file
        lines = [
            f'"""{migration_name}',
            "",
            f"Revision ID: {revision_id}",
            f"Revises: {down_revision or ''}",
            f"Create Date: {create_date}",
            "",
            '"""',
            "from alembic import op",
            "import sqlalchemy as sa",
            "",
            f"revision = '{revision_id}'",
            f"down_revision = {down_revision_str}",
            "branch_labels = None",
            "depends_on = None",
            "",
            "",
            "def upgrade() -> None:",
        ]

        # Add upgrade operations
        if upgrade_ops:
            lines.extend(upgrade_ops)
        else:
            lines.append("    pass")

        lines.extend(["", "", "def downgrade() -> None:"])

        # Add downgrade operations
        if downgrade_ops:
            lines.extend(downgrade_ops)
        else:
            lines.append("    pass")

        # Add final newline
        lines.append("")

        return "\n".join(lines)


class MigrationConflict:
    """Represents a conflict between migrations."""

    def __init__(self, conflict_type: str, description: str, migrations: list[str]):
        """Initialize migration conflict.

        Args:
            conflict_type: Type of conflict (e.g., 'duplicate_revision', 'branching')
            description: Human-readable description
            migrations: List of migration files involved
        """
        self.conflict_type = conflict_type
        self.description = description
        self.migrations = migrations

    def __repr__(self) -> str:
        return f"MigrationConflict({self.conflict_type}: {self.description})"


class MigrationValidator:
    """Validates migrations for conflicts and SQL syntax issues."""

    def __init__(self, migrations_dir: Path | str):
        """Initialize validator.

        Args:
            migrations_dir: Directory containing migration files
        """
        self.migrations_dir = Path(migrations_dir)

    def detect_conflicts(self) -> list[MigrationConflict]:
        """Detect conflicts between migrations.

        Returns:
            List of detected conflicts
        """
        conflicts = []

        if not self.migrations_dir.exists():
            return conflicts

        migrations = list(self.migrations_dir.glob("*.py"))
        if not migrations:
            return conflicts

        # Parse revision info from each migration
        revision_map: Dict[str, list[Path]] = {}  # revision -> files
        down_revision_map: Dict[str, list[Path]] = {}  # down_revision -> files

        for migration_file in migrations:
            revision, down_revision = self._parse_migration_revisions(migration_file)

            if revision:
                if revision not in revision_map:
                    revision_map[revision] = []
                revision_map[revision].append(migration_file)

            if down_revision:
                if down_revision not in down_revision_map:
                    down_revision_map[down_revision] = []
                down_revision_map[down_revision].append(migration_file)

        # Check for duplicate revisions
        for revision, files in revision_map.items():
            if len(files) > 1:
                conflicts.append(MigrationConflict(
                    conflict_type="duplicate_revision",
                    description=f"Multiple migrations have revision '{revision}'",
                    migrations=[str(f) for f in files]
                ))

        # Check for branching (multiple migrations with same down_revision)
        for down_rev, files in down_revision_map.items():
            if len(files) > 1 and down_rev != "None":
                conflicts.append(MigrationConflict(
                    conflict_type="branching",
                    description=f"Multiple migrations branch from revision '{down_rev}'",
                    migrations=[str(f) for f in files]
                ))

        # Check for missing dependencies
        all_revisions = set(revision_map.keys())
        for down_rev, files in down_revision_map.items():
            if down_rev and down_rev != "None" and down_rev not in all_revisions:
                conflicts.append(MigrationConflict(
                    conflict_type="missing_dependency",
                    description=f"Migration depends on missing revision '{down_rev}'",
                    migrations=[str(f) for f in files]
                ))

        return conflicts

    def validate_sql_syntax(self, migration_code: str) -> list[str]:
        """Validate SQL syntax in migration operations.

        Args:
            migration_code: Migration file content

        Returns:
            List of syntax errors found
        """
        errors = []

        # Check for common SQL syntax issues in Alembic operations
        lines = migration_code.split('\n')

        # Check parentheses balance across entire code (multi-line ops are valid)
        total_open = migration_code.count('(')
        total_close = migration_code.count(')')
        if total_open != total_close:
            errors.append(f"Unbalanced parentheses in migration: {total_open} open, {total_close} close")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for missing quotes around table/column names
            if 'create_table(' in stripped or 'drop_table(' in stripped:
                if "''" in stripped or '""' in stripped:
                    errors.append(f"Line {i}: Empty table name detected")

            # Check for invalid nullable values (only on lines that have complete nullable=X)
            if 'nullable=' in stripped:
                nullable_match = re.search(r'nullable=(\w+)', stripped)
                if nullable_match:
                    nullable_val = nullable_match.group(1)
                    if nullable_val not in ('True', 'False'):
                        errors.append(f"Line {i}: Invalid nullable value '{nullable_val}'")

        # Validate Python syntax of the migration
        try:
            compile(migration_code, '<migration>', 'exec')
        except SyntaxError as e:
            errors.append(f"Python syntax error: {e.msg} at line {e.lineno}")

        return errors

    def validate_migration_file(self, migration_file: Path) -> tuple[bool, list[str]]:
        """Validate a migration file for syntax and structural issues.

        Args:
            migration_file: Path to migration file

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        if not migration_file.exists():
            return False, ["Migration file does not exist"]

        content = migration_file.read_text()

        # Check required elements
        if 'revision = ' not in content:
            errors.append("Missing 'revision' variable")

        if 'down_revision = ' not in content:
            errors.append("Missing 'down_revision' variable")

        if 'def upgrade()' not in content:
            errors.append("Missing 'upgrade()' function")

        if 'def downgrade()' not in content:
            errors.append("Missing 'downgrade()' function")

        # Validate SQL syntax
        sql_errors = self.validate_sql_syntax(content)
        errors.extend(sql_errors)

        return len(errors) == 0, errors

    def _parse_migration_revisions(self, migration_file: Path) -> tuple[str | None, str | None]:
        """Parse revision and down_revision from a migration file.

        Args:
            migration_file: Path to migration file

        Returns:
            Tuple of (revision, down_revision)
        """
        content = migration_file.read_text()

        revision = None
        down_revision = None

        # Match revision = 'xxx' or revision = "xxx"
        revision_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
        if revision_match:
            revision = revision_match.group(1)

        # Match down_revision = 'xxx' or down_revision = "xxx" or down_revision = None
        down_revision_match = re.search(r"down_revision\s*=\s*(?:None|['\"]([^'\"]*)['\"])", content)
        if down_revision_match:
            # Group 1 will be None if it matched "None", otherwise it's the revision string
            down_revision = down_revision_match.group(1)
            # Empty string means it was '' or "", treat as None
            if down_revision == "":
                down_revision = None

        return revision, down_revision
