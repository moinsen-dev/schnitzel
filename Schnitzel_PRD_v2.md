# 🍖 SCHNITZEL

**Schema-Driven Full-Stack Framework**

*Product Requirements Document — Version 2.0 | December 2025*

> *"One Schema to Rule Them All"*
>
> **AI-First • Schema-Driven • Batteries Included**

---

## 1. Executive Summary

Schnitzel is a meta-framework that eliminates the friction between Flutter frontends and Python (FastAPI) backends through a unified schema language. Instead of maintaining separate API contracts, data models, and documentation across platforms, developers define their domain once in a declarative YAML schema. Schnitzel then generates type-safe code for both sides, complete with AI-powered tooling that understands the entire system.

**The Name:** "Schnitzel" is a playful German wordplay on "Schnittstelle" (interface) — because at its core, this framework is all about interfaces: between frontend and backend, between developers and AI, between schema and code.

---

## 2. Problem Statement

### 2.1 Current Pain Points

- **Schema Drift:** Frontend Dart models diverge from backend Pydantic models over time, causing runtime errors.
- **Boilerplate Hell:** Every new endpoint requires changes in 4+ places: FastAPI route, Pydantic model, Dart model, API client.
- **AI Blindness:** AI coding assistants lack context about the full-stack architecture, leading to inconsistent suggestions.
- **Infrastructure Complexity:** Setting up Redis, Postgres, vector databases, and job queues requires significant DevOps knowledge.
- **Starter Template Decay:** Traditional starter templates become outdated; dependencies drift, breaking changes accumulate.

### 2.2 Target Users

- Solo developers and small teams building Flutter + Python applications
- Teams using AI coding assistants (Claude, Cursor, GitHub Copilot)
- Developers who prefer declarative, schema-first architecture

---

## 3. Product Vision

### 3.1 Core Philosophy

**Schema as Single Source of Truth:** One YAML file defines models, endpoints, events, and streams. Everything else is generated.

**Always Fresh:** No pre-baked templates. Init scripts run `flutter create`, `poetry init`, etc. at runtime, ensuring latest versions.

**AI-Native:** Every component is designed for AI comprehension. Auto-generated CLAUDE.md, MCP servers, and context files.

**Batteries Included:** Docker Compose with Redis, Postgres, Qdrant (vector DB), and Temporal (job scheduler) pre-configured.

### 3.2 The Schnitzel Promise

1. Define your domain in `schema.schnitzel.yaml`
2. Run `schnitzel generate`
3. Get type-safe Flutter + FastAPI code, Docker setup, and AI tooling

---

## 4. The Schnitzel Schema Language

The schema language is a YAML-based DSL (Domain-Specific Language) that defines the entire contract between frontend and backend. It is designed to be human-readable, AI-parseable, and comprehensive enough to generate complete implementations.

### 4.1 Schema File Structure

```yaml
# schema.schnitzel.yaml
schnitzel: "1.0"

meta:
  name: "MyApp"
  org: "com.example"
  description: "My awesome application"

models:      # Domain models (Section 4.2)
endpoints:   # REST API definitions (Section 4.3)
events:      # Webhook-style events (Section 4.4)
streams:     # SSE/WebSocket streams (Section 4.5)
jobs:        # Scheduled tasks (Section 4.6)
services:    # Infrastructure config (Section 4.7)
```

### 4.2 Models Definition

Models define the domain entities shared between frontend and backend. Each model generates a Pydantic class (Python) and a Freezed class (Dart).

```yaml
models:
  User:
    description: "Application user"
    fields:
      id: { type: uuid, primary: true }
      email: { type: string, unique: true, format: email }
      name: { type: string, min: 1, max: 100 }
      role: { type: enum, values: [admin, user, guest], default: user }
      created_at: { type: datetime, auto: create }
      updated_at: { type: datetime, auto: update }
    relations:
      posts: { type: hasMany, model: Post }
    indexes:
      - [email]
```

#### Supported Field Types

