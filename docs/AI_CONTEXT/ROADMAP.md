# NEXUS Roadmap

> Phase-by-phase breakdown of the NEXUS project. Each phase builds on the previous one.

---

## Phase Overview

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| 0 | Foundation | ✅ Complete | Project setup, FastAPI, React, SQLite, basic config |
| 1 | Provider Runtime | ✅ Complete | BaseProvider abstraction, 15+ provider implementations, health checks, model discovery |
| 2 | Agent Framework | ✅ Complete | Agent CRUD, AgentManager, PromptBuilder, AgentRegistry, testing |
| 3 | AI Runtime | ✅ Complete | AIRuntime gateway, unified chat/stream endpoints, provider resolution |
| 4 | Chat System | ✅ Complete | Conversations, messages, SSE streaming, optimistic updates |
| 5 | Application Shell | ✅ Complete | Layout, Sidebar, TopBar, StatusBar, glassmorphism theme, all pages |
| 6 | Agent Runtime | ✅ Complete | ExecutionManager, state machine, retry/fallback, streaming, cancellation, PromptBuilder v2 |
| 7 | Tool Runtime | ✅ Complete | ToolRegistry, ToolManager, ExecutionContext, 6 built-in tools, API, integration |
| 8 | Memory System | 📋 Planned | Working/long-term memory, embeddings, vector DB, semantic search |
| 9 | Multi-Agent Orchestration | 📋 Planned | Agent teams, delegation, handoffs, shared context |
| 10 | Workflow Engine | 📋 Planned | Visual workflow builder, DAG execution, triggers |
| 11 | GitHub Skill System | 📋 Planned | Installable skills from GitHub, sandboxed execution |
| 12 | Desktop App | 📋 Planned | Tauri wrapper, native menus, tray, auto-updates |
| 13 | Plugin Marketplace | 📋 Planned | Community tools, agents, workflows |
| 14 | Collaboration | 📋 Planned | Multi-user, shared conversations, real-time sync |
| 15 | AI Operating System | 📋 Planned | Full OS integration, file system access, system tools |

---

## Phase 0: Foundation ✅ COMPLETE

**Goal**: Establish project infrastructure

**Deliverables**:
- [x] FastAPI backend with lifespan management
- [x] React 18 + TypeScript + Vite frontend
- [x] Tailwind CSS + Framer Motion setup
- [x] SQLite database with SQLAlchemy 2.0
- [x] Pydantic Settings for configuration
- [x] CORS, exception handling, logging
- [x] Basic project structure (backend/, frontend/, docs/)
- [x] Development script (scripts/dev.js) for concurrent servers

**Dependencies**: None

**Completion**: All tests pass, dev server runs

---

## Phase 1: Provider Runtime ✅ COMPLETE

**Goal**: Universal provider abstraction with 15+ implementations

**Deliverables**:
- [x] `BaseProvider` abstract class with `chat()`, `stream()`, `health_check()`, `list_models()`, `get_capabilities()`
- [x] 15 provider implementations:
  - Local: Ollama, LM Studio
  - Cloud: OpenAI, Anthropic, Gemini, OpenRouter, Groq, Together AI, Perplexity, xAI, Mistral, Cohere, Azure OpenAI, NVIDIA NIM, DeepSeek
  - Custom: OpenAI-compatible endpoint
- [x] Health monitoring with status tracking (healthy/degraded/unhealthy)
- [x] Dynamic model discovery from each provider
- [x] Capability detection (streaming, function calling, vision, JSON mode)
- [x] Provider CRUD API with validation
- [x] Provider service with health checks and model sync

**Dependencies**: Phase 0

**Key Files**:
- `backend/providers/base.py`
- `backend/providers/*.py` (15 implementations)
- `backend/services/provider_service.py`
- `backend/api/providers.py`
- `backend/schemas/provider.py`

---

## Phase 2: Agent Framework ✅ COMPLETE

**Goal**: Agent as first-class entity with configuration, cloning, testing

**Deliverables**:
- [x] Agent model with full configuration (provider, model, temperature, tokens, streaming, system prompt, capabilities, tools)
- [x] AgentRepository with CRUD + specialized queries
- [x] AgentService with business logic (create, update, delete, clone, set_default, test)
- [x] AgentManager for resolution, config building, prompt building, validation
- [x] PromptBuilder v1 for system prompt assembly
- [x] AgentRegistry for active agent tracking
- [x] Agent API: list, get, create, update, delete, clone, set_default, test (streaming + non-streaming)
- [x] Agent test console in UI

