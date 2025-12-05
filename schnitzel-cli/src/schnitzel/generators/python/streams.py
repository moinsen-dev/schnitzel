"""Python FastAPI SSE stream generator for Schnitzel schemas.

Generates FastAPI Server-Sent Events (SSE) streaming endpoints with proper
async generators, reconnection support, and chunk serialization.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import re
from jinja2 import Environment, PackageLoader, select_autoescape

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema, PYTHON_TYPE_MAP
from schnitzel.generators.validation_utils import validate_stream_type


class SSEStreamGenerator:
    """Generates FastAPI SSE streaming endpoints from Schnitzel schemas."""

    def __init__(self):
        """Initialize the SSE stream generator."""
        self.env = Environment(
            loader=PackageLoader('schnitzel', 'templates/python'),
            autoescape=select_autoescape(),
        )

    def generate(self, schema: SchnitzelSchema) -> str:
        """
        Generate Python FastAPI SSE streaming endpoints from a schema.

        Args:
            schema: The Schnitzel schema to generate SSE streams from

        Returns:
            Generated Python code as a string
        """
        # Check if schema has streams section
        if not schema.streams:
            return self._generate_empty_streams()

        # Filter streams by type='sse'
        sse_streams = {}
        for name, stream_def in schema.streams.items():
            # Handle both StreamConfig objects and plain dicts
            stream_type = stream_def.type if hasattr(stream_def, 'type') else stream_def.get("type")
            if stream_type == "sse":
                sse_streams[name] = stream_def

        if not sse_streams:
            return self._generate_empty_streams()

        # Parse streams and prepare template data
        streams_data = []
        needs_uuid = False
        needs_auth = False
        needs_base_model = False

        for stream_name, stream_def in sse_streams.items():
            stream_info = self._parse_stream(stream_name, stream_def)
            streams_data.append(stream_info)

            # Track what imports we need
            if stream_info['needs_uuid']:
                needs_uuid = True
            if stream_info['auth_required']:
                needs_auth = True
            if stream_info['chunk_model'] is not None:
                needs_base_model = True

        # Build imports set - avoid duplicates
        imports = set()

        # Always needed imports
        imports.add('from typing import AsyncGenerator, Any')
        imports.add('import asyncio')
        imports.add('import json')
        imports.add('from datetime import datetime')

        # Conditional imports
        if needs_uuid:
            imports.add('from uuid import UUID')

        # FastAPI imports - combine into single import
        fastapi_imports = ['APIRouter', 'StreamingResponse']
        if needs_auth:
            fastapi_imports.append('Depends')
            imports.add('from ..auth import get_current_user')

        imports.add(f"from fastapi import {', '.join(sorted(fastapi_imports))}")

        if needs_base_model:
            imports.add('from pydantic import BaseModel')

        # Collect model imports (User for auth)
        model_imports = []
        if needs_auth:
            model_imports.append('User')

        # Load and render template
        template = self.env.get_template("streams.py.j2")
        rendered = template.render(
            streams=streams_data,
            imports=sorted(imports),
            model_imports=model_imports
        )
        return rendered

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """
        Generate Python FastAPI SSE streams and write them to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the streams to 'streams.py' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate SSE streams from
            output_dir: Directory where streams.py should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to streams.py file, size in bytes)

        Example:
            >>> generator = SSEStreamGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "backend/app/generated")
            >>> print(f"Streams written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the stream code
        streams_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""# Generated by Schnitzel Framework v{__version__}
# DO NOT EDIT - This file is auto-generated
# Generated at: {timestamp}
# Source: {schema_source}

"""

        # Combine header with generated code
        full_code = header + streams_code

        # Calculate file path and size
        streams_file = output_path / "streams.py"
        file_size = len(full_code.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return streams_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Warn if file already exists
        if streams_file.exists():
            print(f"Warning: Overwriting existing file: {streams_file}")

        streams_file.write_text(full_code, encoding="utf-8")

        return streams_file, file_size

    def _generate_empty_streams(self) -> str:
        """Generate a minimal streams file when no SSE streams are defined."""
        return '''from fastapi import APIRouter


router = APIRouter()
'''

    def _get_attr(self, obj: Any, attr: str, default: Any = None) -> Any:
        """Get attribute from StreamConfig object or dict.

        Args:
            obj: StreamConfig object or dict
            attr: Attribute name
            default: Default value if attribute not found

        Returns:
            Attribute value or default
        """
        if hasattr(obj, attr):
            return getattr(obj, attr, default)
        elif isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    def _parse_stream(self, stream_name: str, stream_def: Any) -> Dict[str, Any]:
        """Parse a stream definition into template data.

        Args:
            stream_name: Name of the stream
            stream_def: Stream definition from schema (StreamConfig object or dict)

        Returns:
            Dictionary with stream information for template rendering

        Raises:
            ValueError: If validation fails
        """
        # Extract stream configuration (handle both StreamConfig and dict)
        path = self._get_attr(stream_def, "path", f"/stream/{stream_name}")
        function_name = self._get_attr(stream_def, "name", stream_name)
        description = self._get_attr(stream_def, "description", f"SSE stream for {stream_name}")
        auth = self._get_attr(stream_def, "auth", "optional")
        auth_required = auth == "required"
        chunks = self._get_attr(stream_def, "chunks", {})
        events = self._get_attr(stream_def, "events", [])

        # Validate stream type (F98)
        stream_type = self._get_attr(stream_def, "type", "sse")
        try:
            validate_stream_type(stream_type)
        except ValueError as e:
            raise ValueError(f"Stream '{stream_name}': {e}") from e

        # Extract path parameters from the path (e.g., /chat/{conversation_id}/stream)
        path_params = re.findall(r'\{(\w+)\}', path)

        # Build function parameters
        parameters = []
        needs_uuid = False

        # Add path parameters
        for param_name in path_params:
            # Default to UUID type for id-like params, otherwise str
            if param_name.endswith('_id') or param_name == 'id':
                param_type = "UUID"
                needs_uuid = True
            else:
                param_type = "str"

            parameters.append({
                'name': param_name,
                'type': param_type,
                'default': None
            })

        # Add auth dependency if required
        if auth_required:
            parameters.append({
                'name': 'current_user',
                'type': 'User',
                'default': 'Depends(get_current_user)'
            })

        # Build generator parameters (pass-through params)
        generator_params = [p['name'] for p in parameters]

        # Build chunk model if chunks are defined
        chunk_model = None
        if chunks:
            chunk_fields = []
            for chunk_name, chunk_def in chunks.items():
                if isinstance(chunk_def, dict):
                    chunk_type = self._get_python_type(chunk_def.get("type", "string"))
                    optional = chunk_def.get("optional", False)

                    if 'UUID' in chunk_type:
                        needs_uuid = True

                    field_info = {
                        'name': chunk_name,
                        'type': chunk_type + (' | None = None' if optional else '')
                    }
                    chunk_fields.append(field_info)
                else:
                    chunk_fields.append({
                        'name': chunk_name,
                        'type': 'str'
                    })

            # Generate chunk model name (PascalCase from function_name)
            chunk_model_name = ''.join(word.capitalize() for word in function_name.split('_')) + 'Chunk'

            chunk_model = {
                'name': chunk_model_name,
                'fields': chunk_fields
            }

        return {
            'name': stream_name,
            'function_name': function_name,
            'path': path,
            'description': description,
            'operation_id': function_name,
            'auth_required': auth_required,
            'parameters': parameters,
            'generator_name': f'_generate_{function_name}_events',
            'generator_params': generator_params,
            'chunk_model': chunk_model,
            'needs_uuid': needs_uuid,
            'events': events,
        }

    def _get_python_type(self, schema_type: str) -> str:
        """
        Map schema type to Python type.

        Args:
            schema_type: Type from schema (e.g., "string", "int", "uuid")

        Returns:
            Python type string (e.g., "str", "int", "UUID")
        """
        schema_type_lower = schema_type.lower()

        # Handle list types: list<string> -> list[str]
        if schema_type_lower.startswith("list<") and schema_type_lower.endswith(">"):
            inner_type = schema_type_lower[5:-1].strip()
            inner_python_type = PYTHON_TYPE_MAP.get(inner_type, inner_type)
            return f"list[{inner_python_type}]"

        # Handle enum types
        if schema_type_lower == "enum":
            return "str"  # Enums are represented as strings in runtime

        # Handle standard types
        return PYTHON_TYPE_MAP.get(schema_type_lower, schema_type)
