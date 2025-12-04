"""Pydantic models for Schnitzel schema validation."""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field as PydanticField, field_validator, model_validator


# =============================================================================
# Field Definition Models
# =============================================================================

class FieldDefinition(BaseModel):
    """Definition of a model field."""

    type: str
    description: Optional[str] = None
    primary: bool = False
    unique: bool = False
    index: bool = False  # Whether to create an index on this field
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

    type: Literal["belongsTo", "hasMany", "hasOne", "manyToMany"]
    model: str
    foreign_key: Optional[str] = None
    cascade: bool = False
    through: Optional[str] = None  # Association table name for manyToMany


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
# Event Configuration Models
# =============================================================================

class EventConfig(BaseModel):
    """Configuration for an event definition."""

    name: str
    description: Optional[str] = None
    payload: Dict[str, Any] = PydanticField(default_factory=dict)
    channels: List[str] = PydanticField(default_factory=list)

    @field_validator("channels")
    @classmethod
    def validate_channels_not_empty(cls, v: List[str]) -> List[str]:
        """Validate that at least one channel is specified."""
        if not v:
            raise ValueError("At least one channel must be specified")
        return v


# =============================================================================
# Stream Configuration Models
# =============================================================================

class MessageConfig(BaseModel):
    """Configuration for a WebSocket message type."""

    type: str
    payload: Dict[str, str] = PydanticField(default_factory=dict)

    @field_validator("type")
    @classmethod
    def validate_type_not_empty(cls, v: str) -> str:
        """Validate message type is not empty."""
        if not v:
            raise ValueError("Message type cannot be empty")
        return v


class StreamConfig(BaseModel):
    """Configuration for a stream definition (SSE or WebSocket)."""

    name: str
    type: Literal["sse", "websocket"]
    path: str
    description: Optional[str] = None
    auth: Literal["required", "optional", "none"] = "required"
    roles: Optional[List[str]] = None
    params: Optional[Dict[str, Any]] = None
    # For SSE streams
    events: Optional[List[str]] = None
    # For WebSocket streams
    messages: Optional[List[MessageConfig]] = None
    # Chunks define the data structure for both SSE and WebSocket
    chunks: Optional[Dict[str, Any]] = None

    @field_validator("path")
    @classmethod
    def validate_path_format(cls, v: str) -> str:
        """Validate path starts with /."""
        if not v.startswith("/"):
            raise ValueError("Path must start with '/'")
        return v


# =============================================================================
# Job Configuration Models
# =============================================================================

class RetryPolicy(BaseModel):
    """Retry policy configuration for Temporal jobs."""

    max_attempts: int = 3
    initial_interval: str = "1m"
    backoff_coefficient: Optional[float] = 2.0

    @field_validator("max_attempts")
    @classmethod
    def validate_max_attempts_positive(cls, v: int) -> int:
        """Validate max_attempts is positive."""
        if v < 1:
            raise ValueError("max_attempts must be at least 1")
        return v

    @field_validator("backoff_coefficient")
    @classmethod
    def validate_backoff_coefficient_positive(cls, v: Optional[float]) -> Optional[float]:
        """Validate backoff_coefficient is positive if specified."""
        if v is not None and v < 1.0:
            raise ValueError("backoff_coefficient must be at least 1.0")
        return v


