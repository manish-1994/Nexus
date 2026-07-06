# NEXUS Coding Standards

> Mandatory conventions for all code in the NEXUS project. Enforced by CI and code review.

---

## General Principles

| Principle | Rule |
|-----------|------|
| **Explicit over implicit** | No magic. Prefer dependency injection over globals. |
| **Type safety** | 100% type coverage. No `any` (TS) or `Any` (Python) without justification. |
| **Async first** | All I/O is async. Use `async/await` throughout. |
| **Single responsibility** | Each module/class/function does one thing. |
| **Immutability** | Prefer immutable data structures. Use `frozen=True` dataclasses, `readonly` in TS. |
| **Error handling** | Never swallow exceptions. Use custom exceptions with context. |
| **Testing** | Write tests for all new logic. Aim for >90% coverage on services/runtimes. |
| **Layer separation** | Strict dependency direction: UI → API → Service → Runtime → Data. No upward/cross-runtime deps. |

---

## Python Standards (Backend)

### Version & Tooling
- **Python**: 3.11+
- **Formatter**: `black` (line length 100)
- **Linter**: `ruff` (replaces flake8, isort)
- **Type checker**: `mypy` (strict mode)
- **Test runner**: `pytest` with `pytest-asyncio`

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Packages/modules | snake_case | `agent_repository.py` |
| Classes | PascalCase | `AgentRepository` |
| Functions/methods | snake_case | `get_agent_by_id` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Private (module) | _leading_underscore | `_active_executions` |
| Private (class) | __dunder | `__private_method` |
| Type variables | PascalCase with `_T` suffix | `ModelType`, `T` |

### Code Style

```python
# Imports: stdlib → third-party → local
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.agent import Agent
from services.base_service import BaseService


# Dataclasses for config/records (frozen=True for immutability)
@dataclass(frozen=True)
class ToolExecutionConfig:
    max_retries: int = 3
    base_delay: float = 1.0


# Classes: type hints on all methods, docstrings for public API
class ToolManager:
    """Orchestrates tool execution with full lifecycle management."""

    def __init__(
        self,
        registry: ToolRegistry,
        permission_validator: Optional[PermissionValidator] = None,
        config: Optional[ToolExecutionConfig] = None,
    ) -> None:
        self.registry = registry
        self.permission_validator = permission_validator or PermissionValidator()
        self.config = config or ToolExecutionConfig()
        self._active_executions: Dict[str, ToolExecutionContext] = {}

    async def execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Execute a tool with full lifecycle management."""
        tool = self._resolve_tool(tool_id)
        # ...


# Async functions: always specify return type
async def _execute_with_retry(
    self,
    exec_ctx: ToolExecutionContext,
    input_data: Dict[str, Any],
) -> Any:
    # ...


# Error handling: custom exceptions, no bare except
try:
    result = await tool.execute(input_data, context)
except asyncio.CancelledError:
    raise
except ValidationError as exc:
    raise ValueError(f"Invalid input: {exc}") from exc
except Exception as exc:
    logger.error("Tool execution failed: %s", exc)
    raise RuntimeError("Tool execution failed") from exc
```

### SQLAlchemy Models

```python
# models/agent.py
class Agent(BaseModel):
    __tablename__ = "agents"

    # Columns: snake_case, explicit types, constraints
    name = Column(String(255), nullable=False)
    temperature = Column(Float, default=0.7)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)

    # Relationships: explicit foreign_keys, lazy loading strategy
    provider = relationship("Provider", foreign_keys=[provider_id], lazy="joined")
```

### Pydantic Schemas

```python
# schemas/agent.py
class AgentBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class AgentCreate(AgentBase):
    provider_id: Optional[int] = None


class AgentResponse(AgentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Repository Pattern

```python
# repositories/base_repository.py
class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, data: dict) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
```

### Service Layer

```python
# services/agent_service.py
class AgentService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.repository = AgentRepository(db)

    def create_agent(self, data: dict) -> Agent:
        self._validate_name_uniqueness(data["name"])
        return self.repository.create(data)
```

### API Routes

```python
# api/agent_routes.py
@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_in: AgentCreate,
    service: AgentService = Depends(_get_service),
) -> AgentResponse:
    agent = service.create_agent(agent_in.model_dump())
    return AgentResponse.model_validate(agent)
