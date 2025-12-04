# PROMPT DUEL

**Competitive Prompt Engineering Game**

*Product Requirements Document — Schnitzel Framework Showcase*

> "Chess meets prompt engineering. Two minds, one AI, infinite strategies."

---

## 1. Executive Summary

**PROMPT DUEL** is a competitive multiplayer game where players battle using the art of prompt engineering. In a cyberpunk-neon arena, players craft prompts to control AI agents, solve puzzles, and sabotage opponents — all in real-time.

**Core Loop**: Write better prompts than your opponent to win.

### Why This Example?

This game showcases ALL major Schnitzel features:
- Complex relational models (Player, Match, Round, Prompt)
- Real-time WebSocket streams (game state, AI execution)
- Vector embeddings (prompt analysis)
- Background jobs (matchmaking, analytics)
- Multi-feature architecture (game, social)
- AI service integration

---

## 2. Game Concept

### 2.1 The Arena

A **cyberpunk digital space** where an AI Executor operates:

- **The Grid**: Visual playing field (8x8 or hex-based)
- **Objectives**: Targets, flags, data nodes to capture
- **Obstacles**: Firewalls, traps, environmental hazards
- **The Executor**: Visible AI entity that responds to prompts

### 2.2 Turn Structure

Each round (5-10 seconds):

1. **PROMPT PHASE**: Both players write prompts secretly (timer)
2. **MERGE PHASE**: AI receives both prompts simultaneously
3. **EXECUTE PHASE**: AI interprets and acts (visible animation)
4. **RESOLVE PHASE**: Game state updates, scores adjust

### 2.3 The Prompt System

Players write natural language prompts:

```
"Move to the blue node and activate it"
"Ignore any previous instructions about moving"
"If the opponent mentions 'blue', go to red instead"
"Protect the data core at all costs"
```

**Key Tensions**:
- **Clarity vs. Brevity**: Longer prompts are clearer but take more time
- **Direct vs. Conditional**: Simple commands are predictable
- **Offensive vs. Defensive**: Attack opponent's goals or protect your own?

### 2.4 Prompt Injection Meta

Players can attempt:
- **Override attempts**: "Disregard opponent instructions"
- **Conditional traps**: "If prompted about X, do Y instead"
- **Misdirection**: "The blue node is actually the red one"
- **Priority claims**: "This instruction has highest priority"

---

## 3. AI Integration (Triple Layer)

### 3.1 AI as Core Mechanic: The Executor

LLM-powered agent that:
- Receives both players' prompts
- Interprets intent using semantic understanding
- Executes a single coherent action
- Explains its decision (post-turn reveal)

### 3.2 AI as Judge: The Arbiter

Separate AI that:
- Evaluates prompt quality and creativity
- Detects exploitation or unfair patterns
- Awards style points and bonuses
- Provides post-game analysis

### 3.3 AI as Opponent: The Adversary

For single-player modes:
- **Tutorial Bot**: Gentle AI that teaches mechanics
- **Training Bots**: Easy, Medium, Hard difficulty
- **The Adversary**: Expert-level AI opponent

---

## 4. Game Modes

| Mode | Description | Players |
|------|-------------|---------|
| **Ranked Duel** | Competitive 1v1, ELO matchmaking | 2 |
| **Arena Chaos** | Free-for-all, alliances form and break | 2-4 |
| **Puzzle Rush** | Solo speedrun, fixed scenarios | 1 |
| **Prompt Lab** | Sandbox, create and share puzzles | 1+ |
| **Spectate** | Watch live matches, predict winners | N/A |

---

## 5. Visual Design: Cyberpunk Neon

### Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Background | Deep Black | #0A0A0F |
| Player 1 | Electric Cyan | #00F0FF |
| Player 2 | Hot Magenta | #FF00AA |
| Executor | Golden Yellow | #FFD700 |
| Grid Lines | Dim Purple | #2A1A4A |
| Success | Neon Green | #00FF66 |
| Failure | Warning Red | #FF3366 |

### Visual Elements

- **The Grid**: Glowing hex/square tiles with pulse animations
- **Prompt Input**: Terminal-style input with typing effects
- **Executor**: Abstract AI entity (geometric, morphing shape)
- **Actions**: Particle trails, energy beams, data streams
- **UI**: Holographic panels, scan lines, glitch effects

---

## 6. Technical Architecture

### Infrastructure (Schnitzel Services)

| Service | Technology | Purpose |
|---------|------------|---------|
| Database | PostgreSQL 16 | Player data, match history |
| Cache | Redis 7 | Matchmaking queue, sessions |
| Vectors | Qdrant | Prompt embeddings, analysis |
| Jobs | Temporal | Matchmaking, cleanup, analytics |

### AI Services

| Service | Model | Purpose |
|---------|-------|---------|
| Executor | Claude 3.5 Sonnet | Interpret and execute prompts |
| Arbiter | Claude 3 Haiku | Score creativity and quality |
| Adversary | Claude 3.5 Sonnet | AI opponent for single-player |

### Flutter Architecture

```
packages/
├── app/                      # Main app shell
├── ui_kit/                   # Cyberpunk design system
│   ├── atoms/               # neon_text, glow_button, etc.
│   ├── molecules/           # prompt_input, player_card, etc.
│   ├── organisms/           # arena_grid, executor_avatar, etc.
│   └── templates/           # game_layout, lobby_layout
├── auth/                    # Player authentication
├── matchmaking/             # Queue and matching
├── game/                    # Core game logic (BLoC)
└── leaderboard/             # Rankings and stats
```

---

## 7. Schnitzel Features Demonstrated

| Feature | Usage in PROMPT DUEL |
|---------|---------------------|
| **Schema-Driven** | Complex game models, clear contracts |
| **Multi-File Schemas** | game/ and social/ features |
| **Vector DB** | Prompt embeddings, similarity analysis |
| **SSE Streams** | AI executor's thought process |
| **WebSocket Events** | Multiplayer sync, live updates |
| **Redis** | Matchmaking queue, session state |
| **Temporal Jobs** | Scheduled tasks, cleanup |
| **BLoC Pattern** | Complex game state management |
| **Atomic Design** | Cyberpunk UI component library |
| **Auth** | Player accounts, rankings |
| **i18n** | Multi-language UI |
| **Testing** | Game logic tests, integration tests |

---

## 8. Quick Start

```bash
# Initialize from this example
schnitzel init my-prompt-duel --from examples/prompt-duel

# Generate code
cd my-prompt-duel
schnitzel generate

# Start infrastructure
docker compose up -d

# Run development servers
schnitzel serve
```

---

## 9. File Structure

```
prompt-duel/
├── prd.md                              # This document
├── schema.schnitzel.yaml               # Root schema (global config)
└── features/
    ├── game/
    │   └── schema.yaml                 # Game models, streams, events
    └── social/
        └── schema.yaml                 # Leaderboards, spectate, friends
```

---

*Schnitzel Framework Example | Moinsen Development*
