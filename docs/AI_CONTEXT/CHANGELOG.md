# NEXUS Changelog

> Complete project history grouped by phase. All notable changes documented.

---

## [Phase 7] - 2025-01-15 — Universal Tool Runtime

### Added
- **Tool Runtime Core** (`backend/tools/`)
  - `BaseTool` abstract class with `ToolMetadata` dataclass
  - `ToolRegistry` with auto-discovery via `pkgutil.iter_modules`
  - `ToolManager` with full execution lifecycle (lookup, permissions, validation, retries, cancellation, logging)
  - `ExecutionContext` shared between Agent Runtime and Tool Runtime
  - `PermissionValidator` with wildcard (`*`) support for development mode
  - Pydantic schemas for tool API (`ToolMetadataResponse`, `ToolExecuteRequest`, `ToolExecuteResponse`, `ToolCancelRequest`, `ToolCancelResponse`)

- **6 Built-in Placeholder Tools** (`backend/tools/builtins/`)
  - `BrowserTool` — `browser.navigate` (category: browser)
  - `PythonTool` — `python.execute`python.execute` (category: python)
  - `TerminalTool` — `terminal.run` (category: terminal, streaming support)
  - `FileTool` — `file.operations` (category: file)
  - `MemoryTool` — `memory.manage` (category: memory)
  - `SearchTool` — `search.query` (category: search)

- **Tool API Endpoints** (`backend/api/tools.py`)
  - `GET /api/v1/tools` — List all tools (filter by category)
  - `GET /api/v1/tools/categories` — List tool categories
  - `GET /api/v1/tools/{tool_id}` — Inspect tool metadata
  - `POST /api/v1/tools/{tool_id}/execute` — Execute tool (non-streaming)
  - `POST /api/v1/tools/{tool_id}/execute-stream` — Execute tool (SSE streaming)
  - `POST /api/v1/tools/cancel` — Cancel running execution
  - `GET /api/v1/tools/executions/active` — List active executions

- **AgentExecutionManager Integration**
  - `tool_manager` property (lazy-loaded singleton)
  - `execute_tool(execution_id, tool_id, input_data)` — Non-streaming tool execution
  - `execute_tool_stream(execution_id, tool_id, input_data)` — Streaming tool execution
  - `list_available_tools(category)` — Tools for prompt assembly
  - Execution state validation (RUNNING/WAITING_FOR_TOOL only)
  - Tool call audit trail persisted to `execution.tool_calls` JSON column

- **Database Migration**
  - `migration_004_add_tool_calls` — Adds `tool_calls` JSON column to `execution_logs` table
  - Idempotent SQLite ALTER TABLE

- **Comprehensive Test Suite** (`backend/tests/test_tool_runtime.py` — 59 tests)
  - ToolRegistry: registration, discovery, listing (10 tests)
  - BaseTool: validation, streaming default (4 tests)
  - PermissionValidator: grants, revokes, wildcard (5 tests)
  - ToolManager: success, not found, permissions, validation, failure, retries, streaming, cancellation (16 tests)
  - ExecutionContext: cancellation, logging, metadata (5 tests)
  - ToolRuntimeIntegration: end-to-end with AgentExecutionManager (5 tests)
  - ToolAPI: all REST endpoints (10 tests)
  - ToolSchemas: Pydantic validation (4 tests)
  - ToolExecutionConfig: defaults and custom (2 tests)

### Changed
- `backend/services/execution_manager.py` — Added ToolManager integration, `execute_tool`, `execute_tool_stream`, `list_available_tools`
- `backend/models/execution.py` — Added `tool_calls = Column(JSON, nullable=True, default=list)`
- `backend/migrations.py` — Added `migration_004_add_tool_calls`
- `backend/api/__init__.py` — Registered `tools_router`

### Fixed
- ToolManager.cancel() now sets both internal cancel_event and shared ExecutionContext.cancel_event for proper cancellation propagation
- API tool not found returns 404 instead of 400
- Test fixtures updated for Agent model field names (`prompt_template`, `preferred_model_id`)

---

## [Phase 6] - 2025-01-10 — Agent Runtime

### Added
- **Execution Model** (`backend/models/execution.py`)
  - `ExecutionStatus` enum: IDLE, QUEUED, RUNNING, WAITING_FOR_TOOL, COMPLETED, FAILED, CANCELLED
  - Full lifecycle tracking: tokens, cost, latency, retry/fallback info, timestamps, error details
  - `tool_calls` JSON column (prepared for Phase 7)

- **AgentExecutionManager** (`backend/services/execution_manager.py`)
  - State machine with validation at each transition
  - `create_execution()`, `submit()`, `execute()`, `execute_stream()`, `cancel()`
  - In-memory active execution registry for cancellation
  - RetryPolicy integration with exponential backoff
  - FallbackPolicy integration for provider failover
  - UsageTracker integration for token/cost tracking
  - PromptBuilder v2 integration

- **RetryPolicy** (`backend/services/retry_policy.py`)
  - Configurable max retries, base delay, max delay, exponential base
  - `should_retry(attempt, error)` — intelligent retry decisions
  - `delay_ms(attempt)` — exponential backoff with jitter
  - `wait_before_retry(attempt)` — async wait

- **FallbackPolicy** (`backend/services/retry_policy.py`)
  - `get_fallback(agent, primary_provider_id, primary_model, failed_error)` — selects fallback provider/model
  - Considers agent capabilities, provider health, model compatibility

- **PromptBuilder v2** (`backend/agents/prompt_builder.py`)
  - Modular resolution: conversation, workspace, memory, files, tools, capabilities
  - Graceful degradation when optional components unavailable
  - Structured prompt sections with clear delimiters

- **Runtime API** (`backend/api/runtime.py`)
  - `POST /runtime/execute` — Non-streaming execution
  - `POST /runtime/execute-stream` — SSE streaming execution
  - `POST /runtime/cancel` — Cancel active execution
  - `GET /runtime/history` — Execution history with filters
  - `GET /runtime/active` — List active executions

- **Database Migration**
  - `migration_003_add_execution_logs` — Creates `execution_logs` table

- **Test Suite** (`backend/tests/test_execution_lifecycle.py` — 12 tests)
  - State machine transitions
  - Non-streaming success
  - Streaming success
  - Streaming cancellation
  - Retry then success
  - Failure after exhausted retries
  - Retry policy decisions
  - Fallback policy no fallback

### Changed
- `backend/agents/manager.py` — Enhanced `build_prompt_for_agent` to use PromptBuilder v2
- `backend/api/agent_routes.py` — Updated test endpoints to use ExecutionManager

---

## [Phase 5] - 2025-01-05 — Application Shell

### Added
- **Layout Components** (`frontend/src/components/Layout/`)
  - `Layout.tsx` — App shell with sidebar, topbar, statusbar, page outlet
  - `Sidebar.tsx` — Navigation with collapsible sections, agent/provider status
  - `TopBar.tsx` — Global actions, search, user menu
  - `StatusBar.tsx` — System status, provider health, token usage

- **Core Visual System** (`frontend/src/components/Core/`)
  - `AICore.tsx` — Ambient animated core responding to system state
  - `AmbientBackground.tsx` — Layered background with noise, gradients
  - `BackgroundScene.tsx` — Three.js scene for immersive effects

- **Design System** (`frontend/tailwind.config.js`)
  - Glassmorphism tokens: `glass`, `glass-strong`, `glass-subtle`
  - Color palette: semantic colors (primary, secondary, accent, surface, background)
  - Spacing scale, border radius, shadows, transitions
  - Animation keyframes: pulse, float, shimmer, rotate

- **All Page Routes** (`frontend/src/pages/`)
  - `HomePage.tsx` — Dashboard with stats, recent activity
  - `ChatPage.tsx` — Full chat interface
  - `AgentsPage.tsx` — Agent management with test console
  - `ProvidersPage.tsx` — Provider management with health
  - `SettingsPage.tsx` — App settings
  - `ToolsPage.tsx` — Placeholder for Tool Runtime
  - `MemoryPage.tsx` — Placeholder for Memory System
  - `WorkflowsPage.tsx` — Placeholder for Workflow Engine
  - `WorkspacePage.tsx` — Placeholder for Workspace
  - `PlannerPage.tsx` — Placeholder for Planner
  - `DashboardPage.tsx` — System overview

- **Common Components** (`frontend/src/components/Common/`)
  - `Motion.tsx` — Framer Motion wrappers
  - `SpotlightSearch.tsx` — Cmd+K command palette
  - `SearchableSelect.tsx` — Accessible select with search
  - `LoadingSpinner.tsx`, `ErrorBoundary.tsx`, `ErrorMessage.tsx`, `Badge.tsx`

### Changed
- `frontend/src/App.tsx` — Complete routing setup with all pages
- `frontend/src/assets/index.css` — Global styles, CSS variables, Tailwind imports

---

## [Phase 4] - 2025-01-01 — Chat System

### Added
- **Conversation & Message Models** (`backend/models/`)
  - `Conversation` — title, user_id, metadata
  - `Message` — role, content, provider, model, tokens, status (sending/streaming/complete/error)

- **ChatService** (`backend/services/chat_service.py`)
  - `send_message()` — Non-streaming with full persistence
  - `stream_message()` — SSE streaming with chunk handling
  - `_build_messages_for_provider()` — Formats conversation for provider

- **Chat API** (`backend/api/chat.py`)
  - `POST /chat` — Send message (streaming + non-streaming)
  - `GET /conversations` — List with pagination
  - `POST /conversations` — Create conversation
  - `GET /conversations/{id}` — Get conversation
  - `PUT /conversations/{id}` — Update conversation
  - `DELETE /conversations/{id}` — Delete conversation
  - `GET /conversations/{id}/messages` — Paginated messages

- **Frontend Chat** (`frontend/src/`)
  - `ChatPage.tsx` — Main chat interface
  - `MessageList.tsx` — Virtualized message list
  - `MessageBubble.tsx` — User/assistant message display
  - `StreamingBubble.tsx` — Real-time streaming display
  - `ThinkingBubble.tsx` — Thinking animation during generation
  - `MessageComposer.tsx` — Input with model/provider selectors
  - `ConversationSidebar.tsx` — Conversation list with search
  - `useChatController.ts` — Chat logic hook
  - `useOptimisticMessages.ts` — Optimistic updates hook
  - `useConversationManager.ts` — Conversation CRUD hook

### Changed
- `backend/services/ai_runtime.py` — Enhanced streaming with conversation_id for context

---

## [Phase 3] - 2024-12-28 — AI Runtime

### Added
- **AIRuntime** (`backend/services/ai_runtime.py`)
  - `chat(messages, provider_id, model, **kwargs)` — Unified non-streaming
  - `stream(messages, provider_id, model, conversation_id, **kwargs)` — Unified streaming
  - `_resolve_provider()` — Smart provider resolution (explicit → agent default → global default)
  - `_parse_custom_headers()` — Provider-specific header parsing

- **AI Runtime API** (`backend/api/ai_runtime.py`)
  - `POST /ai/chat` — Non-streaming chat
  - `POST /ai/stream` — SSE streaming chat
  - `GET /ai/providers/{provider_id}/capabilities` — Provider capabilities

- **Schemas** (`backend/schemas/ai_runtime.py`)
  - `AIRequest`, `AIResponse`, `CapabilityResponse`

### Changed
- `backend/services/agent_service.py` — Updated `test_agent` to use AIRuntime

---

## [Phase 2] - 2024-12-25 — Agent Framework

### Added
- **Agent Model** (`backend/models/agent.py`)
  - Full configuration: provider, model, temperature, max_tokens, streaming, system_prompt, capabilities, tools, memory_enabled

- **AgentRepository** (`backend/repositories/agent_repository.py`)
  - CRUD + `get_default()`, `set_default()`, `list_by_category()`

- **AgentService** (`backend/services/agent_service.py`)
  - CRUD, clone, set_default, test (streaming + non-streaming)
  - Name uniqueness validation
  - Default agent management (only one default)

- **AgentManager** (`backend/agents/manager.py`)
  - `resolve_agent()` — Returns DefaultAgent instance
  - `get_agent_config()` — Builds execution config dict
  - `build_prompt_for_agent()` — Uses PromptBuilder
  - `validate_execution()` — Checks provider/model validity

- **PromptBuilder v1** (`backend/agents/prompt_builder.py`)
  - Assembles system prompt from agent config + conversation context

- **AgentRegistry** (`backend/agents/registry.py`)
  - Singleton registry for active agents

- **Agent API** (`backend/api/agent_routes.py`)
  - Full CRUD + clone, set_default, test (streaming + non-streaming)

- **Frontend Agent Management** (`frontend/src/`)
  - `AgentsPage.tsx` — Agent grid with cards
  - `AgentCreateWizard.tsx` — Multi-step creation form
  - `AgentEditDrawer.tsx` — Edit drawer
  - `AgentDetailsDrawer.tsx` — Detail view
  - `AgentTestConsole.tsx` — Live testing with streaming

---

## [Phase 1] - 2024-12-20 — Provider Runtime

### Added
- **BaseProvider** (`backend/providers/base.py`)
  - Abstract methods: `chat()`, `stream()`, `health_check()`, `list_models()`, `get_capabilities()`
  - `ProviderType` enum (15+ types)
  - `HealthStatus` enum (healthy, degraded, unhealthy)

- **15 Provider Implementations** (`backend/providers/`)
  - `gemini.py` — Google Gemini
  - `openrouter.py` — OpenRouter
  - `openai.py` — OpenAI
  - `anthropic.py` — Anthropic Claude
  - `azure_openai.py` — Azure OpenAI
  - `groq.py` — Groq
  - `together_ai.py` — Together AI
  - `perplexity.py` — Perplexity
  - `xai.py` — xAI Grok
  - `mistral.py` — Mistral
  - `cohere.py` — Cohere
  - `ollama.py` — Ollama (local)
  - `lmstudio.py` — LM Studio (local)
  - `nvidia_nim.py` — NVIDIA NIM
  - `deepseek.py` — DeepSeek
  - `custom.py` / `openai_compatible.py` — Generic OpenAI-compatible

- **ProviderService** (`backend/services/provider_service.py`)
  - CRUD, health checks, model sync, capability detection

- **Provider API** (`backend/api/providers.py`)
  - Full CRUD, test connection, list models, get capabilities

- **CapabilityManager** (`backend/services/capability_manager.py`)
  - Syncs provider capabilities to database

- **Database Migrations**
  - `migration_001_add_preferred_model_id_to_agents`
  - `migration_002_add_agent_config_columns`

---

## [Phase 0] - 2024-12-15 — Foundation

### Added
- **Project Structure** — backend/, frontend/, docs/, plans/, scripts/, data/
- **FastAPI App** (`backend/app.py`) — Lifespan, CORS, exception handlers, router inclusion
- **Configuration** (`backend/config.py`) — Pydantic Settings with env file support
- **Database** (`backend/database.py`) — SQLAlchemy engine, session, init_db, seed_agents
- **Custom Migrations** (`backend/migrations.py`) — Idempotent migration runner
- **React + Vite + TypeScript** — Frontend scaffold
- **Tailwind + Framer Motion** — Styling and animation
- **Development Script** (`scripts/dev.js`) — Concurrent backend/frontend with port management
- **Docker Compose** — Production and development configs

---

## Version History

| Version | Date | Phase | Description |
|---------|------|-------|-------------|
| 0.1.0 | 2025-01-15 | 7 | Universal Tool Runtime complete |
| 0.0.7 | 2025-01-10 | 6 | Agent Runtime complete |
| 0.0.6 | 2025-01-05 | 5 | Application Shell complete |
| 0.0.5 | 2025-01-01 | 4 | Chat System complete |
| 0.0.4 | 2024-12-28 | 3 | AI Runtime complete |
| 0.0.3 | 2024-12-25 | 2 | Agent Framework complete |
| 0.0.2 | 2024-12-20 | 1 | Provider Runtime complete |
| 0.0.1 | 2024-12-15 | 0 | Foundation complete |

---

## Cross-References

- [Roadmap](ROADMAP.md) — Future phases
- [Master Context](NEXUS_MASTER_CONTEXT.md) — Current status
- [Project State](PROJECT_STATE.json) — Machine-readable status