| Type | Python | Dart |
|------|--------|------|
| string | str | String |
| int | int | int |
| float | float | double |
| bool | bool | bool |
| uuid | UUID | String (with uuid validation) |
| datetime | datetime | DateTime |
| json | dict[str, Any] | Map<String, dynamic> |
| list<T> | list[T] | List<T> |
| enum | Enum class | enum |
| vector | list[float] | List<double> (embedding) |

### 4.3 Endpoints Definition

Endpoints define REST API routes with full request/response specifications.

```yaml
endpoints:
  /users:
    GET:
      name: listUsers
      description: "Get paginated list of users"
      auth: required
      query:
        page: { type: int, default: 1 }
        limit: { type: int, default: 20, max: 100 }
        search: { type: string, optional: true }
      response:
        200: { type: PaginatedResponse<User> }
        401: { type: ErrorResponse }

    POST:
      name: createUser
      description: "Create a new user"
      auth: required
      roles: [admin]
      body: CreateUserRequest
      response:
        201: { type: User }
        400: { type: ValidationError }

  /users/{id}:
    params:
      id: { type: uuid }
    GET:
      name: getUser
      response:
        200: { type: User }
```

### 4.4 Events Definition (Webhooks)

Events define push-based notifications from backend to frontend, similar to webhooks but with type safety.

```yaml
events:
  user.created:
    description: "Fired when a new user is created"
    payload: User
    channels: [websocket, redis-pubsub]

  order.status_changed:
    description: "Fired when order status updates"
    payload:
      order_id: uuid
      old_status: string
      new_status: string
    channels: [websocket]
```

### 4.5 Streams Definition (SSE/WebSocket)

Streams define real-time data flows for continuous updates, such as AI chat responses or live feeds.

```yaml
streams:
  /chat/{conversation_id}/stream:
    name: chatStream
    description: "Stream AI chat responses"
    type: sse  # or websocket
    auth: required
    params:
      conversation_id: { type: uuid }
    input: ChatMessage
    chunks:
      delta: { type: string }      # Text chunk
      done: { type: bool }         # Stream complete
      metadata: { type: json, optional: true }
```

### 4.6 Jobs Definition (Scheduled Tasks)

Jobs define recurring or scheduled background tasks managed by Temporal.

```yaml
jobs:
  cleanup_expired_sessions:
    description: "Remove expired user sessions"
    schedule: "0 */6 * * *"  # Every 6 hours
    timeout: 300  # seconds
    retry:
      max_attempts: 3
      backoff: exponential

  sync_embeddings:
    description: "Update vector embeddings for search"
    schedule: "0 2 * * *"  # Daily at 2 AM
    timeout: 3600
```

### 4.7 Services Configuration

Services define which infrastructure components to include in the Docker Compose setup.

```yaml
services:
  database:
    type: postgres
    version: "16"
    extensions: [pgvector, uuid-ossp]

  cache:
    type: redis
    version: "7"
    features: [pubsub, streams]

  vectors:
    type: qdrant
    collections:
      - name: documents
        dimensions: 1536
        distance: cosine

  jobs:
    type: temporal
```

### 4.8 Migrations & Schema Evolution

Schnitzel tracks schema changes and automatically generates database migrations. The system uses a snapshot-based approach to detect changes between schema versions.

#### Schema Versioning

```
.schnitzel/
├── snapshots/
│   ├── 001_initial.yaml
│   ├── 002_add_posts.yaml
│   └── 003_user_roles.yaml
└── migrations/
    ├── 001_initial.sql
    ├── 002_add_posts.sql
    └── 003_user_roles.sql
```

#### Migration CLI Commands

```bash
# Detect changes and generate migration
schnitzel migrate diff --name "add_user_avatar"

# Apply pending migrations
schnitzel migrate up

# Rollback last migration
schnitzel migrate down

# Show migration status
schnitzel migrate status

# Preview SQL without applying
schnitzel migrate diff --dry-run
```

#### Change Detection

| Change Type | Auto-Migration | Requires Review |
|-------------|----------------|-----------------|
| Add model | CREATE TABLE | No |
| Add field | ALTER TABLE ADD | If NOT NULL w/o default |
| Remove field | ALTER TABLE DROP | Yes (data loss) |
| Rename field | ALTER TABLE RENAME | Yes |
| Change type | ALTER COLUMN TYPE | Yes (potential loss) |
| Add index | CREATE INDEX | No |
| Add relation | ADD FOREIGN KEY | If data exists |

