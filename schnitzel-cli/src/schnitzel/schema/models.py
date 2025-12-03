"""Pydantic models for Schnitzel schema validation."""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field as PydanticField, field_validator, model_validator


# =============================================================================
# Field Definition Models
# =============================================================================

class FieldDefinition(BaseModel):
    """Definition of a model field."""

    type: str
    primary: bool = False
    unique: bool = False
    optional: bool = False
    required: bool = False
    default: Optional[Any] = None
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    max_length: Optional[int] = None  # For string length validation
    format: Optional[str] = None
    auto: Optional[Literal["create", "update"]] = None
    values: Optional[List[str]] = None  # For enum types
    dimensions: Optional[int] = None  # For vector types

    # Note: Field type validation is performed by SchemaValidator
    # to provide better error messages with suggestions.

    @model_validator(mode="after")
    def validate_required_optional_mutually_exclusive(self) -> "FieldDefinition":
        """Ensure required and optional are not both True."""
        if self.required and self.optional:
            raise ValueError("Field cannot be both required and optional")
        return self


# Legacy alias for backwards compatibility
Field = FieldDefinition


class Relation(BaseModel):
    """Definition of a model relationship."""

    type: Literal["belongsTo", "hasMany", "hasOne"]
    model: str
    foreign_key: Optional[str] = None
    cascade: bool = False


# =============================================================================
# Model Definition
# =============================================================================

class Model(BaseModel):
    """Definition of a data model."""

    name: str
    description: Optional[str] = None
    fields: Dict[str, FieldDefinition] = PydanticField(default_factory=dict)
    relations: Optional[Dict[str, Relation]] = None
    indexes: Optional[List[Union[str, List[str]]]] = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Validate model name is not empty."""
        if not v:
            raise ValueError("Model name cannot be empty")
        # Note: Full PascalCase validation is performed by SchemaValidator
        # to provide better error messages with suggestions
        return v


# =============================================================================
# Schema Metadata Models
# =============================================================================

class SchemaMetadata(BaseModel):
    """Metadata for the schema."""

    name: str
    version: str
    org: str
    description: Optional[str] = None
    docs: Optional[str] = None


class FeatureMetadata(BaseModel):
    """Metadata for a feature schema."""

    name: str
    version: str
    description: Optional[str] = None
    docs: Optional[str] = None


# =============================================================================
# Root Schema Model
# =============================================================================

class SchnitzelSchema(BaseModel):
    """Root Schnitzel schema model."""

    schnitzel: Optional[str] = None  # Optional for feature schemas
    meta: Optional[SchemaMetadata] = None
    feature: Optional[FeatureMetadata] = None
    imports: Optional[List[str]] = None
    models: Dict[str, Model] = PydanticField(default_factory=dict)
    endpoints: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    roles: Optional[Dict[str, Any]] = None
    services: Optional[Dict[str, Any]] = None
    jobs: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None
    payments: Optional[Dict[str, Any]] = None
    i18n: Optional[Dict[str, Any]] = None
    errors: Optional[Dict[str, Any]] = None
    environments: Optional[Dict[str, Any]] = None
    observability: Optional[Dict[str, Any]] = None
    cicd: Optional[Dict[str, Any]] = None
    release: Optional[Dict[str, Any]] = None
    documentation: Optional[Dict[str, Any]] = None
    linting: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    app: Optional[Dict[str, Any]] = None

    @field_validator("schnitzel")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate schema version format."""
        # Version is optional for feature schemas
        return v

    @model_validator(mode="before")
    @classmethod
    def preprocess_models_dict(cls, data: Any) -> Any:
        """Convert models dict structure to proper format before validation."""
        if not isinstance(data, dict):
            return data

        models = data.get("models")
        if models is None or not isinstance(models, dict):
            return data

        # Convert dict definitions to Model instances
        converted_models = {}
        for model_name, model_data in models.items():
            if isinstance(model_data, dict):
                # Add name to model data if not present
                model_dict = model_data.copy()
                model_dict["name"] = model_name

                # Convert fields to FieldDefinition instances
                if "fields" in model_dict and isinstance(model_dict["fields"], dict):
                    converted_fields = {}
                    for field_name, field_data in model_dict["fields"].items():
                        if isinstance(field_data, dict):
                            try:
                                converted_fields[field_name] = FieldDefinition(**field_data)
                            except Exception as e:
                                # Re-raise with context about which model/field failed
                                raise ValueError(
                                    f"Invalid field definition for '{field_name}' in model '{model_name}': {e}"
                                ) from e
                        else:
                            converted_fields[field_name] = field_data
                    model_dict["fields"] = converted_fields

                # Convert relations to Relation instances
                if "relations" in model_dict and isinstance(model_dict["relations"], dict):
                    converted_relations = {}
                    for rel_name, rel_data in model_dict["relations"].items():
                        if isinstance(rel_data, dict):
                            try:
                                converted_relations[rel_name] = Relation(**rel_data)
                            except Exception as e:
                                # Re-raise with context about which model/relation failed
                                raise ValueError(
                                    f"Invalid relation definition for '{rel_name}' in model '{model_name}': {e}"
                                ) from e
                        else:
                            converted_relations[rel_name] = rel_data
                    model_dict["relations"] = converted_relations

                try:
                    converted_models[model_name] = Model(**model_dict)
                except Exception as e:
                    # Re-raise with context about which model failed
                    raise ValueError(
                        f"Invalid model definition for '{model_name}': {e}"
                    ) from e
            else:
                converted_models[model_name] = model_data

        data["models"] = converted_models
        return data


# =============================================================================
# Helper Type Aliases for Code Generation
# =============================================================================

PYTHON_TYPE_MAP = {
    "string": "str",
    "uuid": "UUID",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "datetime": "datetime",
    "json": "dict[str, Any]",
}

DART_TYPE_MAP = {
    "string": "String",
    "uuid": "String",
    "int": "int",
    "float": "double",
    "bool": "bool",
    "datetime": "DateTime",
    "json": "Map<String, dynamic>",
}
