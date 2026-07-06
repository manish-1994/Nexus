# Project Structure

> Complete directory map with purpose of every folder and key file.

---

## Root Structure

```
NEXUS/
├── backend/                 # Python FastAPI backend
├── frontend/                # React TypeScript frontend
├── docs/                    # Documentation
│   ├── AI_CONTEXT/          # ← THIS DIRECTORY (AI-first docs)
│   ├── api/                 # API reference
│   ├── implementation/      # Phase implementation docs
│   ├── reports/             # Status, changelog, test reports
│   ├── roadmap/             # Future phase plans
│   ├── setup/               # Development setup guides
│   └── testing/             # Test plans and results
├── plans/                   # Architecture plans per phase
├── scripts/                 # Development scripts (dev.js, etc.)
├── data/                    # SQLite database (gitignored)
├── .editorconfig
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
├── Makefile
└── README.md
```

---

## Backend Structure (`backend/`)

```
backend/
├── agents/                  # Agent abstraction layer
│   ├── __init__.py
│   ├── base.py              # BaseAgent abstract class
│   ├── default.py           # DefaultAgent implementation
│   ├── manager.py           # AgentManager - resolution & config
│   ├── prompt_builder.py    # PromptBuilder - assembles system prompts
│   └── registry.py          # AgentRegistry - active agent tracking
│
├── api/                     # FastAPI route definitions
│   ├── __init__.py          # Router aggregation
│   ├── agent_routes.py      # /agents CRUD, clone, test, default
│   ├── ai_runtime.py        # /ai/chat, /ai/stream, /ai/providers
│   ├── chat.py              # /conversations, /chat (SSE streaming)
│   ├── conversations.py     # Conversation management
│   ├── health.py            # /health, /health/ready
│   ├── providers.py         # /providers CRUD, test, models
│   ├── runtime.py           # /runtime/execute, /runtime/execute-stream
│   ├── settings.py          # /settings GET/PUT
│   └── tools.py             # /tools CRUD, execute, cancel, streaming
│
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── agent.py             # Agent (persona, config, capabilities, tools)
│   ├── base.py              # BaseModel - id, created_at, updated_at
│   ├── capability.py        # Capability (provider capabilities)
│   ├── conversation.py      # Conversation (title, user_id)
│   ├── execution.py         # Execution (lifecycle, tokens, tool_calls)
│   ├── message.py           # Message (role, content, tokens, provider)
│   ├── model.py             # Model (provider_id, name, capabilities)
│   ├── provider.py          # Provider (type, config, health_status)
│   ├── settings.py          # Settings (key-value store)
│   └── usage.py             # Usage tracking (tokens, cost)
│
├── providers/               # Provider implementations (15+)
│   ├── __init__.py          # Exports all providers
│   ├── base.py              # BaseProvider abstract class
│   ├── anthropic.py         # Anthropic Claude
│   ├── azure_openai.py      # Azure OpenAI
│   ├── cohere.py            # Cohere
│   ├── custom.py            # Custom OpenAI-compatible
│   ├── deepseek.py          # DeepSeek
│   ├── gemini.py            # Google Gemini
│   ├── groq.py              # Groq
│   ├── lmstudio.py          # LM Studio (local)
│   ├── mistral.py           # Mistral
│   ├── nvidia_nim.py        # NVIDIA NIM
│   ├── ollama.py            # Ollama (local)
│   ├── openai.py            # OpenAI
│   ├── openai_compatible.py # Generic OpenAI-compatible
│   ├── openrouter.py        # OpenRouter
│   ├── perplexity.py        # Perplexity
│   ├── together_ai.py       # Together AI
│   └── xai.py               # xAI Grok
│
├── repositories/            # Data access layer (Repository pattern)
│   ├── __init__.py
│   ├── base_repository.py   # BaseRepository[T] - generic CRUD
│   ├── agent_repository.py  # AgentRepository
│   ├── conversation_repository.py
│   ├── message_repository.py
│   └── provider_repository.py
│
├── schemas/                 # Pydantic v2 schemas (request/response)
│   ├── __init__.py
│   ├── agent.py             # AgentBase, AgentCreate, AgentUpdate, AgentResponse
│   ├── agent_capability.py  # AgentCapability schemas
│   ├── ai_runtime.py        # AIRequest, AIResponse, CapabilityResponse
│   ├── base.py              # BaseSchema with config
│   ├── chat.py              # ChatRequest, ChatResponse, Message schemas
│   ├── execution.py         # Execution schemas
│   ├── health.py            # HealthResponse
│   ├── model.py             # Model schemas
│   └── provider.py          # Provider schemas
│
├── services/                # Business logic layer
│   ├── __init__.py
│   ├── agent_service.py     # Agent CRUD, clone, test, default management
│   ├── ai_runtime.py        # AIRuntime - unified provider gateway
│   ├── base_service.py      # BaseService - common service patterns
│   ├── capability_manager.py # Provider capability sync
│   ├── chat_service.py      # Conversation & message operations
│   ├── conversation_service.py
│   ├── execution_manager.py # AgentExecutionManager - lifecycle orchestrator
│   ├── health_service.py    # Health checks
│   ├── message_service.py   # Message operations
│   ├── model_cache.py       # Model discovery caching
│   ├── provider_service.py  # Provider CRUD, validation
│   ├── provider_validation_service.py
│   ├── retry_policy.py      # RetryPolicy, FallbackPolicy
│   └── usage_tracker.py     # Token usage & cost tracking
│   │
│   └── interfaces/          # Future service interfaces (Phase 8+)
│       ├── knowledge.py
│       ├── memory.py
│       ├── tool.py
│       └── workspace.py
│
├── tools/                   # Universal Tool Runtime (Phase 7)
│   ├── __init__.py          # Exports: BaseTool, ToolRegistry, ToolManager, etc.
│   ├── base.py              # BaseTool, ToolMetadata
│   ├── context.py           # ExecutionContext (shared with Agent Runtime)
│   ├── manager.py           # ToolManager - execution lifecycle
│   ├── permissions.py       # PermissionValidator
│   ├── registry.py          # ToolRegistry - auto-discovery
│   ├── schemas.py           # Tool API schemas
│   │
│   └── builtins/            # Built-in tool implementations
│       ├── __init__.py      # Exports all 6 tools
│       ├── browser.py       # BrowserTool - navigate, extract
│       ├── file.py          # FileTool - read, write, list
│       ├── memory.py        # MemoryTool - store, recall
│       ├── python.py        # PythonTool - execute code
│       ├── search.py        # SearchTool - web search
│       └── terminal.py      # TerminalTool - shell commands
│
├── utils/                   # Shared utilities
│   ├── __init__.py
│   ├── exceptions.py        # Custom exceptions
│   ├── helpers.py           # Common helpers
│   └── security.py          # Encryption (API keys)
│
├── tests/                   # Test suite (141 tests passing)
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (db, client)
│   ├── test_agent_api.py    # Agent API tests (31 tests)
│   ├── test_chat_api.py     # Chat API tests (14 tests)
│   ├── test_chat_service.py # Chat service tests
│   ├── test_config.py       # Config tests
│   ├── test_conversation_service.py
│   ├── test_database.py     # DB initialization tests
│   ├── test_execution_lifecycle.py # Agent execution tests (12 tests)
│   ├── test_health.py       # Health endpoint tests
│   ├── test_message_service.py
│   └── test_tool_runtime.py # Tool Runtime tests (59 tests)
│
├── alembic/                 # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_add_preferred_model_id_to_agents.py
│
├── app.py                   # FastAPI app factory + lifespan
├── config.py                # Settings (Pydantic BaseSettings)
├── database.py              # Engine, session, init_db, seed_agents
├── migrations.py            # Custom migration runner (Phases 0-7)
├── requirements.txt         # Python dependencies
├── test_agent_framework.py  # Manual agent testing script
└── test_gemini_stream.py    # Manual Gemini streaming test
```