#### Breaking Change Detection

Schnitzel validates schema changes against connected Flutter clients to detect breaking API changes before deployment.

```bash
# Check for breaking changes
schnitzel validate --breaking

# Output example:
⚠️  BREAKING: Field 'User.email' type changed (string → int)
⚠️  BREAKING: Endpoint '/users' removed
✓  SAFE: Field 'User.avatar' added (optional)
```

#### API Versioning Strategy

For breaking changes, Schnitzel supports API versioning to maintain backwards compatibility:

```yaml
endpoints:
  /v1/users:           # Legacy version
    deprecated: true
    sunset: "2025-06-01"
    GET:
      response: { 200: UserV1 }

  /v2/users:           # Current version
    GET:
      response: { 200: User }
```

### 4.9 Multi-File Schema Organization

For large projects, Schnitzel supports splitting the schema across multiple files. This enables teams to work independently on different features while maintaining a single source of truth.

```yaml
# schema.schnitzel.yaml (root)
schnitzel: "1.0"

meta:
  name: "MyApp"
  org: "com.example"

imports:
  - features/auth/schema.yaml
  - features/billing/schema.yaml
  - features/content/schema.yaml
  - features/notifications/schema.yaml
```

Each imported file follows the same schema structure but defines only its own domain slice.

### 4.10 Feature Packages

Features represent logical boundaries within the application. Each feature can generate its own Flutter package, enabling modular development where teams own specific domains.

```yaml
features:
  auth:
    description: "User authentication and sessions"
    flutter_package: true  # → packages/feature_auth/
    models: [User, Session, AuthToken]
    exports: [User]  # Models other features can reference

  billing:
    flutter_package: true
    models: [Subscription, Invoice, PaymentMethod]
    depends_on: [auth]  # Can reference auth.User

  content:
    flutter_package: true
    models: [Post, Comment, Category]
    depends_on: [auth]

# App shell imports and composes features
app:
  shell: material  # or: cupertino, adaptive
  features: [auth, billing, content]
```

Feature boundaries are soft — features share an app shell and can reference exported models from dependencies. This enables incremental adoption where teams start with a monolith and extract features as needed.

### 4.11 Authentication (Built-in)

Authentication is a first-class citizen in Schnitzel. The framework generates complete auth flows for both Flutter and FastAPI, eliminating one of the most common friction points in app development.

```yaml
auth:
  providers:
    - email_password
    - magic_link
    - google
    - apple
    - github

  session:
    type: jwt
    access_expiry: 900      # 15 minutes
    refresh_expiry: 604800  # 7 days
    refresh: true

  mfa: optional  # or: required, disabled

  password_policy:
    min_length: 8
    require_uppercase: true
    require_number: true
```

#### RBAC (Role-Based Access Control)

```yaml
roles:
  admin:
    permissions: ["*"]  # Full access

  editor:
    permissions:
      - posts:create
      - posts:update:own  # Can only edit own posts
      - posts:delete:own

  viewer:
    permissions:
      - posts:read
```

### 4.12 Environments

Schnitzel supports environment-specific configurations for development, staging, and production. Environment variables and feature flags are managed declaratively.

```yaml
environments:
  dev:
    api_url: "http://localhost:${PORT_API}"
    debug: true
    features: [debug_panel, mock_payments, seed_data]
    secrets: .env.dev

  staging:
    api_url: "https://staging-api.example.com"
    debug: false
    features: [analytics, error_tracking]

  production:
    api_url: "https://api.example.com"
    debug: false
    features: [analytics, error_tracking, rate_limiting]
```

### 4.13 Deployment Configuration

Schnitzel abstracts deployment complexity. For local development, it generates Docker Compose with automatic port management. For production, it targets modern PaaS platforms.

#### Port Collision Prevention

Developers often work on multiple projects simultaneously. Schnitzel automatically assigns unique ports based on the project name hash, preventing conflicts:

