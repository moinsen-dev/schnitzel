# Schnitzel Examples

This directory contains example Schnitzel schemas demonstrating framework features.

---

## PROMPT DUEL - Competitive Prompt Engineering Game

A multiplayer game where players battle using prompt engineering skills. Features cyberpunk aesthetics, real-time gameplay, and triple AI integration.

### Structure

```
prompt-duel/
├── prd.md                              # Product Requirements Document
├── schema.schnitzel.yaml               # Root schema (global config)
└── features/
    ├── game/schema.yaml                # Matches, rounds, prompts, AI opponents
    └── social/schema.yaml              # Leaderboards, spectating, friends
```

### Features Demonstrated

- **13 Models** with complex relationships
- **25+ REST Endpoints** with auth, roles, pagination
- **5 Real-time Streams** (WebSocket + SSE)
- **15+ Events** with push notifications
- **12 Background Jobs** with scheduling
- **Triple AI Integration** (Executor, Arbiter, Adversary)
- **Vector Embeddings** (prompt analysis)
- **Seasonal Rankings** and achievements

### Quick Start

```bash
schnitzel init my-prompt-duel --from examples/prompt-duel
```

---

## FoodieAI - AI-Powered Restaurant Ordering App

A comprehensive example showcasing ALL Schnitzel schema features.

### Two Versions Available

| Version | Description | Use Case |
|---------|-------------|----------|
| `foodie-ai/` | **Modular** - Split into feature files | Recommended for real projects |
| `foodie-ai-flat.schnitzel.yaml` | **Flat** - Single file (~550 lines) | Quick reference |

### Modular Structure (`foodie-ai/`)

```
foodie-ai/
├── schema.schnitzel.yaml           # Root: global config + imports
└── features/
    ├── restaurants/schema.yaml     # Restaurant, Menu, User models
    ├── orders/schema.yaml          # Order management + tracking
    ├── chat/schema.yaml            # AI assistant
    └── reviews/schema.yaml         # Reviews & ratings
```

### Features Demonstrated

- **12 Models** with relationships and indexes
- **14 REST Endpoints** with auth, roles, pagination
- **3 Real-time Streams** (SSE + WebSocket)
- **5 Events** with push notifications
- **4 Background Jobs** with scheduling
- **5 User Roles** with RBAC permissions
- **AI Integration** (vector embeddings, chat streaming)
- **Integrations** (Stripe, S3, FCM/APNS, i18n)

### Quick Start

```bash
# Initialize from modular example
schnitzel init my-food-app --from examples/foodie-ai

# Or from flat example
schnitzel init my-food-app --from examples/foodie-ai-flat.schnitzel.yaml
```

---

*Schnitzel Framework | Moinsen Development*