---

## Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── api/                 # API client layer
│   │   ├── ai-runtime.ts    # AI Runtime endpoints
│   │   ├── chat.ts          # Chat endpoints
│   │   ├── client.ts        # Axios instance + interceptors
│   │   ├── health.ts        # Health endpoints
│   │   └── providers.ts     # Provider endpoints
│   │
│   ├── components/          # React components (organized by domain)
│   │   ├── Agents/          # Agent management UI
│   │   │   ├── AgentCapabilitiesSelector.tsx
│   │   │   ├── AgentCreateWizard.tsx
│   │   │   ├── AgentDetailsDrawer.tsx
│   │   │   ├── AgentEditDrawer.tsx
│   │   │   └── AgentTestConsole.tsx
│   │   │
│   │   ├── Chat/            # Chat interface
│   │   │   ├── AgentSelector.tsx
│   │   │   ├── ConversationHeader.tsx
│   │   │   ├── ConversationSidebar.tsx
│   │   │   ├── ConversationSidebar.test.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageComposer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── ModelSelector.tsx
│   │   │   ├── ProviderModelSelector.tsx
│   │   │   ├── ProviderSelector.tsx
│   │   │   ├── StreamingBubble.tsx
│   │   │   ├── ThinkingBubble.tsx
│   │   │   └── test_minimal.test.tsx
│   │   │
│   │   ├── Common/          # Shared UI primitives
│   │   │   ├── Badge.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── Motion.tsx
│   │   │   ├── SearchableSelect.tsx
│   │   │   └── SpotlightSearch.tsx
│   │   │
│   │   ├── Core/            # Core visual effects
│   │   │   ├── AICore.tsx
│   │   │   ├── AmbientBackground.tsx
│   │   │   └── BackgroundScene.tsx
│   │   │
│   │   ├── Layout/          # App shell
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── StatusBar.tsx
│   │   │   └── TopBar.tsx
│   │   │
│   │   └── Providers/       # Provider management UI
│   │       ├── CapabilityBadge.tsx
│   │       ├── ProviderCard.tsx
│   │       ├── ProviderForm.tsx
│   │       ├── ProviderIcon.tsx
│   │       ├── ProviderList.tsx
│   │       └── ProviderStatus.tsx
│   │
│   ├── hooks/               # Custom React hooks
│   │   └── index.ts
│   │
│   ├── pages/               # Page components (route targets)
│   │   ├── AgentsPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── ChatPage.test.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── MemoryPage.tsx       # Placeholder (Phase 8)
│   │   ├── PlannerPage.tsx      # Placeholder (Phase 10)
│   │   ├── ProvidersPage.tsx
│   │   ├── SettingsPage.tsx
│   │   ├── ToolsPage.tsx        # Placeholder (Phase 7.5)
│   │   ├── WorkflowsPage.tsx    # Placeholder (Phase 10)
│   │   ├── WorkspacePage.tsx    # Placeholder (Phase 8)
│   │   │
│   │   └── hooks/               # Page-specific hooks
│   │       ├── useAutoScroll.ts
│   │       ├── useChatController.ts
│   │       ├── useConversationManager.ts
│   │       ├── useModelSelection.ts
│   │       └── useOptimisticMessages.ts
│   │
│   ├── services/            # Frontend services
│   │   └── agentApi.ts      # Agent API wrapper
│   │
│   ├── stores/              # Zustand state stores
│   │   ├── index.ts
│   │   ├── agentStore.ts
│   │   ├── modelStore.ts
│   │   └── providerStore.ts
│   │
│   ├── types/               # TypeScript type definitions
│   │   ├── agent.ts
│   │   ├── chat.ts
│   │   ├── health.ts
│   │   ├── index.ts
│   │   └── provider.ts
│   │
│   ├── utils/               # Frontend utilities
│   │   ├── providerErrorParser.ts
│   │   └── toast.ts
│   │
│   ├── App.tsx              # Root component + routing
│   ├── main.tsx             # Entry point
│   ├── vite-env.d.ts
│   └── assets/
│       └── index.css        # Global styles + Tailwind
│
├── index.html
├── package.json
├── package-lock.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── .eslintrc.cjs
├── .prettierrc
├── .env.example
└── test_output.txt
```

---

## Documentation Structure (`docs/`)

```
docs/
├── AI_CONTEXT/              # ← AI-FIRST DOCUMENTATION (this project)
│   ├── NEXUS_MASTER_CONTEXT.md
│   ├── AI_ONBOARDING.md
│   ├── ARCHITECTURE.md
│   ├── PROJECT_STRUCTURE.md
│   ├── ROADMAP.md
│   ├── CHANGELOG.md
│   ├── CODING_STANDARDS.md
│   ├── UI_GUIDELINES.md
│   ├── AGENT_SYSTEM.md
│   ├── TOOL_RUNTIME.md
│   ├── PROVIDER_SYSTEM.md
│   ├── MEMORY_SYSTEM.md
│   ├── KNOWN_ISSUES.md
│   ├── PROMPT_LIBRARY.md
│   ├── NEXUS_MANIFEST.md
│   ├── PROJECT_STATE.json
│   └── PROJECT_INDEX.md
│
├── api/
│   └── API_REFERENCE.md
│
├── implementation/
│   ├── PHASE_01_FOUNDATION.md
│   ├── PHASE_02_CHAT.md
│   ├── PHASE_02_PROVIDER_RUNTIME.md
│   ├── PHASE_03_AI_RUNTIME.md
│   └── PHASE_1_5_APPLICATION_SHELL.md
│
├── reports/
│   ├── BUG_REPORT.md
│   ├── CHANGELOG.md
│   ├── IMPLEMENTATION_REPORT.md
│   ├── STATUS.md
│   └── TEST_REPORT.md
│
├── roadmap/
│   └── NEXT_PHASE.md
│
├── setup/
│   └── DEVELOPMENT_SETUP.md
│
└── testing/
    ├── MANUAL_TEST_RESULTS.md
    ├── TEST_PLAN.md
    └── TEST_RESULTS.md
