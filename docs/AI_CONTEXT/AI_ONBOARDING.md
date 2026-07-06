# AI Onboarding Guide

> **Read this first.** Everything you need to understand NEXUS and start contributing.

---

## What is NEXUS?

NEXUS is a **local-first AI Operating System** — a desktop application that gives you a unified workspace for:
- Managing **AI agents** (personas with tools, memory, and configuration)
- Connecting to **AI providers** (15+ local and cloud providers)
- Executing **tools** (browser, terminal, code, files, search, memory)
- Managing **conversations** with streaming, branching, and history
- Building **workflows** (visual DAGs that agents execute)

**Key differentiator**: Unlike ChatGPT, Claude, or Cursor, NEXUS runs **entirely on your machine**. Your data never leaves unless you explicitly connect a cloud provider.

---

## Why Does NEXUS Exist?

| Problem | NEXUS Solution |
|---------|----------------|
| Cloud AI = data leaves your machine | Local-first: Ollama, LM Studio, local models by default |
| Provider lock-in | Provider abstraction: swap Gemini ↔ OpenRouter ↔ Local in one click |
| Agents are just prompts | Agents are first-class: config, tools, memory, execution lifecycle |
| No tool standardization | Universal Tool Runtime: registry, permissions, retries, cancellation |
| Chat is linear | Conversations are trees: branch, fork, compare |
| UI is a dashboard | UI is a HUD: glassmorphism, motion, depth, ambient intelligence |

---

## Current Architecture (5-Minute Mental Model)

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   FRONTEND  │────▶│    API      │────▶│   SERVICE LAYER  │
│  (React/TS) │     │  (FastAPI)  │     │                  │
└─────────────┘     └─────────────┘     │ AgentExecutionMgr│
                                        │ ToolManager      │
                                        │ AIRuntime        │
                                        └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    ▼                            ▼                            ▼
            ┌───────────────┐            ┌───────────────┐            ┌───────────────┐
            │  AGENT        │            │  TOOL         │            │  PROVIDER     │
            │  RUNTIME      │            │  RUNTIME      │            │  RUNTIME      │
            │               │            │               │            │               │
            │ State Machine │            │ Registry      │            │ BaseProvider  │
            │ PromptBuilder │            │ Manager       │            │ 15+ Impls     │
            │ Retry/Fallback│            │ Permissions   │            │ Health Check  │
            │ Streaming     │            │ Context       │            │ Model Discovery│
            └───────────────┘            └───────────────┘            └───────────────┘
                    │                            │                            │
                    └────────────────────────────┴────────────────────────────┘
                                                 │
                                                 ▼
                                        ┌───────────────┐
                                        │   DATA LAYER  │
                                        │  SQLite +     │
                                        │  SQLAlchemy   │
                                        └───────────────┘