```

### Testing

```python
# tests/test_agent_api.py
@pytest.mark.asyncio
async def test_create_agent(client: TestClient):
    response = client.post("/api/v1/agents", json={"name": "Test Agent"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
```

---

## TypeScript Standards (Frontend)

### Version & Tooling
- **TypeScript**: 5.3+ (strict mode)
- **Formatter**: `prettier` (single quotes, trailing commas)
- **Linter**: `eslint` with `typescript-eslint`
- **Test runner**: `vitest` + `react-testing-library`

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files (components) | PascalCase | `AgentCard.tsx` |
| Files (hooks/utils) | camelCase | `useChatController.ts` |
| Components | PascalCase | `AgentCard` |
| Hooks | camelCase with `use` prefix | `useChatController` |
| Interfaces/Types | PascalCase | `AgentResponse` |
| Functions/variables | camelCase | `sendMessage` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| CSS classes | kebab-case (Tailwind) | `bg-primary-500` |

### Code Style

```typescript
// api/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

export const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

// Interceptors for auth, errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle errors globally
    return Promise.reject(error);
  }
);
```

```typescript
// types/agent.ts
export interface Agent {
  id: number;
  name: string;
  description: string | null;
  provider_id: number | null;
  preferred_model_id: number | null;
  temperature: number;
  max_tokens: number | null;
  streaming: boolean;
  enabled: boolean;
  color: string | null;
  category: string | null;
  top_p: number;
  presence_penalty: number;
  frequency_penalty: number;
  context_window: number | null;
  prompt_template: string | null;
  capabilities: string | null; // JSON string
  tools: string | null; // JSON string
  default_tools: string | null; // JSON string
  memory_enabled: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}
```

```typescript
// stores/agentStore.ts
import { create } from 'zustand';
import { Agent } from '../types/agent';

interface AgentState {
  agents: Agent[];
  selectedAgentId: number | null;
  setAgents: (agents: Agent[]) => void;
  selectAgent: (id: number | null) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  selectedAgentId: null,
  setAgents: (agents) => set({ agents }),
  selectAgent: (selectedAgentId) => set({ selectedAgentId }),
}));
```

```typescript
// hooks/useChatController.ts
import { useCallback, useRef } from 'react';
import { useOptimisticMessages } from './useOptimisticMessages';
import { chatApi } from '../api/chat';

export function useChatController(conversationId: number | null) {
  const { messages, addOptimisticMessage, updateOptimisticMessage } =
    useOptimisticMessages(conversationId);

  const sendMessage = useCallback(
    async (content: string, providerId: number, model: string) => {
      // Optimistic update
      const tempId = Date.now();
      addOptimisticMessage({ id: tempId, role: 'user', content, status: 'sending' });

      try {
        const response = await chatApi.sendMessage({
          conversation_id: conversationId!,
          content,
          provider_id: providerId,
          model,
          stream: true,
        });
        // Handle streaming...
      } catch (error) {
        // Error handling
      }
    },
    [conversationId, addOptimisticMessage]
  );

  return { messages, sendMessage };
}
```

```tsx
// components/Chat/MessageBubble.tsx
import { motion } from 'framer-motion';
import { Message } from '../../types/chat';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`
          max-w-[70%] rounded-2xl px-4 py-2
          ${isUser
            ? 'bg-primary-500 text-white rounded-br-none'
            : 'bg-surface border border-white/10 rounded-bl-none'}
        `}
      >
        {message.content}
      </div>
    </motion.div>
  );
}
```

### React Patterns

- **Function components only** — No class components.
- **Hooks for logic extraction** — Custom hooks for all business logic.
- **Zustand for global state** — Single store per domain (agent, provider, model).
- **TanStack Query for server state** — Use `useQuery`, `useMutation`.
- **Framer Motion for animations** — Wrap components with `motion.div`, use `initial`, `animate`, `exit`.
- **Tailwind for styling** — No CSS-in-JS, no inline styles (except dynamic values).
- **Component composition** — Small, focused components. Pass children as props.

### Testing

```typescript
// components/Chat/MessageBubble.test.tsx
import { render, screen } from '@testing-library/react';
import { MessageBubble } from './MessageBubble';

