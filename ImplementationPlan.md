# Schnitzel Framework — Implementation Plan

**Version:** 1.0
**Date:** December 2025
**Status:** Planning Phase — Ready for Implementation

> *A Moinsen Development Project — Led by Ulrich Diedrichsen*

---

## Implementation Decisions (Confirmed)

| Decision | Answer |
|----------|--------|
| **CLI Language** | Python (same as backend for code sharing) |
| **Template Engine** | Jinja2 for all code generation |
| **Phase 1 Scope** | Python + Dart together from the start |
| **Testing Approach** | Integration tests first, then unit tests |

---

## Executive Summary

This document outlines the complete implementation plan for the Schnitzel framework — a schema-driven full-stack code generator for Flutter + FastAPI applications. The framework consists of **84+ components** organized into **7 implementation phases**.

### Key Deliverables

| Deliverable | Description |
|-------------|-------------|
| **CLI Tool** | `schnitzel` command-line interface (14 commands) |
| **Code Generators** | 18 generators for Python, Dart, and infrastructure |
| **Runtime Libraries** | Backend services (Python) + Frontend services (Dart) |
| **AI Tooling** | CLAUDE.md, MCP server, context generators |
| **Documentation** | OpenAPI, Swagger UI, ReDoc, Markdown |

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Inventory](#2-component-inventory)
3. [Implementation Phases](#3-implementation-phases)
4. [Technology Stack](#4-technology-stack)
5. [Project Structure](#5-project-structure)
6. [Development Guidelines](#6-development-guidelines)
7. [Testing Strategy](#7-testing-strategy)
8. [Risk Assessment](#8-risk-assessment)

---

## 1. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCHNITZEL CLI                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  init   │ │generate │ │  serve  │ │validate │ │ migrate │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       │           │           │           │           │         │
│  ┌────▼───────────▼───────────▼───────────▼───────────▼────┐   │
│  │                    SCHEMA PARSER                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │  YAML    │  │  Multi-  │  │  Schema  │               │   │
│  │  │  Parser  │──▶│  File    │──▶│  Valid-  │               │   │
│  │  │          │  │  Merger  │  │  ator    │               │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                  CODE GENERATORS                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐               │   │
│  │  │ Python/FastAPI  │  │  Dart/Flutter   │               │   │
│  │  │ ┌─────────────┐ │  │ ┌─────────────┐ │               │   │
│  │  │ │ Pydantic    │ │  │ │ Freezed     │ │               │   │
│  │  │ │ SQLAlchemy  │ │  │ │ API Client  │ │               │   │
│  │  │ │ FastAPI     │ │  │ │ BLoC        │ │               │   │
│  │  │ │ Factories   │ │  │ │ Factories   │ │               │   │
│  │  │ └─────────────┘ │  │ └─────────────┘ │               │   │
│  │  └─────────────────┘  └─────────────────┘               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐               │   │
│  │  │ Infrastructure  │  │   AI Tooling    │               │   │
│  │  │ ┌─────────────┐ │  │ ┌─────────────┐ │               │   │
│  │  │ │ Docker      │ │  │ │ CLAUDE.md   │ │               │   │
│  │  │ │ Migrations  │ │  │ │ MCP Server  │ │               │   │
│  │  │ │ CI/CD       │ │  │ │ AI Context  │ │               │   │
│  │  │ └─────────────┘ │  │ └─────────────┘ │               │   │
│  │  └─────────────────┘  └─────────────────┘               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GENERATED PROJECT                             │
│  ┌───────────────────────┐  ┌───────────────────────┐          │
│  │   Flutter Frontend    │  │    Python Backend     │          │
│  │   (packages/)         │  │    (backend/)         │          │
│  └───────────────────────┘  └───────────────────────┘          │
│  ┌───────────────────────┐  ┌───────────────────────┐          │
│  │   Infrastructure      │  │    AI Tooling         │          │
│  │   (docker-compose)    │  │    (.schnitzel/)      │          │
│  └───────────────────────┘  └───────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
schema.schnitzel.yaml
        │
        ▼
┌───────────────┐
│ Schema Parser │ ─── Parse YAML, resolve imports
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Validator   │ ─── Check consistency, naming, security
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  IR (Internal │ ─── Normalized, validated schema object
│ Representation│
└───────┬───────┘
        │
        ├──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Python    │ │    Dart     │ │   Docker    │ │     AI      │
│  Generator  │ │  Generator  │ │  Generator  │ │  Generator  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 2. Component Inventory

### 2.1 Core Infrastructure (4 Components)

| Component | Purpose | Priority |
|-----------|---------|----------|
| **Schema Parser** | Parse YAML schema into internal representation | P0 |
| **Schema Validator** | Validate consistency, types, references | P0 |
| **Multi-file Merger** | Merge imported feature schemas | P0 |
| **CLI Framework** | Command routing and execution | P0 |

### 2.2 Code Generators (18 Components)

#### Python/FastAPI Generators

| Generator | Output | Priority |
|-----------|--------|----------|
| **Pydantic Models** | `models.py` — Data validation classes | P0 |
| **SQLAlchemy ORM** | `orm.py` — Database entity definitions | P1 |
| **FastAPI Routes** | `routes.py` — Endpoint stubs with signatures | P1 |
| **Field Constants** | `fields.py` — Type-safe field name constants | P1 |
| **Factories** | `factories.py` — Test data builders (factory-boy) | P2 |
| **Auth Generator** | JWT, OAuth, RBAC code | P2 |
| **Event Publisher** | WebSocket/Redis pub-sub handlers | P2 |
| **Job Generator** | Temporal workflow definitions | P2 |

#### Dart/Flutter Generators

| Generator | Output | Priority |
|-----------|--------|----------|
| **Freezed Models** | `models.dart` — Immutable data classes | P0 |
| **API Client** | `api_client.dart` — Type-safe HTTP client | P1 |
| **BLoC State** | `bloc/` — State management per feature | P2 |
| **Event Client** | `events.dart` — WebSocket/SSE handlers | P2 |
| **Field Constants** | `fields.dart` — Type-safe field names | P1 |
| **Factories** | `factories.dart` — Test data builders | P2 |

#### Infrastructure Generators

| Generator | Output | Priority |
|-----------|--------|----------|
| **Docker Compose** | `docker-compose.yaml` — Services config | P0 |
| **Database Migrations** | `.schnitzel/migrations/*.sql` | P1 |
| **Environment Config** | Flutter flavors, Gradle, XCode | P1 |
| **CI/CD Pipelines** | `.github/workflows/*.yml` | P3 |

### 2.3 CLI Commands (14 Commands)

| Command | Description | Priority | Dependencies |
|---------|-------------|----------|--------------|
| `schnitzel init` | Initialize new project | P0 | CLI Framework |
| `schnitzel generate` | Generate code from schema | P0 | All generators |
| `schnitzel serve` | Start dev environment | P1 | Docker, generators |
| `schnitzel validate` | Validate schema | P1 | Schema validator |
| `schnitzel migrate` | Database migrations | P1 | DB generator |
| `schnitzel test` | Run test suite | P2 | Test generators |
| `schnitzel seed` | Seed database | P2 | Factories |
| `schnitzel add` | Add schema component | P2 | Schema parser |
| `schnitzel lint` | Lint schema | P2 | Schema validator |
| `schnitzel docs` | Generate API docs | P2 | OpenAPI generator |
| `schnitzel ai` | AI tooling commands | P3 | AI generators |
| `schnitzel release` | Version management | P3 | Version manager |
| `schnitzel deploy` | Deploy to environment | P3 | CI/CD generator |
| `schnitzel i18n` | Translation management | P3 | i18n generator |

### 2.4 Runtime Services

#### Backend Services (Python)

| Service | Purpose |
|---------|---------|
| Authentication Service | JWT, OAuth, Magic Link, MFA |
| RBAC Permission Checker | Role-based access control |
| Event Publisher | WebSocket broadcast, Redis Pub/Sub |
| Background Job Runner | Temporal workflows |
| Cache Manager | Redis caching layer |
| Vector DB Client | Qdrant embeddings/search |
| File Storage Service | S3/MinIO uploads |
| Email Service | Resend/SendGrid integration |
| Push Notification Service | FCM/APNS |

#### Frontend Services (Dart)

| Service | Purpose |
|---------|---------|
| API Client | HTTP with auth injection |
| Event Subscription Manager | Real-time events |
| Stream Handler | SSE/WebSocket streams |
| Offline Storage & Sync | Drift local database |
| Navigation System | go_router routing |
| i18n Manager | shard_i18n translations |

### 2.5 AI Tooling (4 Components)

| Component | Output |
|-----------|--------|
| **CLAUDE.md Generator** | Project context for AI assistants |
| **MCP Server Generator** | `.schnitzel/mcp-server/` |
| **AI Context Generator** | `ai-context.json` structured metadata |
| **Prompt Generator** | `.schnitzel/prompts/` task templates |

### 2.6 Feature System (5 Components)

| Component | Purpose |
|-----------|---------|
| **Feature Resolver** | Parse feature definitions, build dependency graph |
| **Feature Package Generator** | Create Flutter packages per feature |
| **Cross-Reference Resolver** | Validate model exports between features |
| **App Shell Generator** | Main app with feature composition |
| **Workspace Config Generator** | Flutter pub workspace setup |

---

## 3. Implementation Phases

### Phase 1: Foundation (MVP)

**Goal:** Generate working code from schema (Python + Dart in parallel)
**Approach:** Build both Python and Dart generators together from day one

> **Decision:** Python + Dart developed together. This ensures the schema-to-code mapping is consistent across both languages and catches type mapping issues early.

#### Deliverables

1. **Schema Parser & Validator**
   - YAML parsing with PyYAML
   - Pydantic models for schema validation
   - Multi-file import resolution
   - Reference validation

2. **Python Model Generator (Pydantic)**
   - Field type mapping (string→str, uuid→UUID, etc.)
   - Validation rules (min, max, format, unique)
   - Relationships (belongsTo, hasMany)
   - JSON serialization

3. **Dart Model Generator (Freezed)** — *Developed in parallel with Python*
   - Field type mapping (string→String, float→double)
   - Immutable classes with copyWith
   - JSON serialization (json_serializable)
   - Nullable handling

4. **`schnitzel init` command**
   - Project scaffolding (Flutter workspace + Python backend)
   - Delegate to `flutter create`, `uv init`
   - Generate initial schema template
   - Docker Compose setup

5. **`schnitzel generate` command**
   - Target selection (all/flutter/python/docker)
   - Watch mode for development
   - Dry-run preview

6. **Docker Compose Generator**
   - PostgreSQL 16 with pgvector
   - Redis 7 with pub/sub
   - Port collision prevention
   - Health checks

#### Integration Tests (Phase 1)

```bash
# Primary test: Full generation pipeline
pytest tests/integration/test_full_generation.py

# Test flow:
# 1. Parse minimal_schema.yaml
# 2. Generate Python models → verify compiles
# 3. Generate Dart models → verify compiles
# 4. Ensure field types match across languages
```

#### Exit Criteria

- [ ] `schnitzel init myapp` creates working project
- [ ] `schnitzel generate` produces valid Python + Dart code
- [ ] Generated Pydantic models pass validation
- [ ] Generated Freezed models compile without errors
- [ ] Docker Compose starts all services
- [ ] **Integration tests pass for FoodieAI example**

---

### Phase 2: API Layer

**Goal:** Full API generation with database

#### Deliverables

1. **FastAPI Route Generator**
   - Endpoint stubs from schema
   - Query/path parameter handling
   - Request body validation
   - Response serialization
   - OpenAPI metadata

2. **Dart API Client Generator**
   - Dio-based HTTP client
   - Type-safe method signatures
   - Error handling
   - Auth token injection

3. **`schnitzel serve` command**
   - Start Docker services
   - Run FastAPI with hot reload
   - Start Flutter dev server
   - Proxy configuration

4. **`schnitzel validate` command**
   - Schema consistency checks
   - Breaking change detection
   - Naming convention validation

5. **Database Migration Generator**
   - Alembic integration
   - Schema diff detection
   - SQL generation
   - Rollback support

6. **`schnitzel migrate` command**
   - `diff` — Generate migration
   - `up` — Apply migrations
   - `down` — Rollback
   - `status` — Show state

#### Exit Criteria

- [ ] Generated FastAPI routes serve HTTP requests
- [ ] Dart API client makes successful API calls
- [ ] Database migrations create correct schema
- [ ] `schnitzel serve` starts complete dev environment

---

### Phase 3: Real-time & Events

**Goal:** Events, streams, and background jobs

#### Deliverables

1. **Event Publisher/Subscriber**
   - Redis Pub/Sub integration
   - WebSocket broadcast
   - Event type definitions
   - Payload serialization

2. **SSE Stream Handler**
   - Server-side streaming (Python)
   - Client-side consumption (Dart)
   - Chunk parsing
   - Reconnection logic

3. **WebSocket Handler**
   - Bidirectional communication
   - Connection management
   - Message routing
   - Heartbeat/keepalive

4. **Temporal Job Generator**
   - Workflow definitions
   - Activity implementations
   - Schedule configuration
   - Retry policies

5. **BLoC State Generator**
   - Feature-specific BLoCs
   - Event/State classes
   - Repository integration
   - Error handling

#### Exit Criteria

- [ ] Events publish via WebSocket/Redis
- [ ] SSE streams deliver real-time data
- [ ] Scheduled jobs execute on time
- [ ] BLoCs manage feature state correctly

---

### Phase 4: Auth & Security

**Goal:** Complete authentication system

#### Deliverables

1. **JWT Auth Generator**
   - Token generation/validation
   - Access/refresh token rotation
   - Claims management
   - Expiration handling

2. **OAuth Integration**
   - Google OAuth flow
   - Apple Sign In
   - Callback handling
   - Token exchange

3. **RBAC Permission Generator**
   - Role definitions
   - Permission checking
   - Field-level access
   - Middleware integration

4. **Session Management**
   - Redis session store
   - Session invalidation
   - Multi-device support
   - Remember me

#### Exit Criteria

- [ ] JWT auth flow works end-to-end
- [ ] OAuth providers authenticate users
- [ ] RBAC restricts access correctly
- [ ] Sessions persist across requests

---

### Phase 5: Testing & Quality

**Goal:** Test infrastructure and quality tools

#### Deliverables

1. **Factory Generator (Python + Dart)**
   - Model factories with Faker
   - Relationship factories
   - Batch generation
   - Custom overrides

2. **Mock Generator**
   - Repository mocks
   - Service mocks
   - API client mocks

3. **Contract Test Generator**
   - API contract validation
   - Request/response schemas
   - Breaking change detection

4. **`schnitzel test` command**
   - Flutter test runner
   - Pytest runner
   - Coverage reporting
   - Watch mode

5. **`schnitzel seed` command**
   - Dev environment seeding
   - Test data generation
   - Reference resolution

6. **`schnitzel lint` command**
   - Naming conventions
   - Security rules
   - Best practices
   - Auto-fix capability

#### Exit Criteria

- [ ] Factories generate valid test data
- [ ] Contract tests validate API
- [ ] `schnitzel test` runs full suite
- [ ] `schnitzel lint` catches schema issues

---

### Phase 6: Documentation & AI

**Goal:** Full documentation and AI tooling

#### Deliverables

1. **OpenAPI Generator**
   - OpenAPI 3.1 specification
   - Schema definitions
   - Endpoint documentation
   - Authentication docs

2. **`schnitzel docs` command**
   - OpenAPI export
   - Postman collection
   - Markdown generation
   - Local doc server

3. **CLAUDE.md Generator**
   - Project overview
   - Model summaries
   - Endpoint list
   - Development commands

4. **MCP Server Generator**
   - Schema query tools
   - Code generation tools
   - Validation tools
   - Documentation tools

5. **`schnitzel ai` command**
   - `context` — Regenerate AI files
   - `mcp` — Update MCP server
   - `prompt` — Generate task prompts

#### Exit Criteria

- [ ] OpenAPI spec is valid and complete
- [ ] Swagger UI renders correctly
- [ ] CLAUDE.md provides useful context
- [ ] MCP server responds to queries

---

### Phase 7: DevOps & Release

**Goal:** Production-ready deployment

#### Deliverables

1. **CI/CD Pipeline Generator**
   - GitHub Actions workflows
   - PR checks (lint, test, build)
   - Staging deployment
   - Production release

2. **`schnitzel release` command**
   - Semantic versioning
   - Changelog generation
   - Git tagging
   - Feature versioning

3. **`schnitzel deploy` command**
   - Environment deployment
   - App store upload
   - Fastlane integration
   - Rollback support

4. **App Store Metadata Generator**
   - iOS metadata
   - Android metadata
   - Screenshots config
   - Release notes

5. **i18n Generator**
   - Translation structure
   - shard_i18n setup
   - Auto-translate integration

6. **`schnitzel i18n` command**
   - `extract` — Extract strings
   - `fill` — Auto-translate
   - `validate` — Check coverage

#### Exit Criteria

- [ ] CI/CD pipelines run on GitHub
- [ ] Releases bump versions correctly
- [ ] Deployments reach target environments
- [ ] i18n workflow produces translations

---

## 4. Technology Stack

### CLI Tool (Python)

> **Decision:** CLI is written in Python (same language as backend). This allows code sharing between CLI schema models and backend runtime models.

```
schnitzel-cli/
├── pyproject.toml
├── src/
│   └── schnitzel/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI entry point
│       ├── schema/
│       │   ├── parser.py       # YAML parsing
│       │   ├── validator.py    # Schema validation
│       │   └── models.py       # Pydantic schema models
│       ├── generators/
│       │   ├── python/         # Python code generators
│       │   ├── dart/           # Dart code generators
│       │   └── infra/          # Infrastructure generators
│       ├── templates/          # Jinja2 templates
│       │   ├── python/
│       │   │   ├── models.py.j2
│       │   │   ├── orm.py.j2
│       │   │   └── routes.py.j2
│       │   ├── dart/
│       │   │   ├── models.dart.j2
│       │   │   ├── api_client.dart.j2
│       │   │   └── bloc.dart.j2
│       │   └── infra/
│       │       ├── docker-compose.yaml.j2
│       │       └── github-actions.yml.j2
│       └── commands/
│           ├── init.py
│           ├── generate.py
│           └── ...
└── tests/
```

| Dependency | Purpose |
|------------|---------|
| `typer` | CLI framework |
| `rich` | Terminal UI |
| `pyyaml` | YAML parsing |
| `pydantic` | Schema validation |
| `jinja2` | **All code generation** (Python, Dart, YAML, etc.) |

> **Decision:** Jinja2 is used for ALL code generation. A single template engine simplifies maintenance and allows shared template helpers across all output languages.

### Backend Runtime (Python)

| Dependency | Purpose |
|------------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM |
| `alembic` | Migrations |
| `pydantic` | Validation |
| `redis` | Caching |
| `temporalio` | Job scheduler |
| `qdrant-client` | Vector DB |
| `python-jose` | JWT |
| `passlib` | Password hashing |

### Frontend Runtime (Dart/Flutter)

| Dependency | Purpose |
|------------|---------|
| `flutter_bloc` | State management |
| `freezed` | Immutable models |
| `json_serializable` | JSON serialization |
| `dio` | HTTP client |
| `drift` | SQLite ORM |
| `go_router` | Navigation |
| `shard_i18n` | Internationalization |

### Infrastructure

| Service | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 16 | Primary database |
| pgvector | - | Vector embeddings |
| Redis | 7 | Cache, pub/sub |
| Qdrant | Latest | Vector search |
| Temporal | Latest | Job scheduling |

---

## 5. Project Structure

### Generated Project Layout

```
myapp/
├── schema.schnitzel.yaml      # Single source of truth
├── pubspec.yaml               # Flutter workspace root
├── CLAUDE.md                  # AI context (generated)
├── docker-compose.yaml        # Infrastructure (generated)
├── .env.dev                   # Dev secrets
├── .env.staging               # Staging secrets
├── .env.production            # Production secrets
│
├── packages/                  # Flutter pub workspace
│   ├── app/                   # Main app shell
│   │   ├── lib/
│   │   │   ├── main.dart
│   │   │   └── app.dart
│   │   └── pubspec.yaml
│   │
│   ├── ui_kit/                # Atomic Design components
│   │   ├── lib/
│   │   │   ├── atoms/
│   │   │   ├── molecules/
│   │   │   ├── organisms/
│   │   │   └── templates/
│   │   └── pubspec.yaml
│   │
│   ├── shared/                # Shared/generated code
│   │   ├── lib/
│   │   │   ├── generated/     # ⚠️ Auto-generated
│   │   │   │   ├── models.dart
│   │   │   │   ├── api_client.dart
│   │   │   │   ├── events.dart
│   │   │   │   └── fields.dart
│   │   │   └── utils/
│   │   └── pubspec.yaml
│   │
│   └── <feature>/             # Feature packages
│       ├── lib/
│       │   ├── bloc/
│       │   ├── models/
│       │   ├── pages/
│       │   └── widgets/
│       └── pubspec.yaml
│
├── backend/                   # Python backend
│   ├── app/
│   │   ├── generated/         # ⚠️ Auto-generated
│   │   │   ├── models.py
│   │   │   ├── orm.py
│   │   │   ├── routes.py
│   │   │   ├── fields.py
│   │   │   └── factories.py
│   │   ├── src/               # Custom code
│   │   │   ├── services/
│   │   │   └── utils/
│   │   └── main.py
│   ├── pyproject.toml
│   └── uv.lock
│
├── docs/                      # Documentation
│   ├── app.md
│   ├── API.md                 # Generated
│   ├── openapi.yaml           # Generated
│   ├── CHANGELOG.md
│   └── features/
│       └── <feature>.md
│
└── .schnitzel/                # Framework metadata
    ├── snapshots/             # Schema history
    │   ├── 001_initial.yaml
    │   └── 002_add_orders.yaml
    ├── migrations/            # DB migrations
    │   ├── 001_initial.sql
    │   └── 002_add_orders.sql
    ├── mcp-server/            # MCP server
    │   ├── server.py
    │   └── tools.py
    ├── prompts/               # AI prompts
    │   ├── add-feature.md
    │   └── fix-bug.md
    └── cache/                 # Build cache
```

---

## 6. Development Guidelines

### Code Generation Principles

1. **Never Edit Generated Files**
   - All files in `generated/` are overwritten
   - Custom code goes in `src/`

2. **Jinja2 Templates**
   - All code generation uses Jinja2
   - Templates stored in `schnitzel/templates/`
   - Language-specific template directories

3. **Deterministic Output**
   - Same schema → same generated code
   - Sorted imports, consistent formatting
   - No random elements

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Models | PascalCase | `User`, `OrderItem` |
| Fields | snake_case | `created_at`, `user_id` |
| Endpoints | kebab-case | `/user-profiles` |
| Events | dot.notation | `order.placed` |
| BLoCs | PascalCase + Bloc | `AuthBloc`, `OrdersBloc` |

### Zero-Tolerance Policy

- **No errors** — All generated code compiles
- **No warnings** — Strict linting compliance
- **No TODOs** — Complete implementations
- **No mock data** — Real structures and types

---

## 7. Testing Strategy

> **Approach:** Integration tests first, unit tests second. This ensures generated code works end-to-end before optimizing individual components.

### Integration Tests (Priority 1)

Integration tests validate the complete generation pipeline:

```
tests/integration/
├── test_full_generation.py     # Schema → Generated code → Compilation
├── test_foodieai_example.py    # Full FoodieAI example generation
├── test_python_compilation.py  # Generated Python compiles & runs
├── test_dart_compilation.py    # Generated Dart compiles without errors
├── test_api_contracts.py       # Generated APIs match schema contracts
└── fixtures/
    ├── minimal_schema.yaml
    ├── full_schema.yaml
    └── edge_cases/
```

#### Integration Test Flow

```
1. Load example schema (e.g., FoodieAI)
2. Run `schnitzel generate`
3. Verify Python code compiles (pyright/mypy)
4. Verify Dart code compiles (dart analyze)
5. Run generated Python tests
6. Run generated Dart tests
7. Verify API contracts match
```

### Unit Tests (Priority 2)

Unit tests cover individual components after integration tests pass:

```
tests/unit/
├── schema/
│   ├── test_parser.py
│   └── test_validator.py
├── generators/
│   ├── python/
│   │   ├── test_models.py
│   │   └── test_routes.py
│   └── dart/
│       ├── test_models.py
│       └── test_api_client.py
└── commands/
    ├── test_init.py
    └── test_generate.py
```

### Test Coverage Requirements

| Component | Minimum Coverage | Priority |
|-----------|------------------|----------|
| Integration Tests | 100% of examples | P0 |
| Schema Parser | 90% | P1 |
| Validators | 95% | P1 |
| Generators | 80% | P2 |
| CLI Commands | 70% | P2 |

---

## 8. Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema complexity | Generated code breaks | Extensive validation, incremental rollout |
| Breaking changes | Existing projects fail | Versioned schema, migration guides |
| Platform drift | Flutter/Python updates break generation | CI testing against latest versions |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Template bugs | Invalid generated code | Template unit tests, compilation checks |
| Performance | Slow generation | Caching, incremental generation |
| Dependencies | Version conflicts | Lock files, version pinning |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Documentation | Outdated docs | Auto-generate from schema |
| Adoption | Low usage | Example projects, tutorials |

---

## Appendix A: CLI Command Reference

### Quick Reference

```bash
# Project Lifecycle
schnitzel init <name> [--template minimal|full|ai-chat]
schnitzel generate [--target all|flutter|python|docker]
schnitzel serve [--backend-only] [--port 8000]

# Schema Management
schnitzel validate [--strict] [--breaking]
schnitzel lint [--fix] [--format json]
schnitzel add <type> <name>

# Database
schnitzel migrate diff --name "<description>"
schnitzel migrate up
schnitzel migrate down
schnitzel migrate status
schnitzel seed [--env dev|test]

# Testing
schnitzel test [--flutter] [--backend] [--coverage]

# Documentation
schnitzel docs [--format openapi|postman|markdown]

# Release
schnitzel release --bump patch|minor|major
schnitzel deploy --env staging|production

# AI Tooling
schnitzel ai context
schnitzel ai mcp
schnitzel ai prompt

# i18n
schnitzel i18n extract
schnitzel i18n fill --provider deepl
schnitzel i18n validate
```

---

## Appendix B: Schema Quick Reference

```yaml
schnitzel: "1.0"

meta:
  name: "MyApp"
  version: "1.0.0"
  org: "com.example"

models:
  User:
    description: "Application user"
    fields:
      id: { type: uuid, primary: true }
      email: { type: string, unique: true, format: email }
      name: { type: string, min: 1, max: 100 }
    relations:
      posts: { type: hasMany, model: Post }

endpoints:
  /users:
    GET:
      name: listUsers
      auth: required
      response: { 200: PaginatedResponse<User> }
    POST:
      name: createUser
      roles: [admin]
      body: CreateUserRequest
      response: { 201: User }

events:
  user.created:
    payload: User
    channels: [websocket, redis-pubsub]

streams:
  /chat/{id}/stream:
    type: sse
    chunks: { delta: string, done: bool }

jobs:
  cleanup_sessions:
    schedule: "0 */6 * * *"
    timeout: 300

services:
  database: { type: postgres, version: "16" }
  cache: { type: redis, version: "7" }
  vectors: { type: qdrant }
  jobs: { type: temporal }
```

---

*— End of Implementation Plan —*

*Schnitzel Framework © 2025 — Moinsen Development*
