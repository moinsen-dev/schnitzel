# SCHNITZEL

**Schema-Driven Full-Stack Framework**

> *"One Schema to Rule Them All"*
>
> AI-First | Schema-Driven | Batteries Included

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is Schnitzel?

Schnitzel is a meta-framework that eliminates the friction between Flutter frontends and Python (FastAPI) backends through a unified schema language. Define your domain once in a declarative YAML schema, and Schnitzel generates type-safe code for both platforms, complete with AI-powered tooling that understands the entire system.

**The Name:** "Schnitzel" is a playful German wordplay on "Schnittstelle" (interface) - because at its core, this framework is all about interfaces.

---

## Quick Start

```bash
# Install Schnitzel
pip install schnitzel

# Initialize a new project
schnitzel init myapp

# Generate code from your schema
schnitzel generate
```

---

## The Schnitzel Promise

1. **Define** your domain in `schema.schnitzel.yaml`
2. **Run** `schnitzel generate`
3. **Ship** with type-safe Flutter + FastAPI code, Docker setup, and AI tooling

---

## Features

- **Schema as Single Source of Truth** - One YAML file defines models, endpoints, events, and streams
- **Always Fresh** - No pre-baked templates; init scripts use latest tool versions at runtime
- **Zero-Tolerance Quality** - Generated code has no errors, no warnings, no TODOs, no mock data
- **AI-Native** - Auto-generated CLAUDE.md, MCP servers, and context files for AI comprehension
- **Batteries Included** - Docker Compose with Redis, Postgres, Qdrant, and Temporal pre-configured

### Generated Output

| Platform | Technologies |
|----------|--------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **Frontend** | Flutter, flutter_bloc, Freezed, Dio, Drift |
| **Infrastructure** | Docker Compose, PostgreSQL 16, Redis 7, Qdrant |

---

## Documentation

- [Product Requirements Document](Schnitzel_PRD_v2.md) - Full vision and schema language specification
- [Implementation Plan](ImplementationPlan.md) - Development roadmap and phases
- [CLI Documentation](schnitzel-cli/README.md) - Command reference

---

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting a pull request.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**A Moinsen Development Project** - Led by Ulrich Diedrichsen
