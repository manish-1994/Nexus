# NEXUS Master Context

> **Single Source of Truth** for the NEXUS project. Read this first.

---

## Project Overview

**NEXUS** is a local-first AI Operating System — a desktop application that provides a unified interface for managing AI agents, providers, tools, conversations, and workflows. It runs entirely on your machine with optional cloud provider integration.

**Core Philosophy**: *Your AI, Your Data, Your Control*

---

## Vision

Build the **definitive local AI workspace** that:
- Runs 100% locally by default (Ollama, LM Studio, local models)
- Seamlessly integrates cloud providers (Gemini, OpenRouter, OpenAI, Anthropic, etc.)
- Provides a **provider-agnostic** agent runtime with tool use, memory, and multi-agent orchestration
- Features a **glassmorphism HUD interface** designed for AI-first interaction
- Serves as a platform for **AI skills/plugins** (browser, terminal, code execution, file ops, search, memory)

---

## Goals

| Goal | Status |
|------|--------|
| Local-first architecture with zero required cloud dependencies | ✅ |
| Provider abstraction layer (15+ providers supported) | ✅ |
| Agent framework with execution lifecycle, retry/fallback, streaming | ✅ |
| Universal Tool Runtime with 6 built-in tools | ✅ |
| Glassmorphism UI with motion, depth, HUD design | 🚧 |
| Conversation management with optimistic updates | ✅ |
| Long-term memory system (vector embeddings) | 📋 Planned |
| Multi-agent orchestration | 📋 Planned |
| GitHub Skill system (installable AI capabilities) | 📋 Planned |
| Cross-platform desktop app (Tauri/Electron) | 📋 Planned |

---

## Current Version

| Component | Version |
|-----------|---------|
| Backend | 0.1.0 (NEXUS V3) |
| Frontend | 0.1.0 |
| Database | SQLite (SQLAlchemy ORM) |
| Architecture Version | 3.0 |

---

## Current Phase

**Phase 7 — Universal Tool Runtime** ✅ **COMPLETED**