```yaml
meta:
  name: myapp
  port_mode: auto  # or: fixed

# Auto-generated ports (hash of 'myapp'):
# API:      8100
# Postgres: 5500
# Redis:    6400
# Qdrant:   6350
```

Alternatively, Schnitzel can set up a Traefik reverse proxy for domain-based routing (e.g., `myapp.localhost`, `myapp-api.localhost`).

#### Deployment Targets

```yaml
deployment:
  local:
    type: docker-compose
    proxy: traefik  # optional: enables *.localhost routing

  production:
    target: fly  # or: railway, render, docker-swarm
    region: fra  # Frankfurt
    scaling:
      min: 1
      max: 10
    resources:
      cpu: shared-cpu-1x
      memory: 512mb
    health_check: /health
    ssl: auto
```

### 4.14 Common Integrations

Real-world applications require common capabilities beyond CRUD. Schnitzel provides declarative configuration for frequently needed integrations.

#### File Storage

```yaml
storage:
  provider: s3  # or: minio, gcs, local
  buckets:
    avatars:
      public: true
      max_size: 5mb
      allowed_types: [image/jpeg, image/png, image/webp]
    documents:
      public: false
      max_size: 50mb
```

#### Push Notifications

```yaml
notifications:
  push:
    fcm: true     # Firebase Cloud Messaging (Android)
    apns: true    # Apple Push Notification Service
  email:
    provider: resend  # or: sendgrid, ses
    templates: true   # Generate email templates
```

#### Internationalization (i18n)

```yaml
i18n:
  default_locale: en
  supported: [en, de, fr, es]
  fallback: en
  # Generates: Flutter ARB files + backend message catalogs
```

#### Offline Support & Sync

```yaml
offline:
  enabled: true
  storage: drift  # SQLite via Drift
  sync_strategy: last_write_wins  # or: merge, manual
  models:  # Which models to cache locally
    - User
    - Post
```

#### Error Contracts

Standardized error responses ensure consistent error handling across the entire stack:

```yaml
errors:
  format: rfc7807  # Problem Details standard
  codes:
    AUTH_INVALID_CREDENTIALS:
      status: 401
      message: "Invalid email or password"
    RESOURCE_NOT_FOUND:
      status: 404
      message: "The requested resource was not found"
    RATE_LIMIT_EXCEEDED:
      status: 429
      message: "Too many requests"
```

#### Observability

```yaml
observability:
  logging:
    format: json
    level: info  # debug in dev
  error_tracking:
    provider: sentry
  metrics:
    enabled: true
    endpoint: /metrics  # Prometheus format
```

### 4.15 Type-Safe Field Access

Schnitzel generates static field name constants for every model. This eliminates magic strings and ensures compile-time errors when fields are renamed or removed — not runtime surprises.

#### Generated Dart Constants

```dart
// generated/models/user.fields.dart
abstract class UserFields {
  static const String id = 'id';
  static const String email = 'email';
  static const String name = 'name';
  static const String role = 'role';
  static const String createdAt = 'created_at';
}

// Usage - compile error if field renamed/removed:
query.where(UserFields.email, isEqualTo: email);
final name = json[UserFields.name];
sortBy(UserFields.createdAt);
```

#### Generated Python Constants

```python
# generated/models/user_fields.py
class UserFields:
    ID = "id"
    EMAIL = "email"
    NAME = "name"
    ROLE = "role"
    CREATED_AT = "created_at"

# Usage:
query.filter_by(**{UserFields.EMAIL: email})
data.get(UserFields.NAME)
```

#### Endpoint & Event Constants

The same pattern applies to endpoints and events:

```dart
// Dart
abstract class Endpoints {
  static const users = '/users';
  static String user(String id) => '/users/$id';
}

abstract class Events {
  static const userCreated = 'user.created';
  static const orderStatusChanged = 'order.status_changed';
}
```

### 4.16 Testing as Core DNA

Testing is not an afterthought in Schnitzel — it's part of the generation pipeline. Every model, endpoint, and service gets corresponding test infrastructure automatically.

#### Testing Configuration