**Dependencies**: Phase 1

**Key Files**:
- `backend/models/agent.py`
- `backend/repositories/agent_repository.py`
- `backend/services/agent_service.py`
- `backend/agents/manager.py`
- `backend/agents/prompt_builder.py`
- `backend/agents/registry.py`
- `backend/api/agent_routes.py`
- `frontend/src/pages/AgentsPage.tsx`
- `frontend/src/components/Agents/*`

---

## Phase 3: AI Runtime ✅ COMPLETE

**Goal**: Unified gateway for all AI operations

**Deliverables**:
- [x] `AIRuntime` class as central gateway
- [x] Provider resolution logic (explicit → agent default → global default)
- [x] Unified `/ai/chat` endpoint (non-streaming)
- [x] Unified `/ai/stream` endpoint (SSE streaming)
- [x] Custom headers parsing for provider-specific options
- [x] Capabilities endpoint per provider
- [x] Integration with AgentService for agent testing

**Dependencies**: Phase 1, Phase 2

**Key Files**:
- `backend/services/ai_runtime.py`
- `backend/api/ai_runtime.py`
- `backend/schemas/ai_runtime.py`

---

## Phase 4: Chat System ✅ COMPLETE

**Goal**: Full conversation management with streaming

**Deliverables**:
- [x] Conversation model with title, user_id, metadata
- [x] Message model with role, content, provider, model, tokens, status
- [x] ConversationRepository, MessageRepository
- [x] ChatService with send_message (streaming + non-streaming)
- [x] Optimistic message updates in UI
- [x] SSE streaming with thinking bubbles, token usage
- [x] Conversation CRUD API
- [x] Message history with pagination
- [x] ChatPage with MessageList, MessageComposer, ConversationSidebar
- [x] StreamingBubble, ThinkingBubble components

**Dependencies**: Phase 3

**Key Files**:
- `backend/models/conversation.py`
- `backend/models/message.py`
- `backend/repositories/conversation_repository.py`
- `backend/repositories/message_repository.py`
- `backend/services/chat_service.py`
- `backend/api/chat.py`
- `frontend/src/pages/ChatPage.tsx`
- `frontend/src/components/Chat/*`
- `frontend/src/hooks/useChatController.ts`
- `frontend/src/hooks/useOptimisticMessages.ts`

---

## Phase 5: Application Shell ✅ COMPLETE

**Goal**: Complete UI shell with glassmorphism design system

**Deliverables**:
- [x] Layout component with Sidebar, TopBar, StatusBar
- [x] Glassmorphism design tokens in Tailwind config
- [x] Framer Motion animations throughout
- [x] AICore ambient background system
- [x] All page routes: Home, Chat, Agents, Providers, Settings, Tools, Memory, Workflows, Workspace, Planner, Dashboard
- [x] Responsive design (mobile → desktop)
- [x] Dark theme with CSS variables
- [x] Spotlight search (Cmd+K)
- [x] Motion wrapper components

**Dependencies**: Phase 4

**Key Files**:
- `frontend/src/components/Layout/*`
- `frontend/src/components/Core/*`
- `frontend/src/pages/*.tsx`
- `frontend/tailwind.config.js`
- `frontend/src/assets/index.css`

---

## Phase 6: Agent Runtime ✅ COMPLETE

**Goal**: Production-grade agent execution with state machine, retry, fallback, streaming, cancellation

**Deliverables**:
- [x] Execution model with full lifecycle tracking
- [x] ExecutionStatus enum: IDLE → QUEUED → RUNNING → WAITING_FOR_TOOL → COMPLETED/FAILED/CANCELLED
- [x] AgentExecutionManager orchestrating full lifecycle
- [x] State machine with validation at each transition
- [x] RetryPolicy with exponential backoff + jitter
- [x] FallbackPolicy with provider/model fallback on failure
- [x] Streaming execution with chunk-by-chunk cancellation
- [x] Cancellation support for QUEUED, RUNNING, WAITING_FOR_TOOL
- [x] PromptBuilder v2 with tool/capability/memory/workspace resolution
- [x] Execution history with pagination and filtering
- [x] Runtime API: submit, execute, stream, cancel, history, active
- [x] Usage tracking (tokens, cost, latency)
- [x] 22 comprehensive tests covering all scenarios