```

**Dependency Rule**: Layers only depend **downward**. UI never touches DB. Services never touch UI.

---

## Coding Philosophy

| Principle | What It Means |
|-----------|---------------|
| **Local-first** | Every feature works without internet. Cloud is optional enhancement. |
| **Provider-agnostic** | Never hardcode provider logic. Use `BaseProvider` abstraction. |
| **Explicit over implicit** | No magic. Dependency injection. Clear interfaces. |
| **SOLID everywhere** | Single responsibility, open/closed, Liskov, interface segregation, dependency inversion. |
| **Type safety** | Pydantic v2 (backend), TypeScript strict (frontend). No `any`. |
| **Async first** | All I/O is async. `async/await` throughout. |
| **Test-driven** | Write tests before or with code. 141 tests and counting. |

---

## UI Philosophy

**NEXUS is NOT a dashboard. It is an AI Operating System.**

| Concept | Implementation |
|---------|----------------|
| **Glassmorphism** | `bg-white/10 backdrop-blur-md border border-white/10` — depth through transparency |
| **Motion** | Framer Motion for every transition. `whileHover`, `whileTap`, `animate`, `exit` |
| **Depth** | Layered z-index: Background → Content → HUD → Modals → Toasts |
| **HUD Design** | Floating panels, not full-screen pages. Contextual, dismissible, keyboard-first |
| **Ambient Intelligence** | Subtle animations (AICore, AmbientBackground) that respond to system state |
| **Tokens over values** | Colors, spacing, radii defined in Tailwind config — never hardcoded |

---

## Backend Philosophy

| Layer | Responsibility | Example |
|-------|----------------|---------|
| **Models** | Pure SQLAlchemy. No business logic. | `models/agent.py` |
| **Repositories** | Data access only. CRUD + queries. | `repositories/agent_repository.py` |
| **Services** | Business logic. Orchestration. | `services/agent_service.py` |
| **Runtimes** | Execution engines. State machines. | `services/execution_manager.py` |
| **API Routes** | HTTP only. Validation → Service → Response. | `api/agent_routes.py` |

**Never**: Put SQL in services. Put business logic in models. Put HTTP in repositories.

---

## How to Contribute

### 1. Understand the Phase System
Each phase = one architectural layer. Phases are sequential. Don't skip.

### 2. Follow the Patterns
- New provider? Extend `BaseProvider` in `providers/`
- New tool? Extend `BaseTool` in `tools/builtins/`
- New API? Add route in `api/`, schema in `schemas/`, service in `services/`
- New UI page? Add component in `pages/`, register in `App.tsx`

### 3. Run Tests Before Committing
```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm test
```

### 4. Update Documentation
Any architectural change tople change → update relevant `.md` in `docs/AI_CONTEXT/`

---

## Things That Should NEVER Be Changed

| File/Pattern | Reason |
|--------------|--------|
| `backend/config.py` settings structure | Breaks all env configuration |
| `backend/models/base.py` | Base model for all ORM entities |
| `backend/providers/base.py` | Provider abstraction contract |
| `backend/tools/base.py` | Tool abstraction contract |
| `backend/services/execution_manager.py` state machine | Core execution lifecycle |
| `frontend/tailwind.config.js` color/spacing tokens | Design system foundation |
| `frontend/src/stores/*.ts` Zustand store patterns | State management contract |

---

## Current Priorities (Phase 7 Complete → Phase 8 Next)

| Priority | Task | Owner |
|----------|------|-------|
| 🔴 Critical | Memory System: vector embeddings, semantic search | Phase 8 |
| 🟡 High | Frontend tool invocation UI (connect chat → tools) | Phase 7.5 |
| 🟡 High | PromptBuilder tool resolution (agents know about tools) | Phase 7.5 |
| 🟢 Medium | Real tool implementations (browser, terminal, file ops) | Phase 8-11 |
| 🟢 Medium | Multi-agent orchestration | Phase 9 |
| 🔵 Low | Desktop app (Tauri) | Phase 12 |

---

## Quick Start for Development

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend && python -m pytest tests/ -v
cd frontend && npm test
```

---

## Key Files to Read First

| File | Why |
|------|-----|
| `backend/app.py` | App entry, middleware, router registration |
| `backend/config.py` | All settings, env vars |
| `backend/services/execution_manager.py` | Core execution logic |
| `backend/tools/manager.py` | Tool execution logic |
| `frontend/src/components/Core/AICore.tsx` | Ambient background system |
| `frontend/src/stores/agentStore.ts` | Agent state management |
| `docs/AI_CONTEXT/ARCHITECTURE.md` | Complete architecture diagrams |

---

## Questions?

Check:
- `docs/AI_CONTEXT/KNOWN_ISSUES.md` — Current bugs and limitations
- `docs/AI_CONTEXT/ROADMAP.md` — Future phases
- `plans/` — Architecture plans per phase
- `docs/reports/STATUS.md` — Current status report

**Welcome to NEXUS.** Build something that matters.