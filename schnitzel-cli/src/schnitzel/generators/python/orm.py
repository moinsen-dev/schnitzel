"""Python SQLAlchemy ORM generator for Schnitzel schemas.

Generates SQLAlchemy 2.0 ORM models with modern type hints and declarative mapping.
"""

from datetime import datetime
from pathlib import Path
from typing import Set
from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, Model, FieldDefinition, Relation


# SQLAlchemy type mapping for schema types
SQLALCHEMY_TYPE_MAP = {
    "string": "sa.String",
    "str": "sa.String",
    "text": "sa.Text",
    "uuid": "sa.UUID",
    "int": "sa.Integer",
    "integer": "sa.Integer",
    "float": "sa.Float",
    "double": "sa.Float",
    "bool": "sa.Boolean",
    "boolean": "sa.Boolean",
    "datetime": "sa.DateTime",
    "date": "sa.Date",
    "json": "sa.JSON",
    "bytes": "sa.LargeBinary",
}

# Python type hints for ORM models
PYTHON_TYPE_HINTS = {
    "string": "str",
    "str": "str",
    "text": "str",
    "uuid": "uuid.UUID",
    "int": "int",
    "integer": "int",
    "float": "float",
    "double": "float",
    "bool": "bool",
    "boolean": "bool",
    "datetime": "datetime",
    "date": "datetime",
    "json": "dict[str, Any]",
    "bytes": "bytes",
}