**Dependencies**: Phase 2, Phase 3, Phase 4

**Key Files**:
- `backend/models/execution.py`
- `backend/services/execution_manager.py`
- `backend/services/retry_policy.py`
- `backend/agents/prompt_builder.py`
- `backend/api/runtime.py`
- `backend/tests/test_execution_lifecycle.py`

---

## Phase 7: Tool Runtime ✅ COMPLETE

**Goal**: Universal tool execution framework with registry, permissions, retries, cancellation

**Deliverables**:
- [x] `BaseTool` abstract class with `ToolMetadata` (id, name, description, version, category, input/output schemas, timeout, streaming, cancellation, permissions)
- [x] `ToolRegistry` with auto-discovery via `pkgutil` from `tools.builtins`
- [x] `ToolManager` with full lifecycle: lookup → permissions → validation → retry → cancellation → logging
- [x] `ExecutionContext` shared between Agent Runtime and Tool Runtime (execution_id, agent_id, conversation_id, cancel_event, logger)
- [x] `PermissionValidator` with wildcard (`*`) support for development
- [x] 6 built-in placeholder tools:
  - BrowserTool (`browser.navigate`)
  - PythonTool (`python.execute`)
  - TerminalTool (`terminal.run`, streaming)
  - FileTool (`file.operations`)
  - MemoryTool (`memory.manage`)
  - SearchTool (`search.query`)
- [x] Tool API: list, categories, inspect, execute, execute-stream, cancel, active executions
- [x] AgentExecutionManager integration: `execute_tool()`, `execute_tool_stream()`, `list_available_tools()`
- [x] Execution model: `tool_calls` JSON column for audit trail
- [x] Migration 004: add tool_calls column
- [x] 59 comprehensive tests

**Dependencies**: Phase 6

**Key Files**:
- `backend/tools/base.py`
- `backend/tools/registry.py`
- `backend/tools/manager.py`
- `backend/tools/context.py`
- `backend/tools/permissions.py`
- `backend/tools/schemas.py`
- `backend/tools/builtins/*.py`
- `backend/api/tools.py`
- `backend/services/execution_manager.py` (integration)
- `backend/models/execution.py` (tool_calls column)
- `backend/migrations.py` (migration_004)
- `backend/tests/test_tool_runtime.py`

---

## Phase 8: Memory System 📋 PLANNED

**Goal**: Persistent, searchable memory for agents

**Deliverables**:
- [ ] Working memory (in-context, per conversation)
- [ ] Conversation memory (cross-session, summarized)
- [ ] Long-term memory (vector embeddings, semantic search)
- [ ] Vector database integration (pgvector / Chroma / FAISS)
- [ ] Embedding provider abstraction (local + cloud)
- [ ] Memory ranking and relevance scoring
- [ ] Memory API: store, retrieve, search, forget
- [ ] Agent memory configuration (enabled, capacity, retention)
- [ ] PromptBuilder memory resolution

**Dependencies**: Phase 7

**Estimated Effort**: 2-3 weeks

---

## Phase 9: Multi-Agent Orchestration 📋 PLANNED

**Goal**: Agents working together as teams

**Deliverables**:
- [ ] Agent team definition (lead + members)
- [ ] Delegation protocol (handoff, consult, broadcast)
- [ ] Shared context between team members
- [ ] Team execution manager
- [ ] Inter-agent communication protocol
- [ ] Conflict resolution
- [ ] Team memory (shared + individual)
- [ ] Visual team builder in UI

**Dependencies**: Phase 8

**Estimated Effort**: 3-4 weeks

---

## Phase 10: Workflow Engine 📋 PLANNED

**Goal**: Visual, executable workflows for complex tasks

**Deliverables**:
- [ ] DAG-based workflow definition
- [ ] Visual workflow builder (React Flow / custom)
- [ ] Node types: Agent, Tool, Condition, Loop, Parallel, Human-in-loop
- [ ] Workflow execution engine with state persistence
- [ ] Trigger system: schedule, webhook, event, manual
- [ ] Workflow versioning and rollback
- [ ] Execution monitoring and debugging
- [ ] Workflow templates library