class JobConfig(BaseModel):
    """Configuration for a Temporal job definition."""

    name: str
    schedule: Optional[str] = None  # Cron expression (optional for manual-trigger jobs)
    workflow: str  # PascalCase workflow name
    timeout: str = "30m"  # Default timeout
    retry_policy: Optional[RetryPolicy] = None
    params: Optional[Dict[str, str]] = None  # Workflow parameters with types

    @field_validator("workflow")
    @classmethod
    def validate_workflow_pascalcase(cls, v: str) -> str:
        """Validate workflow name is PascalCase."""
        if not v:
            raise ValueError("Workflow name cannot be empty")
        if not v[0].isupper():
            raise ValueError("Workflow name must be PascalCase (start with uppercase)")
        return v


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
    events: Optional[Dict[str, EventConfig]] = None
    streams: Optional[Dict[str, StreamConfig]] = None
    jobs: Optional[Dict[str, JobConfig]] = None
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
    def preprocess_schema_data(cls, data: Any) -> Any:
        """Convert models, jobs, streams, and events dict structures to proper format before validation."""
        if not isinstance(data, dict):
            return data

        # Convert events dict to EventConfig instances
        events = data.get("events")
        if events is not None and isinstance(events, dict):
            converted_events = {}
            for event_name, event_data in events.items():
                if isinstance(event_data, dict):
                    event_dict = event_data.copy()
                    # Add name if not present
                    if "name" not in event_dict:
                        event_dict["name"] = event_name
                    try:
                        converted_events[event_name] = EventConfig(**event_dict)
                    except Exception as e:
                        raise ValueError(
                            f"Invalid event definition for '{event_name}': {e}"
                        ) from e
                else:
                    converted_events[event_name] = event_data
            data["events"] = converted_events

        # Convert streams dict to StreamConfig instances
        streams = data.get("streams")
        if streams is not None and isinstance(streams, dict):
            converted_streams = {}
            for stream_name, stream_data in streams.items():
                if isinstance(stream_data, dict):
                    stream_dict = stream_data.copy()
                    # Add name if not present
                    if "name" not in stream_dict:
                        stream_dict["name"] = stream_name
                    # Add path - the key in the streams dict is the path
                    if "path" not in stream_dict:
                        stream_dict["path"] = stream_name

                    # Convert messages list to MessageConfig instances for WebSocket streams
                    if stream_dict.get("type") == "websocket" and "messages" in stream_dict:
                        messages = stream_dict["messages"]
                        if isinstance(messages, list):
                            converted_messages = []
                            for msg_data in messages:
                                if isinstance(msg_data, dict):
                                    try:
                                        converted_messages.append(MessageConfig(**msg_data))
                                    except Exception as e:
                                        raise ValueError(
                                            f"Invalid message definition in stream '{stream_name}': {e}"
                                        ) from e
                                else:
                                    converted_messages.append(msg_data)
                            stream_dict["messages"] = converted_messages

                    try:
                        converted_streams[stream_name] = StreamConfig(**stream_dict)
                    except Exception as e:
                        raise ValueError(
                            f"Invalid stream definition for '{stream_name}': {e}"
                        ) from e
                else:
                    converted_streams[stream_name] = stream_data
            data["streams"] = converted_streams

        # Convert jobs dict to JobConfig instances (backward compatibility)
        jobs = data.get("jobs")
        if jobs is not None and isinstance(jobs, dict):
            converted_jobs = {}
            for job_name, job_data in jobs.items():
                if isinstance(job_data, dict):
                    job_dict = job_data.copy()

                    # Add name if not present (backward compatibility)
                    if "name" not in job_dict:
                        job_dict["name"] = job_name

                    # Convert workflow if not present - use PascalCase of job name
                    if "workflow" not in job_dict:
                        # Convert snake_case to PascalCase
                        workflow_name = "".join(word.capitalize() for word in job_name.split("_"))
                        job_dict["workflow"] = workflow_name

                    # Convert timeout to string if it's an integer (backward compatibility)
                    if "timeout" in job_dict and isinstance(job_dict["timeout"], int):
                        job_dict["timeout"] = f"{job_dict['timeout']}s"

                    # Convert retry to retry_policy (backward compatibility)
                    if "retry" in job_dict and "retry_policy" not in job_dict:
                        retry_data = job_dict.pop("retry")
                        if isinstance(retry_data, dict):
                            # Map old retry format to new RetryPolicy format
                            retry_policy = {}
                            if "max_attempts" in retry_data:
                                retry_policy["max_attempts"] = retry_data["max_attempts"]
                            if "backoff" in retry_data:
                                # Map backoff types (exponential -> coefficient of 2.0)
                                if retry_data["backoff"] == "exponential":
                                    retry_policy["backoff_coefficient"] = 2.0
                            if "initial_interval" in retry_data:
                                retry_policy["initial_interval"] = retry_data["initial_interval"]
                            job_dict["retry_policy"] = retry_policy

                    try:
                        converted_jobs[job_name] = JobConfig(**job_dict)
                    except Exception as e:
                        # Re-raise with context about which job failed
                        raise ValueError(
                            f"Invalid job definition for '{job_name}': {e}"
                        ) from e
                else:
                    converted_jobs[job_name] = job_data

            data["jobs"] = converted_jobs

        models = data.get("models")

        # Handle None or missing models - convert to empty dict
        if models is None:
            data["models"] = {}
            return data

        if not isinstance(models, dict):
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
    "str": "str",
    "text": "str",
    "uuid": "UUID",
    "int": "int",
    "integer": "int",
    "float": "float",
    "double": "float",
    "decimal": "Decimal",
    "bool": "bool",
    "boolean": "bool",
    "datetime": "datetime",
    "date": "datetime",
    "json": "dict[str, Any]",
    "vector": "list[float]",
    "bytes": "bytes",
}

DART_TYPE_MAP = {
    "string": "String",
    "str": "String",
    "int": "int",
    "integer": "int",
    "float": "double",
    "double": "double",
    "decimal": "double",  # Decimals are doubles in Dart
    "bool": "bool",
    "boolean": "bool",
    "datetime": "DateTime",
    "date": "DateTime",
    "uuid": "String",  # UUIDs are strings in Dart
    "text": "String",
    "json": "Map<String, dynamic>",
    "list": "List<dynamic>",
    "vector": "List<double>",
    "bytes": "List<int>",
}