All 141 tests passing (82 Phase 6 + 59 Phase 7).

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                        UI LAYER                               │
│  React 18 + TypeScript + Tailwind + Framer Motion            │
│  Pages → Components → Hooks → Stores → API Client            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                                │
│  FastAPI + Pydantic v2 + SQLAlchemy 2.0                      │
│  /api/v1/agents | /chat | /providers | /tools | /runtime     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                              │
│  AgentExecutionManager ←→ ToolManager ←→ AIRuntime           │
│  AgentService | ChatService | ProviderService | UsageTracker │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   RUNTIME LAYERS                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Agent       │  │ Tool        │  │ Provider            │  │
│  │ Runtime     │  │ Runtime     │  │ Runtime             │  │
│  │             │  │             │  │                     │  │
│  │ State       │  │ Registry    │  │ BaseProvider        │  │
│  │ Machine     │  │ Manager     │  │ 15+ Implementations │  │
│  │ Prompt      │  │ Permissions │  │ Health/Capabilities │  │
│  │ Builder     │  │ Context     │  │ Model Discovery     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                │
│  SQLite + SQLAlchemy ORM + Alembic Migrations                │
│  Agents | Conversations | Messages | Executions | Providers  │
│  Models | Capabilities | Usage | Settings                    │
└─────────────────────────────────────────────────────────────┘
```

**Dependency Direction**: UI → API → Services → Runtimes → Data (strictly downward)

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.109+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.0+ | Validation/schemas |
| Alembic | 1.13+ | Migrations |
| Uvicorn | 0.27+ | ASGI server |
| httpx | 0.26+ | Async HTTP client |
| pytest | 7.4+ | Testing |
| pytest-asyncio | 0.23+ | Async testing |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2+ | UI framework |
| TypeScript | 5.3+ | Type safety |
| Vite | 5.0+ | Build tool |
| Tailwind CSS | 3.4+ | Styling |
| Framer Motion | 10.16+ | Animations |
| TanStack Query | 5.0+ | Server state |
| Zustand | 4.4+ | Client state |
| React Router | 6.20+ | Routing |
| Lucide React | 0.29+ | Icons |

### Providers Supported (15+)
- **Local**: Ollama, LM Studio
- **Cloud**: OpenAI, Anthropic, Gemini, OpenRouter, Groq, Together AI, Perplexity, xAI, Mistral, Cohere, Azure OpenAI, NVIDIA NIM, DeepSeek, Custom OpenAI-compatible

---

## Folder Structure

```
NEXUS/
├── backend/
│   ├── agents/           # Agent abstraction & prompt building
│   ├── api/              # FastAPI routes (agents, chat, providers, tools, runtime)
│   ├── models/           # SQLAlchemy models
│   ├── providers/        # Provider implementations (15+)
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic (execution, AI runtime, etc.)
│   ├── tools/            # Tool Runtime (registry, manager, builtins)
│   ├── utils/            # Helpers, exceptions, security
│   ├── tests/            # Unit/integration tests
│   ├── alembic/          # Database migrations
│   ├── app.py            # FastAPI app entry
│   ├── config.py         # Settings
│   ├── database.py       # DB init & seeding
│   └── migrations.py     # Custom migration runner
├── frontend/
│   ├── src/
│   │   ├── api/          # API client & types
│   │   ├── components/   # React components (Agents, Chat, Core, Layout, Providers)
│   │   ├── hooks/        # Custom React hooks
│   │   ├── pages/        # Page components
│   │   ├── services/     # Frontend services
│   │   ├── stores/       # Zustand stores
│   │   ├── types/        # TypeScript types
│   │   └── utils/        # Utilities
│   └── package.json
├── docs/
│   ├── AI_CONTEXT/       # ← THIS DIRECTORY (AI-first documentation)
│   ├── api/              # API reference
│   ├── implementation/   # Phase implementation docs
│   ├── reports/          # Status, changelog, test reports
│   ├── roadmap/          # Future phases
│   ├── setup/            # Development setup
│   └── testing/          # Test plans/results
├── plans/                # Architecture plans per phase
├── scripts/              # Dev scripts (dev.js, etc.)
└── data/                 # SQLite database (gitignored)
```

---

## Completed Phases

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 0 | Foundation | ✅ | Project setup, FastAPI, React, Tailwind, SQLite, basic config |
| 1 | Provider Runtime | ✅ | BaseProvider, 15 provider implementations, health checks, model discovery |
| 2 | Agent Framework | ✅ | Agent CRUD, AgentManager, PromptBuilder, AgentRegistry, testing |
| 3 | AI Runtime | ✅ | AIRuntime gateway, unified chat/stream endpoints, provider resolution |
| 4 | Chat System | ✅ | Conversations, messages, streaming SSE, optimistic updates |
| 5 | Application Shell | ✅ | Layout, Sidebar, TopBar, StatusBar, glassmorphism theme, pages |
| 6 | Agent Runtime | ✅ | ExecutionManager, state machine, retry/fallback, streaming, cancellation, PromptBuilder v2 |
| 7 | Tool Runtime | ✅ | ToolRegistry, ToolManager, ExecutionContext, 6 built-in tools, API, integration |

---

## Remaining Phases (Planned)

| Phase | Name | Description |
|-------|------|-------------|
| 8 | Memory System | Working/long-term memory, embeddings, vector DB, semantic search |
| 9 | Multi-Agent Orchestration | Agent teams, delegation, handoffs, shared context |
| 10 | Workflow Engine | Visual workflow builder, DAG execution, triggers |
| 11 | GitHub Skill System | Installable skills from GitHub, sandboxed execution |
| 12 | Desktop App | Tauri wrapper, native menus, tray, auto-updates |
| 13 | Plugin Marketplace | Community tools, agents, workflows |
| 14 | Collaboration | Multi-user, shared conversations, real-time sync |
| 15 | AI Operating System | Full OS integration, file system access, system tools |

---

## Current Status

### ✅ Working
- All 15+ providers with health checks and model discovery
- Agent CRUD, cloning, default agent, testing (streaming + non-streaming)
- Conversation management with optimistic UI updates
- SSE streaming chat with thinking bubbles, token usage
- Agent execution lifecycle: IDLE → QUEUED → RUNNING → WAITING_FOR_TOOL → COMPLETED/FAILED/CANCELLED
- Retry with exponential backoff + provider fallback
- Tool Runtime: 6 built-in tools (Browser, Python, Terminal, File, Memory, Search)
- Tool execution with permissions, retries, cancellation, streaming
- Glassmorphism UI with motion, depth, HUD components
- 141 tests passing

### 🚧 In Progress
- UI polish (ToolsPage, MemoryPage, WorkflowsPage, WorkspacePage are placeholders)
- PromptBuilder tool resolution integration
- Frontend tool invocation from chat

### 📋 Not Started
- Memory system (vector embeddings)
- Multi-agent orchestration
- Workflow engine
- Desktop app packaging

---

## Known Limitations

| Limitation | Impact | Planned Fix |
|------------|--------|-------------|
| SQLite only (no PostgreSQL) | Single-user, local-only | Phase 14: Multi-user support |
| No authentication | Local dev only | Phase 14: Auth system |
| Tools are placeholders | No real browser/terminal/file ops | Phase 8-11: Real implementations |
| No vector database | No semantic memory/search | Phase 8: pgvector/Chroma/FAISS |
| Frontend tool UI not connected | Can't invoke tools from chat | Phase 7.5: Tool invocation UI |
| Single conversation context | No cross-conversation memory | Phase 8: Memory system |
| No agent-to-agent communication | Single agent only | Phase 9: Multi-agent |

---

## Future Vision

**NEXUS becomes the "VS Code for AI Agents"** — a local-first operating environment where:
- Agents are first-class citizens with persistent memory
- Tools are installable skills (like VS Code extensions)
- Workflows are visual programs that agents execute
- Everything runs locally by default, cloud is optional
- The UI is an intelligent HUD, not a dashboard
- Developers build **AI skills** not just prompts

---

## Quick Links

- [AI Onboarding](AI_ONBOARDING.md) — Start here if new to the project
- [Architecture](ARCHITECTURE.md) — Complete architecture with diagrams
- [Roadmap](ROADMAP.md) — All phases with goals and deliverables
- [Coding Standards](CODING_STANDARDS.md) — Conventions and rules
- [Project State](PROJECT_STATE.json) — Machine-readable status