**Dependencies**: Phase 9

**Estimated Effort**: 4-5 weeks

---

## Phase 11: GitHub Skill System 📋 PLANNED

**Goal**: Installable, versioned AI capabilities from GitHub

**Deliverables**:
- [ ] Skill manifest format (package.json equivalent)
- [ ] GitHub repository scanner for skills
- [ ] Sandboxed execution environment (Deno / WASM / containers)
- [ ] Skill installation, update, removal
- [ ] Skill marketplace UI
- [ ] Dependency resolution between skills
- [ ] Permission model for skills
- [ ] Built-in skills: browser, terminal, code, git, github, web search

**Dependencies**: Phase 10

**Estimated Effort**: 4-6 weeks

---

## Phase 12: Desktop App 📋 PLANNED

**Goal**: Native desktop application

**Deliverables**:
- [ ] Tauri wrapper (Rust + WebView)
- [ ] Native menu bar / system tray
- [ ] Auto-updater (GitHub Releases)
- [ ] Native file dialogs
- [ ] Global hotkeys
- [ ] Startup at login
- [ ] Code signing (macOS/Windows)
- [ ] Installer generation (.dmg, .msi, .AppImage)

**Dependencies**: Phase 7 (can start earlier)

**Estimated Effort**: 3-4 weeks

---

## Phase 13: Plugin Marketplace 📋 PLANNED

**Goal**: Community-driven ecosystem

**Deliverables**:
- [ ] Marketplace backend (registry API)
- [ ] Publishing workflow for developers
- [ ] Installation from marketplace
- [ ] Ratings, reviews, categories
- [ ] Featured/curated collections
- [ ] Revenue sharing (optional)
- [ ] Security scanning

**Dependencies**: Phase 11, Phase 12

**Estimated Effort**: 4-6 weeks

---

## Phase 14: Collaboration 📋 PLANNED

**Goal**: Multi-user, real-time features

**Deliverables**:
- [ ] User authentication (OAuth, email/password)
- [ ] Workspaces / organizations
- [ ] Shared conversations with real-time sync (WebRTC / WebSocket)
- [ ] Presence indicators
- [ ] Comments / annotations on messages
- [ ] Role-based access control
- [ ] Audit logs
- [ ] PostgreSQL migration (from SQLite)

**Dependencies**: Phase 12

**Estimated Effort**: 6-8 weeks

---

## Phase 15: AI Operating System 📋 PLANNED

**Goal**: Full OS integration - the ultimate vision

**Deliverables**:
- [ ] File system access (read/write/watch)
- [ ] Process management (spawn, monitor, kill)
- [ ] System API integration (notifications, clipboard, screenshots)
- [ ] Window management (tiling, focus)
- [ ] Shell integration (command completion, history)
- [ ] IDE integration (VS Code extension)
- [ ] Browser extension for web context
- [ ] Mobile companion app
- [ ] Self-improving agents (learning from usage)

**Dependencies**: All previous phases

**Estimated Effort**: Ongoing

---

## Milestone Summary

| Milestone | Target Phase | Description |
|-----------|--------------|-------------|
| **MVP** | Phase 7 | Local-first AI workspace with agents, providers, tools, chat |
| **Memory Alpha** | Phase 8 | Persistent memory with semantic search |
| **Team Alpha** | Phase 9 | Multi-agent collaboration |
| **Workflow Alpha** | Phase 10 | Visual workflow automation |
| **Desktop Beta** | Phase 12 | Native desktop app |
| **Platform 1.0** | Phase 13 | Marketplace + ecosystem |
| **Multi-user 1.0** | Phase 14 | Collaboration features |
| **OS Integration** | Phase 15 | True AI Operating System |

---

## Current Focus

**Phase 7 Complete** → **Phase 8 Next**

Immediate priorities:
1. Memory System design and vector DB selection
2. Frontend tool invocation UI (connect chat → tools)
3. PromptBuilder tool resolution (agents know about available tools)
4. Real tool implementations (beyond placeholders)

---

## Cross-References

- [Master Context](NEXUS_MASTER_CONTEXT.md) — Project overview
- [Architecture](ARCHITECTURE.md) — System design
- [Changelog](CHANGELOG.md) — Historical changes
- [Project State](PROJECT_STATE.json) — Machine-readable status