```yaml
testing:
  generate:
    factories: true      # Test data builders
    mocks: true          # Mockito mocks for services
    fakes: true          # In-memory implementations
    fixtures: true       # JSON fixtures from schema
    contract_tests: true # API contract validation

  coverage:
    minimum: 80
    exclude: [generated/*]

  seed:
    dev: seed/dev.yaml    # Dev environment data
    test: seed/test.yaml  # Isolated test data
```

#### Generated Factories (Dart)

```dart
// generated/testing/user_factory.dart
class UserFactory {
  static User create({
    String? id,
    String? email,
    String? name,
    UserRole? role,
  }) => User(
    id: id ?? Faker.uuid(),
    email: email ?? Faker.email(),
    name: name ?? Faker.name(),
    role: role ?? UserRole.user,
  );

  static List<User> createList(int count) =>
    List.generate(count, (_) => create());
}

// Usage in tests:
final user = UserFactory.create(name: 'Test User');
final admins = UserFactory.createList(5).map((u) => u.copyWith(role: UserRole.admin));
```

#### Generated Factories (Python)

```python
# generated/testing/factories.py
class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    email = factory.Faker('email')
    name = factory.Faker('name')
    role = UserRole.user

# Usage:
user = UserFactory.create(name='Test User')
```

#### Generated Mocks & Fakes

```dart
// generated/testing/mocks.dart
@GenerateMocks([UserRepository, AuthService, ApiClient])
class Mocks {}

// generated/testing/fakes.dart
class FakeUserRepository implements UserRepository {
  final _users = <String, User>{};

  @override
  Future<User?> findById(String id) async => _users[id];

  @override
  Future<User> save(User user) async {
    _users[user.id] = user;
    return user;
  }
  // ... all repository methods
}
```

#### Contract Tests

Contract tests validate that Flutter and FastAPI agree on API shapes. Generated automatically from the schema:

```python
# generated/testing/contracts/test_user_contract.py
def test_get_users_response_matches_schema():
    response = client.get('/users')
    assert response.status_code == 200
    validate_schema(response.json(), PaginatedUserResponse)

def test_create_user_validates_input():
    response = client.post('/users', json={'invalid': 'data'})
    assert response.status_code == 422  # Validation error
```

#### Seed Data

```yaml
# seed/dev.yaml
users:
  - email: admin@example.com
    name: Admin User
    role: admin
    password: dev-password-123

  - $factory: User
    $count: 50  # Generate 50 random users

posts:
  - $factory: Post
    $count: 100
    author: $ref:users  # Reference seeded users
```

#### CLI Testing Commands

```bash
schnitzel test              # Run all tests
schnitzel test --flutter    # Flutter tests only
schnitzel test --backend    # Backend tests only
schnitzel test --contracts  # Contract tests only
schnitzel test --coverage   # With coverage report

schnitzel seed              # Seed dev database
schnitzel seed --env test   # Seed test database
```

---

## 5. CLI Specification

The Schnitzel CLI is the primary interface for project initialization, code generation, and development workflows.

### 5.1 Installation

```bash
# Via pip (recommended)
pip install schnitzel-cli

# Via pipx (isolated environment)
pipx install schnitzel-cli
```

### 5.2 Command Reference

#### schnitzel init

Initialize a new Schnitzel project. Runs framework setup commands at runtime.

```bash
schnitzel init <project-name> [options]

Options:
  --org           Organization identifier (e.g., com.example)
  --template      Starter template (minimal, full, ai-chat)
  --no-flutter    Skip Flutter app creation
  --no-backend    Skip Python backend creation
  --ai-provider   AI provider integration (openai, anthropic, local)
  --verbose       Show detailed output
```

**What it does:** Executes `flutter create --org <org>`, `poetry init`, creates Docker Compose files, generates initial schema, and sets up AI tooling.

#### schnitzel generate

Generate code from the schema file.

```bash
schnitzel generate [options]

Options:
  --schema        Path to schema file (default: schema.schnitzel.yaml)
  --target        Generation target (all, flutter, python, docker, ai)
  --watch         Watch schema for changes and regenerate
  --dry-run       Show what would be generated without writing
```