```

---

## Plans Structure (`plans/`)

```
plans/
├── automatic-model-discovery.md
├── chat-workspace-ux-improvements.md
├── chat-workspace-ux-streaming-enhancement.md
└── phase-2.2-agent-management.md
```

---

## Scripts Structure (`scripts/`)

```
scripts/
└── dev.js                   # Concurrent backend + frontend dev server
```

---

## Data Structure (`data/`)

```
data/
└── nexus.db                 # SQLite database (gitignored)
```

---

## Key File Purposes (Quick Reference)

| File | Purpose |
|------|---------|
| `backend/app.py` | FastAPI app, middleware, exception handlers, router inclusion |
| `backend/config.py` | Pydantic Settings - all env configuration |
| `backend/database.py` | SQLAlchemy engine, session factory, init_db, seed_agents |
| `backend/migrations.py` | Custom migration runner for Phases 0-7 |
| `backend/agents/prompt_builder.py` | Assembles system prompt from agent config + context |
| `backend/services/execution_manager.py` | Core orchestration: state machine, retry, fallback, tools |
| `backend/services/ai_runtime.py` | Unified provider gateway (chat/stream) |
| `backend/services/retry_policy.py` | Exponential backoff + provider fallback logic |
| `backend/tools/manager.py` | Tool execution: permissions, retries, cancellation, logging |
| `backend/tools/registry.py` | Auto-discovers tools from `tools.builtins` package |
| `frontend/src/App.tsx` | React Router setup, all page routes |
| `frontend/src/components/Layout/Layout.tsx` | App shell: sidebar, topbar, statusbar, page outlet |
| `frontend/src/pages/ChatPage.tsx` | Main chat interface with streaming |
| `frontend/src/hooks/useChatController.ts` | Chat logic: send, stream, cancel, optimistic updates |
| `frontend/src/stores/agentStore.ts` | Agent state management (Zustand) |

---

## Module Dependency Rules

```
backend/
├── models/           ← NO DEPENDENCIES (pure SQLAlchemy)
├── repositories/     ← depends on models
├── schemas/          ← NO DEPENDENCIES (pure Pydantic)
├── providers/        ← depends on models, schemas
├── agents/           ← depends on models, schemas
├── tools/            ← depends on models, schemas
├── services/         ← depends on repositories, providers, agents, tools
├── api/              ← depends on services, schemas
└── app.py            ← depends on api, config, database
```

**Frontend follows similar: types → api → hooks → components → pages → App**

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python packages | snake_case | `agent_repository.py` |
| Python classes | PascalCase | `AgentRepository` |
| Python functions | snake_case | `get_agent_by_id` |
| Python constants | UPPER_SNAKE | `MAX_RETRIES` |
| TypeScript files | PascalCase (components) / camelCase (utils) | `AgentCard.tsx`, `useChatController.ts` |
| React components | PascalCase | `AgentCard` |
| TypeScript interfaces | PascalCase | `AgentResponse` |
| Database tables | snake_case plural | `agents`, `execution_logs` |
| Database columns | snake_case | `agent_id`, `created_at` |
| API endpoints | kebab-case | `/api/v1/agents`, `/api/v1/chat` |
| Environment variables | UPPER_SNAKE | `DATABASE_URL`, `SECRET_KEY` |

---

## Cross-References

- [Architecture](ARCHITECTURE.md) — Layer responsibilities and data flows
- [Roadmap](ROADMAP.md) — Phase-by-phase deliverables
- [Coding Standards](CODING_STANDARDS.md) — Conventions and rules
- [Master Context](NEXUS_MASTER_CONTEXT.md) — Project overview