class SQLAlchemyORMGenerator:
    """Generates SQLAlchemy 2.0 ORM models from Schnitzel schemas."""

    def __init__(self):
        """Initialize the SQLAlchemy ORM generator."""
        self.imports: Set[str] = set()
        self.needs_uuid = False
        self.needs_datetime = False
        self.needs_any = False
        self.needs_relationship = False
        self.needs_func = False
        self.needs_enum = False
        self.enum_definitions: dict[str, list[str]] = {}  # Maps enum name to values
        self.schema: SchnitzelSchema | None = None  # Current schema being generated

    def generate(self, schema: SchnitzelSchema) -> str:
        """
        Generate SQLAlchemy ORM models from a schema.

        Args:
            schema: The Schnitzel schema to generate ORM models from

        Returns:
            Generated Python code as a string
        """
        self.imports = set()
        self.needs_uuid = False
        self.needs_datetime = False
        self.needs_any = False
        self.needs_relationship = False
        self.needs_func = False
        self.needs_enum = False
        self.needs_table = False  # For association tables
        self.enum_definitions = {}
        self.association_tables: dict[str, tuple[str, str]] = {}  # table_name -> (model1, model2)
        self.schema = schema  # Store schema for relationship resolution

        # Collect type information from all models
        self._collect_type_imports(schema)

        # Collect association tables from manyToMany relationships
        self._collect_association_tables(schema)

        # Build imports
        imports_code = self._build_imports()

        # Build base declaration
        base_code = self._build_base_declaration()

        # Generate association tables
        association_tables_code = ""
        if self.association_tables:
            association_code_sections = []
            for table_name, (model1, model2) in sorted(self.association_tables.items()):
                table_code = self._generate_association_table(table_name, model1, model2)
                association_code_sections.append(table_code)
            association_tables_code = "\n\n".join(association_code_sections)

        # Generate enum classes
        enum_code_sections = []
        if self.enum_definitions:
            for enum_name, enum_values in sorted(self.enum_definitions.items()):
                enum_code = self._generate_enum_class(enum_name, enum_values)
                enum_code_sections.append(enum_code)

        # Generate model classes
        model_code_sections = []
        for model_name, model in schema.models.items():
            model_code = self._generate_model(model)
            model_code_sections.append(model_code)

        # Combine all parts
        enums_code = "\n\n".join(enum_code_sections) if enum_code_sections else ""
        models_code = "\n\n".join(model_code_sections)

        # Build final output
        parts = [imports_code, base_code]
        if association_tables_code:
            parts.append(association_tables_code)
        if enums_code:
            parts.append(enums_code)
        parts.append(models_code)

        return "\n\n".join(parts) + "\n"

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """
        Generate SQLAlchemy ORM models and write them to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the models to 'orm.py' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate ORM models from
            output_dir: Directory where orm.py should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to orm.py file, size in bytes)

        Example:
            >>> generator = SQLAlchemyORMGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "backend/app/generated")
            >>> print(f"ORM models written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the ORM code
        orm_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""# Generated by Schnitzel Framework v{__version__}
# DO NOT EDIT - This file is auto-generated
# Generated at: {timestamp}
# Source: {schema_source}

"""

        # Combine header with generated code
        full_code = header + orm_code

        # Calculate file path and size
        orm_file = output_path / "orm.py"
        file_size = len(full_code.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return orm_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Warn if file already exists
        if orm_file.exists():
            print(f"Warning: Overwriting existing file: {orm_file}")

        orm_file.write_text(full_code, encoding="utf-8")

        return orm_file, file_size

    def _generate_enum_class(self, enum_name: str, enum_values: list[str]) -> str:
        """Generate a Python Enum class.

        Args:
            enum_name: Name of the enum class
            enum_values: List of enum values

        Returns:
            Generated enum class code as string
        """
        lines = [f"class {enum_name}(str, enum.Enum):"]
        lines.append(f'    """Generated enum for {enum_name}."""')
        lines.append("")

        for value in enum_values:
            # Convert value to uppercase for enum member name
            # e.g., "pending" -> "PENDING", "active_user" -> "ACTIVE_USER"
            member_name = value.upper().replace("-", "_").replace(" ", "_")
            lines.append(f'    {member_name} = "{value}"')

        return "\n".join(lines)

    def _generate_model(self, model: Model) -> str:
        """Generate a single SQLAlchemy ORM model class.

        Args:
            model: Model definition from schema

        Returns:
            Generated class code as string
        """
        lines = [f"class {model.name}(Base):"]

        # Add docstring if description exists (MUST be immediately after class definition)
        if model.description:
            lines.append(f'    """{model.description}"""')
            lines.append("")

        # Add table name (pluralized snake_case)
        lines.append(f'    __tablename__ = "{self._pluralize_table_name(model.name)}"')
        lines.append("")

        # Detect composite primary keys
        primary_key_fields = []
        if model.fields:
            for field_name, field_def in model.fields.items():
                if field_def.primary:
                    primary_key_fields.append(field_name)

        is_composite_pk = len(primary_key_fields) > 1

        # Collect check constraints from fields
        check_constraints = []
        if model.fields:
            for field_name, field_def in model.fields.items():
                constraints = self._generate_check_constraints(field_name, field_def)
                check_constraints.extend(constraints)

        # Add __table_args__ for composite primary keys and/or check constraints
        if is_composite_pk or check_constraints:
            lines.append(f"    __table_args__ = (")
            if is_composite_pk:
                pk_fields_str = ", ".join([f'"{field}"' for field in primary_key_fields])
                lines.append(f"        sa.PrimaryKeyConstraint({pk_fields_str}),")
            for constraint in check_constraints:
                lines.append(f"        {constraint},")
            lines.append(f"    )")
            lines.append("")

        # Collect foreign key field names and their target models
        fk_field_info: dict[str, str] = {}  # Maps FK field name to target model name
        if model.relations:
            for relation_name, relation_def in model.relations.items():
                if relation_def.type == "belongsTo":
                    # Get the FK column name for this relationship
                    fk_column_name = (
                        relation_def.foreign_key
                        if relation_def.foreign_key
                        else self._to_snake_case(relation_name) + "_id"
                    )
                    # Check if this field already exists in the schema
                    if model.fields and fk_column_name in model.fields:
                        fk_field_info[fk_column_name] = relation_def.model

        # Generate field columns with proper ordering
        if model.fields:
            lines.append("    # Fields")
            ordered_fields = self._order_fields(model.fields)
            for field_name, field_def in ordered_fields:
                # Check if this field is a foreign key and get target model
                fk_target_model = fk_field_info.get(field_name)
                field_line = self._generate_field_column(
                    field_name, field_def, model.name, is_composite_pk, fk_target_model
                )
                lines.append(f"    {field_line}")

        # Generate foreign key columns for belongsTo relationships
        # Only if they don't already exist in the schema
        has_generated_fks = False
        if model.relations:
            for relation_name, relation_def in model.relations.items():
                if relation_def.type == "belongsTo":
                    fk_column_name = (
                        relation_def.foreign_key
                        if relation_def.foreign_key
                        else self._to_snake_case(relation_name) + "_id"
                    )
                    # Only generate if the field doesn't exist in schema
                    if fk_column_name not in fk_field_info:
                        if not has_generated_fks:
                            lines.append("")
                            lines.append("    # Foreign Keys")
                            has_generated_fks = True
                        fk_line = self._generate_foreign_key_column(relation_name, relation_def)
                        lines.append(f"    {fk_line}")

        # Generate relationship fields
        if model.relations:
            lines.append("")
            lines.append("    # Relationships")
            for relation_name, relation_def in model.relations.items():
                relation_line = self._generate_relationship(relation_name, relation_def, model.name)
                if relation_line:
                    lines.append(f"    {relation_line}")

        return "\n".join(lines)

    def _order_fields(self, fields: dict[str, FieldDefinition]) -> list[tuple[str, FieldDefinition]]:
        """Order fields according to best practices.

        Field ordering:
        1. Primary key fields first
        2. Required (non-optional) fields
        3. Optional fields
        4. Timestamp fields (created_at, updated_at) last

        Within each group, fields are alphabetically ordered.

        Args:
            fields: Dictionary of field name to field definition

        Returns:
            List of (field_name, field_def) tuples in proper order
        """
        timestamp_fields = {"created_at", "updated_at", "deleted_at"}

        # Categorize fields
        primary_keys = []
        required_fields = []
        optional_fields = []
        timestamps = []

        for field_name, field_def in fields.items():
            if field_def.primary:
                primary_keys.append((field_name, field_def))
            elif field_name in timestamp_fields:
                timestamps.append((field_name, field_def))
            elif field_def.optional:
                optional_fields.append((field_name, field_def))
            else:
                required_fields.append((field_name, field_def))

        # Sort each group alphabetically
        primary_keys.sort(key=lambda x: x[0])
        required_fields.sort(key=lambda x: x[0])
        optional_fields.sort(key=lambda x: x[0])
        timestamps.sort(key=lambda x: x[0])

        # Combine in order: PK -> required -> optional -> timestamps
        return primary_keys + required_fields + optional_fields + timestamps

    def _generate_field_column(self, field_name: str, field_def: FieldDefinition, model_name: str = "", is_composite_pk: bool = False, fk_target_model: str | None = None) -> str:
        """Generate a SQLAlchemy column definition with type hints.

        Args:
            field_name: Name of the field
            field_def: Field definition from schema
            model_name: Name of the model (for enum naming)
            is_composite_pk: Whether this model has a composite primary key
            fk_target_model: Target model name if this field is a foreign key

        Returns:
            Column definition string with type hints
        """
        # Get SQLAlchemy column type
        sa_type = self._get_sqlalchemy_type(field_def, field_name, model_name)

        # Get Python type hint
        python_type = self._get_python_type_hint(field_def, field_name, model_name)

        # Handle optional types
        if field_def.optional:
            python_type = f"{python_type} | None"

        # Build column arguments
        column_args = [sa_type]

        # Add ForeignKey constraint if this is a foreign key field
        if fk_target_model:
            target_table = self._pluralize_table_name(fk_target_model)
            column_args.append(f'sa.ForeignKey("{target_table}.id")')

        # Add primary key constraint (only for single primary keys)
        # For composite primary keys, PrimaryKeyConstraint is used in __table_args__
        if field_def.primary and not is_composite_pk:
            column_args.append("primary_key=True")

        # Add unique constraint
        if field_def.unique:
            column_args.append("unique=True")

        # Add index
        if field_def.index:
            column_args.append("index=True")

        # Add nullable constraint (opposite of required, but respect optional)
        if field_def.optional:
            column_args.append("nullable=True")
        elif field_def.required or field_def.primary:
            column_args.append("nullable=False")

        # Add default value
        if field_def.default is not None:
            # For enum types, use the enum class member
            if field_def.type.lower() == "enum" and field_def.values:
                enum_class_name = self._get_enum_class_name(field_name, model_name)
                default_value = str(field_def.default).upper().replace("-", "_").replace(" ", "_")
                column_args.append(f"default={enum_class_name}.{default_value}")
            else:
                column_args.append(f"default={self._format_default(field_def.default)}")

        # Add server defaults for auto fields
        if field_def.auto == "create":
            column_args.append("server_default=func.now()")
        elif field_def.auto == "update":
            column_args.append("onupdate=func.now()")

        # Add comment parameter if description exists
        if field_def.description:
            # Escape quotes in the description
            escaped_description = field_def.description.replace('\\', '\\\\').replace('"', '\\"')
            column_args.append(f'comment="{escaped_description}"')

        column_args_str = ", ".join(column_args)

        # Return mapped column with type hint
        return f"{field_name}: Mapped[{python_type}] = mapped_column({column_args_str})"

    def _generate_foreign_key_column(self, relation_name: str, relation_def: Relation) -> str:
        """Generate a foreign key column for a belongsTo relationship.

        Args:
            relation_name: Name of the relationship field
            relation_def: Relation definition from schema

        Returns:
            Foreign key column definition string
        """
        # Get the foreign key column name
        if relation_def.foreign_key:
            fk_column_name = relation_def.foreign_key
        else:
            # Default: relationName -> relation_name_id
            fk_column_name = self._to_snake_case(relation_name) + "_id"

        # Get the target table name (pluralized)
        target_table = self._pluralize_table_name(relation_def.model)

        # Infer the FK type from the target model's primary key
        # Default to UUID if we can't find the target model
        fk_sa_type = "sa.UUID"
        fk_python_type = "uuid.UUID"

        if self.schema and relation_def.model in self.schema.models:
            target_model = self.schema.models[relation_def.model]
            # Find the primary key field in the target model
            if target_model.fields:
                for field_name, field_def in target_model.fields.items():
                    if field_def.primary:
                        # Use the same type as the target's primary key
                        fk_sa_type = self._get_sqlalchemy_type(field_def, field_name, target_model.name)
                        fk_python_type = self._get_python_type_hint(field_def, field_name, target_model.name)
                        break

        # Generate the FK column with inferred type
        return f'{fk_column_name}: Mapped[{fk_python_type} | None] = mapped_column({fk_sa_type}, sa.ForeignKey("{target_table}.id"), nullable=True)'

    def _pluralize_table_name(self, model_name: str) -> str:
        """Convert model name to pluralized snake_case table name.

        Args:
            model_name: PascalCase model name (e.g., "User", "Post")

        Returns:
            Pluralized snake_case table name (e.g., "users", "posts")

        Examples:
            User -> users
            Post -> posts
            Category -> categories
            Address -> addresses
        """
        # Convert to snake_case first
        snake = self._to_snake_case(model_name)

        # Simple pluralization rules
        if snake.endswith("y") and len(snake) > 1 and snake[-2] not in "aeiou":
            # Category -> categories
            return snake[:-1] + "ies"
        elif snake.endswith("z"):
            # Quiz -> quizzes (double z before adding es)
            return snake + "zes"
        elif snake.endswith("s") or snake.endswith("x"):
            # Address -> addresses, Box -> boxes
            return snake + "es"
        else:
            # User -> users, Post -> posts
            return snake + "s"

    def _generate_relationship(self, relation_name: str, relation_def: Relation, current_model_name: str) -> str:
        """Generate a SQLAlchemy relationship definition.

        Args:
            relation_name: Name of the relationship field
            relation_def: Relation definition from schema
            current_model_name: Name of the current model (for back_populates)

        Returns:
            Relationship definition string or empty string if not supported
        """
        self.needs_relationship = True

        # Check if this is a self-referential relationship
        is_self_referential = (relation_def.model == current_model_name)

        # Determine the back_populates name
        back_populates = self._get_back_populates_name(
            current_model_name,
            relation_name,
            relation_def.type,
            relation_def.model
        )

        if relation_def.type == "belongsTo":
            # Many-to-one relationship (this model belongs to another)
            # For self-referential relationships, need to add remote_side parameter
            if is_self_referential:
                # For self-referential relationships, remote_side must reference the actual column
                # Use bracket notation without quotes to reference the id column of the current class
                return f'{relation_name}: Mapped["{relation_def.model} | None"] = relationship(back_populates="{back_populates}", remote_side=[id])'
            else:
                # Quote the entire union type for forward references
                return f'{relation_name}: Mapped["{relation_def.model} | None"] = relationship(back_populates="{back_populates}")'

        elif relation_def.type == "hasMany":
            # One-to-many relationship (this model has many of another)
            return f'{relation_name}: Mapped[list["{relation_def.model}"]] = relationship(back_populates="{back_populates}")'

        elif relation_def.type == "hasOne":
            # One-to-one relationship
            # Quote the entire union type for forward references
            return f'{relation_name}: Mapped["{relation_def.model} | None"] = relationship(back_populates="{back_populates}", uselist=False)'

        elif relation_def.type == "manyToMany":
            # Many-to-many relationship using association table
            association_table = self._get_association_table_name(
                current_model_name,
                relation_def.model,
                relation_def.through
            )
            return f'{relation_name}: Mapped[list["{relation_def.model}"]] = relationship(secondary={association_table}, back_populates="{back_populates}")'

        return ""

    def _get_back_populates_name(
        self,
        current_model: str,
        relation_name: str,
        relation_type: str,
        target_model: str
    ) -> str:
        """Determine the back_populates name for a relationship.

        For bidirectional relationships, we need to find the matching relationship
        on the other side. By convention:
        - belongsTo (many-to-one): back reference is typically plural (posts)
        - hasMany (one-to-many): back reference is typically singular (user)
        - hasOne (one-to-one): back reference is typically singular (profile)

        For self-referential relationships, we need to find the actual relationship
        name on the other side of the relationship.

        Args:
            current_model: Name of the current model
            relation_name: Name of the current relationship field
            relation_type: Type of relation (belongsTo, hasMany, hasOne)
            target_model: Name of the target model

        Returns:
            Name to use for back_populates
        """
        # Check if this is a self-referential relationship
        is_self_referential = (current_model == target_model)

        if is_self_referential and self.schema:
            # For self-referential relationships, find the matching relationship
            # on the same model that points back to this one
            model = self.schema.models.get(current_model)
            if model and model.relations:
                # Find the complementary relationship
                for other_rel_name, other_rel_def in model.relations.items():
                    if other_rel_name == relation_name:
                        continue  # Skip the current relationship

                    # Check if this is the reverse relationship
                    if other_rel_def.model == target_model:
                        # For belongsTo, look for hasMany/hasOne
                        # For hasMany, look for belongsTo
                        if relation_type == "belongsTo" and other_rel_def.type in ("hasMany", "hasOne"):
                            return other_rel_name
                        elif relation_type == "hasMany" and other_rel_def.type == "belongsTo":
                            return other_rel_name
                        elif relation_type == "hasOne" and other_rel_def.type == "belongsTo":
                            return other_rel_name

        # For manyToMany, look for the matching relationship on the target model
        if relation_type == "manyToMany" and self.schema:
            target_model_obj = self.schema.models.get(target_model)
            if target_model_obj and target_model_obj.relations:
                for other_rel_name, other_rel_def in target_model_obj.relations.items():
                    if other_rel_def.type == "manyToMany" and other_rel_def.model == current_model:
                        return other_rel_name

        # For non-self-referential relationships, use the conventional naming
        # Convert model name to lowercase
        model_lower = current_model[0].lower() + current_model[1:]

        if relation_type == "belongsTo":
            # If this model belongs to another, the other side likely has hasMany
            # So use plural form: User <- Post, back_populates="posts"
            return self._simple_pluralize(model_lower)
        elif relation_type == "manyToMany":
            # For manyToMany, use plural form on both sides
            return self._simple_pluralize(model_lower)
        else:
            # For hasMany or hasOne, the other side likely has belongsTo
            # So use singular form: User -> posts, back_populates="user"
            return model_lower

    def _simple_pluralize(self, word: str) -> str:
        """Simple pluralization for relationship names.

        Args:
            word: Singular word

        Returns:
            Pluralized word
        """
        if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        elif word.endswith("s") or word.endswith("x") or word.endswith("z"):
            return word + "es"
        else:
            return word + "s"

    def _get_association_table_name(
        self, model1: str, model2: str, custom_name: str | None = None
    ) -> str:
        """Generate association table name for many-to-many relationships.

        Args:
            model1: First model name
            model2: Second model name
            custom_name: Custom association table name if specified

        Returns:
            Association table variable name
        """
        if custom_name:
            return custom_name

        # Generate default name by combining model names in alphabetical order
        names = sorted([self._to_snake_case(model1), self._to_snake_case(model2)])
        return f"{names[0]}_{names[1]}_association"

    def _get_sqlalchemy_type(self, field_def: FieldDefinition, field_name: str = "", model_name: str = "") -> str:
        """Get SQLAlchemy column type for a field.

        Args:
            field_def: Field definition
            field_name: Name of the field (for enum naming)
            model_name: Name of the model (for enum naming)

        Returns:
            SQLAlchemy type string (e.g., "String(255)", "Integer")
        """
        schema_type_lower = field_def.type.lower()

        # Handle string types with max_length
        if schema_type_lower in ("string", "str") and field_def.max_length:
            return f"sa.String({field_def.max_length})"

        # Handle vector types (array of floats)
        if schema_type_lower == "vector":
            dimensions = field_def.dimensions or 1536  # Default to OpenAI embedding size
            return f"sa.ARRAY(sa.Float, dimensions={dimensions})"

        # Handle list types (both list<type> and list[type] formats)
        if schema_type_lower.startswith("list<"):
            inner_type = schema_type_lower[5:-1].strip()
            inner_sa_type = SQLALCHEMY_TYPE_MAP.get(inner_type, "sa.String")
            return f"sa.ARRAY({inner_sa_type})"
        if schema_type_lower.startswith("list["):
            inner_type = schema_type_lower[5:-1].strip()
            inner_sa_type = SQLALCHEMY_TYPE_MAP.get(inner_type, "sa.String")
            return f"sa.ARRAY({inner_sa_type})"

        # Handle enum types
        if schema_type_lower == "enum" and field_def.values:
            enum_class_name = self._get_enum_class_name(field_name, model_name)
            return f"sa.Enum({enum_class_name})"

        # Standard type mapping
        return SQLALCHEMY_TYPE_MAP.get(schema_type_lower, "sa.String")

    def _get_python_type_hint(self, field_def: FieldDefinition, field_name: str = "", model_name: str = "") -> str:
        """Get Python type hint for ORM model field.

        Args:
            field_def: Field definition
            field_name: Name of the field (for enum naming)
            model_name: Name of the model (for enum naming)

        Returns:
            Python type hint string
        """
        schema_type_lower = field_def.type.lower()

        # Handle list types (both list<type> and list[type] formats)
        if schema_type_lower.startswith("list<"):
            inner_type = schema_type_lower[5:-1].strip()
            inner_python_type = PYTHON_TYPE_HINTS.get(inner_type, "str")
            return f"list[{inner_python_type}]"
        if schema_type_lower.startswith("list["):
            inner_type = schema_type_lower[5:-1].strip()
            inner_python_type = PYTHON_TYPE_HINTS.get(inner_type, "str")
            return f"list[{inner_python_type}]"

        # Handle vector types
        if schema_type_lower == "vector":
            return "list[float]"

        # Handle enum types
        if schema_type_lower == "enum" and field_def.values:
            enum_class_name = self._get_enum_class_name(field_name, model_name)
            return enum_class_name

        # Standard type mapping
        return PYTHON_TYPE_HINTS.get(schema_type_lower, "str")

    def _format_default(self, value) -> str:
        """Format a default value for SQLAlchemy column definition.

        Args:
            value: The default value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        else:
            return repr(value)

    def _generate_check_constraints(self, field_name: str, field_def: FieldDefinition) -> list[str]:
        """Generate check constraints for a field based on min/max values.

        Args:
            field_name: Name of the field
            field_def: Field definition with potential min/max constraints

        Returns:
            List of CheckConstraint strings to add to __table_args__
        """
        constraints = []

        # Generate min constraint
        if field_def.min is not None:
            constraint_name = f"check_{field_name}_min"
            constraints.append(
                f'sa.CheckConstraint("{field_name} >= {field_def.min}", name="{constraint_name}")'
            )

        # Generate max constraint
        if field_def.max is not None:
            constraint_name = f"check_{field_name}_max"
            constraints.append(
                f'sa.CheckConstraint("{field_name} <= {field_def.max}", name="{constraint_name}")'
            )

        return constraints

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case for table names.

        Args:
            name: PascalCase name

        Returns:
            snake_case name
        """
        import re
        # Insert underscore before uppercase letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_enum_class_name(self, field_name: str, model_name: str) -> str:
        """Generate an enum class name from field and model name.

        Args:
            field_name: Name of the field
            model_name: Name of the model

        Returns:
            Enum class name in PascalCase (e.g., "UserRole", "OrderStatus")
        """
        # Convert field_name to PascalCase
        field_pascal = "".join(word.capitalize() for word in field_name.split("_"))
        return f"{model_name}{field_pascal}"

    def _collect_type_imports(self, schema: SchnitzelSchema) -> None:
        """Collect necessary imports based on field types used.

        Args:
            schema: The schema to scan for type usage
        """
        for model in schema.models.values():
            for field_name, field_def in model.fields.items():
                field_type_lower = field_def.type.lower()

                # Check for UUID type
                if "uuid" in field_type_lower:
                    self.needs_uuid = True

                # Check for datetime type
                if "datetime" in field_type_lower or "date" in field_type_lower:
                    self.needs_datetime = True

                # Check for json type (needs Any)
                if field_type_lower == "json":
                    self.needs_any = True

                # Check for auto fields (needs func)
                if field_def.auto in ("create", "update"):
                    self.needs_func = True

                # Check for enum types
                if field_type_lower == "enum" and field_def.values:
                    self.needs_enum = True
                    enum_class_name = self._get_enum_class_name(field_name, model.name)
                    # Store enum definition if not already present
                    if enum_class_name not in self.enum_definitions:
                        self.enum_definitions[enum_class_name] = field_def.values

            # Check for relationships
            if model.relations:
                self.needs_relationship = True

    def _collect_association_tables(self, schema: SchnitzelSchema) -> None:
        """Collect association tables from manyToMany relationships.

        Args:
            schema: The schema to scan for manyToMany relationships
        """
        seen_pairs = set()

        for model in schema.models.values():
            if not model.relations:
                continue

            for relation_name, relation_def in model.relations.items():
                if relation_def.type == "manyToMany":
                    self.needs_table = True

                    # Create a consistent pair key (alphabetically sorted)
                    pair = tuple(sorted([model.name, relation_def.model]))
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)

                    # Generate or use custom table name
                    table_name = self._get_association_table_name(
                        model.name,
                        relation_def.model,
                        relation_def.through
                    )
                    self.association_tables[table_name] = pair

    def _generate_association_table(self, table_name: str, model1: str, model2: str) -> str:
        """Generate an association table for manyToMany relationships.

        Args:
            table_name: Name of the association table variable
            model1: First model name
            model2: Second model name

        Returns:
            Generated association table code
        """
        table1 = self._pluralize_table_name(model1)
        table2 = self._pluralize_table_name(model2)

        # Infer the FK type from the models (default to UUID)
        fk1_type = "sa.UUID"
        fk2_type = "sa.UUID"

        if self.schema:
            for model_name, sa_type_var in [(model1, "fk1_type"), (model2, "fk2_type")]:
                if model_name in self.schema.models:
                    model = self.schema.models[model_name]
                    if model.fields:
                        for field_name, field_def in model.fields.items():
                            if field_def.primary:
                                if sa_type_var == "fk1_type":
                                    fk1_type = self._get_sqlalchemy_type(field_def, field_name, model_name)
                                else:
                                    fk2_type = self._get_sqlalchemy_type(field_def, field_name, model_name)
                                break

        return f'''{table_name} = sa.Table(
    "{self._to_snake_case(model1)}_{self._to_snake_case(model2)}",
    Base.metadata,
    sa.Column("{self._to_snake_case(model1)}_id", {fk1_type}, sa.ForeignKey("{table1}.id"), primary_key=True),
    sa.Column("{self._to_snake_case(model2)}_id", {fk2_type}, sa.ForeignKey("{table2}.id"), primary_key=True),
)'''

    def _build_imports(self) -> str:
        """Build import statements based on collected requirements.

        Returns:
            Import statements as string
        """
        imports = []

        # Future annotations for forward references
        imports.append("from __future__ import annotations")
        imports.append("")

        # Standard library imports
        if self.needs_enum:
            imports.append("import enum")
        if self.needs_datetime:
            imports.append("from datetime import datetime")
        if self.needs_uuid:
            imports.append("import uuid")
        if self.needs_any:
            imports.append("from typing import Any")

        if self.needs_enum or self.needs_datetime or self.needs_uuid or self.needs_any:
            imports.append("")

        # SQLAlchemy imports - using 'sa' alias
        imports.append("import sqlalchemy as sa")
        imports.append("from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column")

        if self.needs_relationship:
            imports.append("from sqlalchemy.orm import relationship")

        if self.needs_func:
            imports.append("from sqlalchemy import func")

        return "\n".join(imports)

    def _build_base_declaration(self) -> str:
        """Build the SQLAlchemy Base class declaration.

        Returns:
            Base class declaration as string
        """
        return """class Base(DeclarativeBase):
    \"\"\"SQLAlchemy declarative base class.\"\"\"
    pass"""