#### schnitzel serve

Start development servers.

```bash
schnitzel serve [options]

Options:
  --backend-only  Start only the backend services
  --port          API port (default: 8000)
  --reload        Enable hot reload
```

#### schnitzel add

Add components to the schema interactively or via CLI.

```bash
schnitzel add <type> <name> [options]

Types: model, endpoint, event, stream, job

Examples:
  schnitzel add model Product
  schnitzel add endpoint /products --methods GET,POST
  schnitzel add stream /notifications --type websocket
```

#### schnitzel validate

Validate schema and check for inconsistencies.

```bash
schnitzel validate [options]

Options:
  --strict        Fail on warnings
  --fix           Auto-fix common issues
  --breaking      Check for breaking API changes
```

#### schnitzel migrate

Database migration management.

```bash
schnitzel migrate <command> [options]

Commands:
  diff            Generate migration from schema changes
  up              Apply pending migrations
  down            Rollback last migration
  status          Show migration status
  reset           Reset database (dev only)

Options:
  --name          Migration name (for diff)
  --dry-run       Preview SQL without applying
  --force         Skip confirmation prompts
```

#### schnitzel test

Run tests across Flutter and backend.

```bash
schnitzel test [options]

Options:
  --flutter       Run Flutter tests only
  --backend       Run backend tests only
  --contracts     Run contract tests only
  --coverage      Generate coverage report
  --watch         Watch mode for TDD
```

#### schnitzel seed

Seed database with test data.

```bash
schnitzel seed [options]

Options:
  --env           Environment (dev, test, staging)
  --reset         Clear existing data before seeding
  --file          Custom seed file path
```

#### schnitzel ai

AI tooling commands.

```bash
schnitzel ai context    # Regenerate CLAUDE.md and AI context files
schnitzel ai mcp        # Generate/update MCP server
schnitzel ai prompt     # Generate task-specific prompts
```

---

## 6. AI-First Architecture

Every Schnitzel project is designed to be understood and modified by AI coding assistants. This is not an afterthought but a core design principle.

### 6.1 Auto-Generated CLAUDE.md

Every project includes a dynamically generated CLAUDE.md file that provides complete context to AI assistants.

```markdown
# CLAUDE.md (Auto-generated)

## Project Overview
This is a Schnitzel-powered project with Flutter frontend and FastAPI backend.

## Schema Location
The single source of truth is `schema.schnitzel.yaml`.

## Available Models
- User: Application user with email, name, role
- Post: Blog post with title, content, author

## Available Endpoints
- GET /users - List users (paginated)
- POST /users - Create user (admin only)

## Development Commands
- `schnitzel generate` - Regenerate code from schema
- `schnitzel serve` - Start dev servers
- `docker compose up` - Start infrastructure
```

### 6.2 MCP Server Generation

Schnitzel auto-generates an MCP (Model Context Protocol) server that exposes the project's schema and operations to AI assistants like Claude.

- **Schema Tools:** Query models, endpoints, and relationships
- **Code Generation:** AI can request code generation for new components
- **Validation:** Check schema consistency before changes
- **Documentation:** Access auto-generated API docs

### 6.3 AI Context Files

```
.schnitzel/
├── ai-context.json      # Structured project metadata
├── schema-summary.md    # Human-readable schema overview
├── mcp-server/          # Generated MCP server
│   ├── server.py
│   └── tools.py
└── prompts/
    ├── add-feature.md   # Prompt for adding features
    ├── fix-bug.md       # Prompt for debugging
    └── refactor.md      # Prompt for refactoring
```

---

## 7. Technical Architecture

### 7.1 Project Structure

```
myapp/
├── schema.schnitzel.yaml    # Single source of truth
├── CLAUDE.md                # AI instructions
├── docker-compose.yaml      # Infrastructure
│
├── app/                     # Flutter application
│   ├── lib/
│   │   ├── generated/       # Auto-generated code
│   │   │   ├── models/      # Freezed models
│   │   │   ├── api/         # API client
│   │   │   └── events/      # Event handlers
│   │   └── src/             # Custom code
│   └── pubspec.yaml
│
├── backend/                 # Python backend
│   ├── app/
│   │   ├── generated/       # Auto-generated code
│   │   │   ├── models.py    # Pydantic models
│   │   │   ├── routes.py    # FastAPI routes
│   │   │   └── events.py    # Event definitions
│   │   └── src/             # Custom code
│   └── pyproject.toml
│
└── .schnitzel/              # AI tooling
    ├── mcp-server/
    └── prompts/
```

