# Schnitzel Examples

This directory contains example Schnitzel schemas demonstrating framework features.

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