test('renders user message', () => {
  render(
    <MessageBubble
      message={{ id: 1, role: 'user', content: 'Hello', status: 'complete' }}
    />
  );
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

---

## Database Standards

### Migrations
- Use **Alembic** for schema versioning (production).
- Use **custom `migrations.py`** for idempotent SQLite ALTER TABLE during development.
- Migration naming: `migration_XXX_description.py` (e.g., `migration_004_add_tool_calls`).
- Always provide `upgrade()` and `downgrade()` (Alembic) or idempotent `ALTER TABLE IF NOT EXISTS`.

### Naming
- Tables: snake_case plural (`agents`, `execution_logs`).
- Columns: snake_case (`agent_id`, `created_at`).
- Foreign keys: `<table>_id` (`provider_id`).
- Indexes: `ix_<table>_<column>` (auto-generated).

### JSON Columns
- Use `JSON` type for flexible data (`tool_calls`, `capabilities`, `tools`).
- Default to empty list/object: `default=list` or `default=dict`.

---

## API Standards

### REST Conventions
| Operation | Method | Path | Response |
|-----------|--------|------|----------|
| List | GET | `/agents` | 200 + List[AgentResponse] |
| Get | GET | `/agents/{id}` | 200 + AgentResponse |
| Create | POST | `/agents` | 201 + AgentResponse |
| Update | PATCH | `/agents/{id}` | 200 + AgentResponse |
| Delete | DELETE | `/agents/{id}` | 204 |
| Custom action | POST | `/agents/{id}/test` | 200 + AgentTestResponse |

### Streaming
- Use **Server-Sent Events (SSE)** for streaming endpoints.
- Endpoint returns `StreamingResponse` with `text/event-stream`.
- Client uses `EventSource` or fetch with `ReadableStream`.

### Error Responses
```json
// 400 Validation Error
{ "detail": "Missing required field: name" }

// 404 Not Found
{ "detail": "Agent not found" }

// 500 Internal Error
{ "detail": "Internal server error", "message": "..." }
```

### Versioning
- All routes under `/api/v1/` prefix (configurable via `api_v1_prefix`).
- Breaking changes → new version `/api/v2/`.

---

## Git & Commit Standards

### Branch Naming
- `feature/<short-description>` — New features
- `fix/<short-description>` — Bug fixes
- `refactor/<short-description>` — Refactoring
- `docs/<short-description>` — Documentation
- `chore/<short-description>` — Maintenance

### Commit Messages (Conventional Commits)
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`.

Example:
```
feat(tools): add ToolManager with retry and cancellation

- Implement ToolExecutionConfig with exponential backoff
- Add PermissionValidator with wildcard support
- Integrate with AgentExecutionManager

Closes #42
```

### Pull Requests
- Title follows commit convention.
- Description includes: motivation, changes, testing, screenshots (UI).
- Require: CI passing, 1 approval, up-to-date with main.

---

## Documentation Standards

- All public APIs must have docstrings (Python) or JSDoc (TypeScript).
- Architecture decisions recorded in `docs/AI_CONTEXT/`.
- Update relevant `.md` files with every architectural change.
- Use Mermaid diagrams for architecture/flows.

---

## Security Standards

- **Never commit secrets** — Use `.env` (gitignored).
- **Encrypt API keys at rest** — Fernet encryption via `utils/security.py`.
- **Validate all inputs** — Pydantic on backend, Zod (planned) on frontend.
- **Parameterized queries only** — SQLAlchemy ORM prevents SQL injection.
- **CORS restricted** — Configure `cors_origins` in settings.

---

## Performance Standards

- **Database**: Use joined loading (`lazy="joined"`) for relationships needed in response.
- **Pagination**: All list endpoints support `skip`/`limit`.
- **Caching**: TanStack Query cache for frontend, model cache for provider models.
- **Streaming**: Chunked responses, no buffering in middleware.
- **Bundle size**: Code-split by route (`React.lazy`), tree-shake dependencies.

---

## Accessibility (Frontend)

- Semantic HTML (`<button>`, `<nav>`, `<main>`, `<section>`).
- ARIA labels for icon-only buttons.
- Focus visible outlines (Tailwind `focus-visible:ring-2`).
- Color contrast ratios (WCAG AA).
- Keyboard navigation for all interactive elements.

---

## Cross-References

- [Architecture](ARCHITECTURE.md) — Layer responsibilities
- [Project Structure](PROJECT_STRUCTURE.md) — File organization
- [UI Guidelines](UI_GUIDELINES.md) — Design system
- [Master Context](NEXUS_MASTER_CONTEXT.md) — Project overview