### 7.2 Generator Pipeline

The generation process follows a deterministic pipeline that ensures consistency across all outputs.

1. **Parse:** Load and validate schema.schnitzel.yaml
2. **Resolve:** Resolve model references, validate relationships
3. **Transform:** Convert to intermediate representation (IR)
4. **Generate:** Run language-specific generators
5. **Post-process:** Format code, run build_runner (Dart), update AI context

### 7.3 Infrastructure Stack

| Service | Technology | Purpose |
|---------|------------|---------|
| API | FastAPI | REST + SSE endpoints |
| Database | PostgreSQL 16 | Primary data store |
| Cache | Redis 7 | Caching, pub/sub, sessions |
| Vector DB | Qdrant | Embeddings, RAG search |
| Jobs | Temporal | Scheduled tasks, workflows |

---

## 8. Non-Functional Requirements

### 8.1 Performance

- Code generation completes in under 5 seconds for schemas with up to 50 models
- Generated API client adds less than 50KB to Flutter bundle
- MCP server responds to queries in under 100ms

### 8.2 Compatibility

- Flutter: 3.19+ (Dart 3.3+)
- Python: 3.11+
- Docker: 24.0+
- Node.js: 18+ (for MCP server)

### 8.3 Extensibility

- Plugin system for custom generators
- Custom field types via type extensions
- Template overrides for generated code

---

## 9. Development Roadmap

### Phase 1: Foundation (MVP)
*Duration: 6 weeks*

- Schema parser and validator
- Basic model generation (Pydantic + Freezed)
- REST endpoint generation
- CLI: init, generate commands
- CLAUDE.md generation

### Phase 2: Infrastructure
*Duration: 4 weeks*

- Docker Compose generation
- Redis integration
- PostgreSQL with migrations
- Basic auth scaffolding

### Phase 3: Real-Time
*Duration: 4 weeks*

- Event system (WebSocket + Redis pub/sub)
- SSE streaming support
- Flutter stream handlers

### Phase 4: AI Integration
*Duration: 4 weeks*

- MCP server generation
- Qdrant vector DB integration
- AI-aware prompts and context
- Embedding pipeline scaffolding

### Phase 5: Jobs & Polish
*Duration: 4 weeks*

- Temporal job scheduler
- Plugin system
- Documentation site
- Starter templates

---

## 10. Appendix

### 10.1 Complete Schema Example

```yaml
# schema.schnitzel.yaml - Complete Example
schnitzel: "1.0"

meta:
  name: "BlogApp"
  org: "com.example"
  description: "AI-powered blogging platform"

models:
  User:
    fields:
      id: { type: uuid, primary: true }
      email: { type: string, unique: true }
      name: { type: string }

  Post:
    fields:
      id: { type: uuid, primary: true }
      title: { type: string }
      content: { type: string }
      embedding: { type: vector, dimensions: 1536 }
    relations:
      author: { type: belongsTo, model: User }

endpoints:
  /posts:
    GET:
      name: listPosts
      response: { 200: PaginatedResponse<Post> }

streams:
  /posts/{id}/ai-enhance:
    type: sse
    chunks: { delta: string, done: bool }

services:
  database: { type: postgres }
  cache: { type: redis }
  vectors: { type: qdrant }
```

### 10.2 Glossary

- **Schema:** The YAML file defining the entire project contract
- **Generator:** Component that transforms schema to platform-specific code
- **MCP:** Model Context Protocol - AI assistant integration standard
- **SSE:** Server-Sent Events - one-way streaming from server to client
- **Freezed:** Dart code generation library for immutable data classes
- **Pydantic:** Python data validation library

---

*— End of Document —*

*Schnitzel Framework © 2025*
