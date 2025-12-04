"""Code generators for Schnitzel framework."""

from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.generators.python.events import EventPublisherGenerator
from schnitzel.generators.python.streams import SSEStreamGenerator
from schnitzel.generators.python.websocket import WebSocketHandlerGenerator
from schnitzel.generators.python.jobs import TemporalJobGenerator
from schnitzel.generators.dart.models import DartModelGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator
from schnitzel.generators.dart.events import DartEventClientGenerator
from schnitzel.generators.dart.bloc import BlocStateGenerator
from schnitzel.generators.infra.migrations import AlembicMigrationGenerator

__all__ = [
    "PythonModelGenerator",
    "SQLAlchemyORMGenerator",
    "PythonRouteGenerator",
    "EventPublisherGenerator",
    "SSEStreamGenerator",
    "WebSocketHandlerGenerator",
    "TemporalJobGenerator",
    "DartModelGenerator",
    "DartApiClientGenerator",
    "DartEventClientGenerator",
    "BlocStateGenerator",
    "AlembicMigrationGenerator",
]
