# NEXUS V3 - Phase 3: AI Runtime Implementation Plan

## 1. Architecture Analysis

### Existing Architecture

```
Chat Module
    │
    ├── ChatService (backend/services/chat_service.py)
    │       ├── send_message()
    │       └── stream_message()
    │
    ├── ProviderRegistry (backend/providers/__init__.py)
    │       ├── register(ProviderType, ProviderClass)
    │       └── get(ProviderType) -> ProviderClass
    │
    ├── BaseProvider (backend/providers/base.py)
    │       ├── chat(messages, model, **kwargs) -> str
    │       ├── stream(messages, model, **kwargs) -> AsyncGenerator[str, None]
    │       ├── health_check() -> HealthStatus
    │       └── list_models() -> List[Dict[str, Any]]
    │
    ├── Provider Implementations
    │       ├── OpenRouterProvider
    │       ├── GroqProvider
    │       ├── OllamaProvider
    │       ├── GeminiProvider
    │       └── LMStudioProvider
    │
    └── Database Models
            ├── Provider (name, type, api_key, base_url, is_active, health_status)
            └── Model (name, display_name, max_tokens, supports_streaming)
```

### Strengths

1. **Clean abstraction**: `BaseProvider` defines clear interface
2. **Registry pattern**: `ProviderRegistry` enables dynamic provider loading
3. **Streaming support**: All providers implement `stream()` method
4. **API key encryption**: `utils.security.encrypt_api_key()` protects credentials
5. **Health monitoring**: Providers expose `health_check()` for status tracking
6. **Database persistence**: Providers and models stored in SQLite

### Weaknesses

1. **Code duplication**: `OpenRouterProvider` and `GroqProvider` are nearly identical
   - Both use same OpenAI-compatible endpoint pattern
   - Both parse SSE `data: {...}` format identically
   - Reference: `backend/providers/openrouter.py:84-118` and `backend/providers/groq.py:78-112`

2. **No unified OpenAI-compatible provider**: Services like Ollama, LM Studio, Together AI, Fireworks AI all expose OpenAI-compatible APIs but require separate implementations

3. **Limited provider configuration**: `Provider` model lacks:
   - Timeout configuration
   - Custom headers
   - Priority/fallback order
   - Organization ID
   - Default model per provider

4. **No capability detection**: Cannot automatically determine if provider supports:
   - Streaming
   - Vision/images
   - Embeddings
   - Tool calling
   - Audio

5. **No caching**: Model lists and health status fetched on every request

6. **Tight coupling**: `ChatService` directly instantiates providers via `ProviderRegistry.get()`

7. **No usage tracking**: No token counting, cost calculation, or rate limit monitoring

8. **Inconsistent error handling**: Each provider handles errors differently

### Technical Debt

1. **Gemini provider**: Custom JSON line parsing instead of SSE
   - Reference: `backend/providers/gemini.py:105-120`
   - Uses `response.aiter_lines()` with raw JSON parsing
   - Different from OpenAI-compatible SSE format

2. **Hardcoded URLs**: Provider endpoints hardcoded in each implementation
   - OpenRouter: `https://openrouter.ai/api/v1/chat/completions`
   - Groq: `https://api.groq.com/openai/v1/chat/completions`
   - Should be configurable via `base_url`

3. **No retry logic**: Failed requests fail immediately without retry

4. **No timeout configuration**: All timeouts hardcoded to 60s

### Missing Abstractions

1. **AI Runtime Gateway**: No central orchestration layer
2. **Capability Manager**: No provider capability detection/exposure
3. **Usage Tracker**: No token counting or cost tracking
4. **Model Registry**: No centralized model metadata cache
5. **Fallback Manager**: No automatic provider fallback
6. **Request Router**: No intelligent provider selection

---

## 2. Gap Analysis

### Already Implemented

| Feature | Status | Location |
|---------|--------|----------|
| Provider registry | ✅ | `backend/providers/__init__.py` |
| Base provider interface | ✅ | `backend/providers/base.py` |
| 5 provider implementations | ✅ | `backend/providers/*.py` |
| API key encryption | ✅ | `backend/utils/security.py` |
| Provider CRUD API | ✅ | `backend/api/providers.py` |
| Model discovery | ✅ | `backend/services/provider_service.py` |
| Health checks | ✅ | All provider implementations |
| Streaming support | ✅ | All providers |
| Frontend provider management | ✅ | `frontend/src/pages/ProvidersPage.tsx` |

### Needs Improvement

| Feature | Current State | Target State |
|---------|--------------|--------------|
| OpenAI-compatible providers | 2 implementations (OpenRouter, Groq) | 1 generic implementation for all |
| Provider configuration | Basic (name, type, api_key, base_url) | Full (timeout, headers, priority, default_model) |
| Error handling | Inconsistent per provider | Standardized with retry logic |
| Model caching | None | Cache with TTL |
| Health status caching | None | Cache with configurable interval |
| Capability detection | Manual `supports_streaming` flag | Automatic detection |
| Usage tracking | None | Token counting, cost estimation |

### Missing Completely

| Feature | Priority | Description |
|---------|----------|-------------|
| AI Runtime Gateway | P0 | Central orchestration layer for all AI requests |
| OpenAI-compatible provider | P0 | Single implementation for OpenAI-compatible APIs |
| Capability Manager | P1 | Auto-detect provider capabilities |
| Usage Tracker | P1 | Token counting, cost calculation, rate limits |
| Model Registry Cache | P1 | Centralized model metadata with TTL |
| Fallback Manager | P2 | Automatic provider fallback on failure |
| Request Router | P2 | Intelligent provider selection based on capabilities/cost |
| Connection pooling | P2 | Reuse HTTP connections across requests |
| Rate limiter | P2 | Per-provider rate limiting |
| Audit log | P3 | Track all AI requests for compliance |

### Recommendations

1. **Create `OpenAICompatibleProvider`**: Consolidate OpenRouter, Groq, Ollama, LM Studio into one implementation
2. **Add `AI_RUNTIME.md` architecture document**: Define clear boundaries between modules
3. **Extend `Provider` model**: Add configuration fields for timeout, headers, priority
4. **Create `Capability` model**: Store detected capabilities per provider
5. **Add `Usage` model**: Track token usage and costs
6. **Create `AIRuntime` service**: Central gateway for all AI operations
7. **Update frontend**: Display capabilities, health, latency, usage stats

---

## 3. AI Runtime Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEXUS V3                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬────────┤
│    Chat     │   Memory    │   Planner   │  Workflow   │  ...   │
├─────────────┴─────────────┴─────────────┴─────────────┴────────┤
│                      AI Runtime Gateway                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Request Router  │  Capability Manager  │  Usage Tracker  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Provider Registry (Enhanced)                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │   OpenAI    │  │   Gemini    │  │   Custom    │  ...  │  │
│  │  │ Compatible  │  │  Native     │  │  Provider   │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 3.1 AI Runtime Gateway (`backend/services/ai_runtime.py`)

**Purpose**: Single entry point for all AI operations across all modules.

```python
class AIRuntime:
    """Central gateway for all AI operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.registry = ProviderRegistry()
        self.capability_manager = CapabilityManager(db)
        self.usage_tracker = UsageTracker(db)
        self.model_cache = ModelCache()
    
    async def chat(self, messages, provider_id=None, model=None, **kwargs):
        """Route chat request to appropriate provider."""
        provider = self._resolve_provider(provider_id, model, kwargs)
        return await provider.chat(messages, model, **kwargs)
    
    async def stream(self, messages, provider_id=None, model=None, **kwargs):
        """Route streaming request to appropriate provider."""
        provider = self._resolve_provider(provider_id, model, kwargs)
        async for chunk in provider.stream(messages, model, **kwargs):
            yield chunk
    
    def _resolve_provider(self, provider_id, model, requirements):
        """Select provider based on requirements."""
        # 1. Check if specific provider requested
        # 2. Check capabilities match requirements
        # 3. Check provider health
        # 4. Fallback to default provider
        pass
```

#### 3.2 OpenAI-Compatible Provider (`backend/providers/openai_compatible.py`)

**Purpose**: Single implementation for all OpenAI-compatible APIs.

```python
class OpenAICompatibleProvider(BaseProvider):
    """Generic provider for OpenAI-compatible APIs."""
    
    def __init__(self, api_key, base_url, chat_path="/chat/completions"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat_path = chat_path
    
    async def chat(self, messages, model, **kwargs):
        """Send chat completion request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.chat_path}",
                headers=self._headers(),
                json={"model": model, "messages": messages, **kwargs},
                timeout=self._timeout(),
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    
    async def stream(self, messages, model, **kwargs):
        """Stream chat completion."""
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", ...) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
```

**Providers that use this implementation**:
- OpenRouter
- Groq
- Ollama
- LM Studio
- Together AI
- Fireworks AI
- DeepInfra
- LocalAI
- LiteLLM
- vLLM
- OpenWebUI
- Any custom OpenAI-compatible API

**Configuration per provider**:
```python
PROVIDER_CONFIGS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
    },
}
```

#### 3.3 Capability Manager (`backend/services/capability_manager.py`)

**Purpose**: Detect and expose provider capabilities.

```python
class CapabilityManager:
    """Detect and manage provider capabilities."""
    
    CAPABILITIES = {
        "streaming": "Supports streaming responses",
        "vision": "Supports image inputs",
        "embeddings": "Supports embedding generation",
        "tools": "Supports function calling",
        "images": "Supports image generation",
        "audio": "Supports audio input/output",
        "reasoning": "Supports extended reasoning",
    }
    
    async def detect_capabilities(self, provider) -> Dict[str, bool]:
        """Auto-detect provider capabilities."""
        capabilities = {}
        
        # Check streaming via model metadata
        models = await provider.list_models()
        capabilities["streaming"] = any(m.get("supports_streaming") for m in models)
        
        # Check vision via model names
        capabilities["vision"] = any(
            "vision" in m.get("name", "").lower() or 
            "multimodal" in m.get("name", "").lower()
            for m in models
        )
        
        # Check tools via model metadata
        capabilities["tools"] = any(
            m.get("supports_tools") or m.get("supports_function_calling")
            for m in models
        )
        
        return capabilities
```

#### 3.4 Usage Tracker (`backend/services/usage_tracker.py`)

**Purpose**: Track token usage and costs.

```python
class UsageTracker:
    """Track AI usage and costs."""
    
    MODEL_COSTS = {
        "gpt-4o": {"input": 2.50, "output": 10.00},  # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "llama-3.3-70b": {"input": 0.00, "output": 0.00},
        # ... more models
    }
    
    def track_usage(self, provider, model, input_tokens, output_tokens):
        """Record usage for billing/analytics."""
        pass
    
    def estimate_cost(self, model, input_tokens, output_tokens) -> float:
        """Estimate cost for a request."""
        pass
```

#### 3.5 Model Registry Cache (`backend/services/model_cache.py`)

**Purpose**: Cache model metadata with TTL.

```python
class ModelCache:
    """Cache model metadata with TTL."""
    
    def __init__(self, ttl_seconds=3600):
        self.ttl = ttl_seconds
        self._cache = {}
    
    async def get_models(self, provider_id: int) -> List[Dict]:
        """Get models from cache or fetch fresh."""
        if provider_id in self._cache:
            entry = self._cache[provider_id]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["models"]
        
        # Fetch fresh models
        models = await self._fetch_models(provider_id)
        self._cache[provider_id] = {
            "models": models,
            "timestamp": time.time(),
        }
        return models
```

---

## 4. Database Changes

### 4.1 Provider Model Extensions

```python
# backend/models/provider.py

class Provider(BaseModel):
    """Provider model."""
    __tablename__ = "providers"
    
    # Existing fields
    name = Column(String(255), nullable=False)
    type = Column(Enum(ProviderType), nullable=False)
    api_key = Column(Text, nullable=True)
    base_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    health_status = Column(Enum(ProviderStatus), default=ProviderStatus.CHECKING)
    last_checked = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # NEW fields
    default_model = Column(String(255), nullable=True)  # Default model for this provider
    timeout = Column(Integer, default=60)  # Request timeout in seconds
    priority = Column(Integer, default=0)  # Higher = preferred
    custom_headers = Column(Text, nullable=True)  # JSON: {"X-Custom": "value"}
    max_retries = Column(Integer, default=3)  # Retry failed requests
    organization_id = Column(String(255), nullable=True)  # For OpenAI orgs
    capabilities = Column(Text, nullable=True)  # JSON: {"streaming": true, "vision": false}
    
    # Relationships
    models = relationship("Model", back_populates="provider", cascade="all, delete-orphan")
    usages = relationship("Usage", back_populates="provider", cascade="all, delete-orphan")
```

### 4.2 New: Capability Model

```python
# backend/models/capability.py

class Capability(BaseModel):
    """Provider capability cache."""
    __tablename__ = "capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    streaming = Column(Boolean, default=False)
    vision = Column(Boolean, default=False)
    embeddings = Column(Boolean, default=False)
    tools = Column(Boolean, default=False)
    images = Column(Boolean, default=False)
    audio = Column(Boolean, default=False)
    reasoning = Column(Boolean, default=False)
    detected_at = Column(String(50), nullable=True)
    
    provider = relationship("Provider", back_populates="capabilities")
```

### 4.3 New: Usage Model

```python
# backend/models/usage.py

class Usage(BaseModel):
    """AI usage tracking."""
    __tablename__ = "usages"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model = Column(String(255), nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)  # Estimated cost in USD
    request_type = Column(String(50), nullable=False)  # "chat" or "stream"
    created_at = Column(String(50), nullable=True)
    
    provider = relationship("Provider", back_populates="usages")
```

### 4.4 Migration

```python
# alembic/versions/XXXX_add_ai_runtime_fields.py

def upgrade():
    # Add new columns to providers
    op.add_column("providers", sa.Column("default_model", sa.String(255), nullable=True))
    op.add_column("providers", sa.Column("timeout", sa.Integer, default=60))
    op.add_column("providers", sa.Column("priority", sa.Integer, default=0))
    op.add_column("providers", sa.Column("custom_headers", sa.Text, nullable=True))
    op.add_column("providers", sa.Column("max_retries", sa.Integer, default=3))
    op.add_column("providers", sa.Column("organization_id", sa.String(255), nullable=True))
    op.add_column("providers", sa.Column("capabilities", sa.Text, nullable=True))
    
    # Create capabilities table
    op.create_table("capabilities", ...)
    
    # Create usages table
    op.create_table("usages", ...)

def downgrade():
    op.drop_table("usages")
    op.drop_table("capabilities")
    op.drop_column("providers", "capabilities")
    op.drop_column("providers", "organization_id")
    # ... etc
```

---

## 5. API Design

### 5.1 New AI Runtime Endpoints

```python
# backend/api/ai_runtime.py

router = APIRouter()

@router.post("/ai/chat")
async def ai_chat(request: AIRequest, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Unified chat endpoint for all modules."""
    pass

@router.post("/ai/stream")
async def ai_stream(request: AIRequest, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Unified streaming endpoint for all modules."""
    pass

@router.get("/ai/providers/{provider_id}/capabilities")
async def get_capabilities(provider_id: int, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Get detected capabilities for a provider."""
    pass

@router.get("/ai/providers/{provider_id}/usage")
async def get_usage(provider_id: int, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Get usage statistics for a provider."""
    pass

@router.post("/ai/providers/{provider_id}/refresh-models")
async def refresh_models(provider_id: int, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Force refresh model cache."""
    pass
```

### 5.2 Enhanced Provider Endpoints

```python
# Add to backend/api/providers.py

@router.get("/providers/{provider_id}/capabilities")
async def get_provider_capabilities(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Get provider capabilities."""
    pass

@router.post("/providers/{provider_id}/test-stream")
async def test_provider_stream(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Test streaming capability."""
    pass

@router.get("/providers/{provider_id}/usage")
async def get_provider_usage(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Get provider usage stats."""
    pass
```

### 5.3 Request/Response Schemas

```python
# backend/schemas/ai_runtime.py

class AIRequest(BaseModel):
    provider_id: Optional[int] = None
    model: Optional[str] = None
    messages: List[Dict[str, Any]]
    stream: bool = False
    requirements: Optional[Dict[str, Any]] = None  # {"vision": true, "tools": true}
    metadata: Optional[Dict[str, Any]] = None  # {"module": "chat", "conversation_id": 1}

class AIResponse(BaseModel):
    content: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[float] = None
    finish_reason: Optional[str] = None

class CapabilityResponse(BaseModel):
    provider_id: int
    capabilities: Dict[str, bool]
    detected_at: str
    models_count: int
```

---

## 6. Frontend Design

### 6.1 Enhanced Providers Page

**New features**:
- Capability badges (Streaming, Vision, Tools, etc.)
- Health status with latency
- Usage statistics
- Default provider/model selection
- Priority ordering
- Connection test with timing

### 6.2 New Components

```
frontend/src/components/Providers/
├── ProviderCard.tsx (existing - enhance)
├── ProviderForm.tsx (existing - enhance)
├── ProviderList.tsx (existing - enhance)
├── ProviderStatus.tsx (existing - enhance)
├── CapabilityBadge.tsx (NEW)
├── UsageStats.tsx (NEW)
├── ModelCache.tsx (NEW)
└── ProviderTest.tsx (NEW)
```

### 6.3 Provider Form Enhancements

```typescript
// Add to ProviderForm.tsx
interface ProviderFormData {
  name: string;
  type: string;
  api_key: string;
  base_url: string;
  default_model: string;
  timeout: number;
  priority: number;
  max_retries: number;
  custom_headers: string;  // JSON textarea
  organization_id: string;
}
```

### 6.4 API Client

```typescript
// frontend/src/api/ai-runtime.ts
export const aiRuntimeApi = {
  chat: async (data: AIRequest): Promise<AIResponse> => { ... },
  stream: async (data: AIRequest): Promise<ReadableStream> => { ... },
  getCapabilities: async (providerId: number): Promise<CapabilityResponse> => { ... },
  getUsage: async (providerId: number): Promise<UsageStats> => { ... },
  refreshModels: async (providerId: number): Promise<void> => { ... },
}
```

---

## 7. Testing Plan

### 7.1 Backend Tests

| Test Category | Tests | Location |
|--------------|-------|----------|
| OpenAICompatibleProvider | Chat, stream, health, models | `backend/tests/test_openai_compatible_provider.py` |
| AIRuntime | Routing, fallback, capability matching | `backend/tests/test_ai_runtime.py` |
| CapabilityManager | Detection, caching | `backend/tests/test_capability_manager.py` |
| UsageTracker | Token counting, cost estimation | `backend/tests/test_usage_tracker.py` |
| ModelCache | TTL, invalidation | `backend/tests/test_model_cache.py` |
| Migration | Schema changes | `backend/tests/test_migration.py` |

### 7.2 Frontend Tests

| Test Category | Tests | Location |
|--------------|-------|----------|
| CapabilityBadge | Render, colors | `frontend/src/components/Providers/CapabilityBadge.test.tsx` |
| UsageStats | Display stats | `frontend/src/components/Providers/UsageStats.test.tsx` |
| ProviderForm | New fields | `frontend/src/components/Providers/ProviderForm.test.tsx` |

### 7.3 Integration Tests

| Test | Description |
|------|-------------|
| E2E streaming | Send message, verify stream with new provider |
| Capability detection | Add provider, verify capabilities auto-detected |
| Fallback | Disable provider, verify fallback works |
| Usage tracking | Send messages, verify usage recorded |

### 7.4 Manual Tests

| Test | Steps |
|------|-------|
| Add OpenAI provider | Configure, test connection, view models |
| Add Groq provider | Verify uses OpenAICompatibleProvider |
| Add Ollama provider | Verify localhost connection works |
| Capability display | Verify badges show on provider cards |
| Usage stats | Verify stats update after messages |

---

## 8. Documentation Plan

### 8.1 Files to Update

| File | Changes |
|------|---------|
| `docs/architecture/AI_RUNTIME.md` | NEW - Architecture overview |
| `docs/reports/IMPLEMENTATION_REPORT.md` | Add Phase 3 section |
| `docs/testing/TEST_RESULTS.md` | Add Phase 3 results |
| `docs/reports/STATUS.md` | Update current sprint |
| `CHANGELOG.md` | Add Phase 3 entries |
| `docs/api/API_REFERENCE.md` | Add AI Runtime endpoints |

### 8.2 New Documentation

```
docs/architecture/
├── AI_RUNTIME.md          # Architecture overview
├── PROVIDERS.md           # Provider implementation guide
└── CAPABILITIES.md        # Capability detection spec

docs/implementation/
├── PHASE_03_AI_RUNTIME.md # Implementation details
```

---

## 9. Rollback Plan

### 9.1 Database Rollback

```bash
cd backend
alembic downgrade -1  # Revert last migration
```

### 9.2 Code Rollback

```bash
git revert HEAD~3..HEAD  # Revert Phase 3 commits
```

### 9.3 Feature Flags

```python
# backend/config.py
AI_RUNTIME_ENABLED = os.getenv("AI_RUNTIME_ENABLED", "false").lower() == "true"
```

```python
# backend/api/chat.py
if settings.AI_RUNTIME_ENABLED:
    runtime = AIRuntime(db)
    # Use new runtime
else:
    # Use existing provider registry
```

---

## 10. Phase Task Breakdown

### Task 1: Database Migration
- [ ] Create Alembic migration for new columns/tables
- [ ] Add `Provider` model extensions
- [ ] Create `Capability` model
- [ ] Create `Usage` model
- [ ] Run migration and verify

### Task 2: OpenAI-Compatible Provider
- [ ] Create `OpenAICompatibleProvider` class
- [ ] Implement `chat()`, `stream()`, `health_check()`, `list_models()`
- [ ] Add provider configs for OpenRouter, Groq, Ollama, LM Studio
- [ ] Update `ProviderRegistry` to use new provider
- [ ] Remove old `OpenRouterProvider`, `GroqProvider`, `OllamaProvider`, `LMStudioProvider`
- [ ] Keep `GeminiProvider` as native implementation

### Task 3: Capability Manager
- [ ] Create `CapabilityManager` service
- [ ] Implement capability detection logic
- [ ] Add caching with TTL
- [ ] Create API endpoint
- [ ] Add tests

### Task 4: Usage Tracker
- [ ] Create `UsageTracker` service
- [ ] Implement token counting
- [ ] Implement cost estimation
- [ ] Create `Usage` model and repository
- [ ] Add API endpoint
- [ ] Add tests

### Task 5: Model Cache
- [ ] Create `ModelCache` service
- [ ] Implement TTL-based caching
- [ ] Add invalidation logic
- [ ] Integrate with provider service

### Task 6: AI Runtime Gateway
- [ ] Create `AIRuntime` service
- [ ] Implement provider resolution logic
- [ ] Add fallback mechanism
- [ ] Integrate with ChatService
- [ ] Create API endpoints
- [ ] Add tests

### Task 7: Frontend Enhancements
- [ ] Add `CapabilityBadge` component
- [ ] Add `UsageStats` component
- [ ] Enhance `ProviderForm` with new fields
- [ ] Enhance `ProviderCard` with capabilities/usage
- [ ] Add API client methods
- [ ] Add tests

### Task 8: Integration & Testing
- [ ] Run backend tests
- [ ] Run frontend tests
- [ ] Run `npm run build`, `lint`, `type-check`
- [ ] Manual E2E testing
- [ ] Verify Chat module still works

### Task 9: Documentation
- [ ] Write `docs/architecture/AI_RUNTIME.md`
- [ ] Update `docs/reports/IMPLEMENTATION_REPORT.md`
- [ ] Update `docs/testing/TEST_RESULTS.md`
- [ ] Update `docs/reports/STATUS.md`
- [ ] Update `CHANGELOG.md`
- [ ] Update `docs/api/API_REFERENCE.md`

### Task 10: Lock Phase
- [ ] Final verification
- [ ] Lock Phase 3
- [ ] Prepare Phase 4 plan

---

## Appendix: File Reference Map

### Backend Files to Create
```
backend/services/ai_runtime.py
backend/services/capability_manager.py
backend/services/usage_tracker.py
backend/services/model_cache.py
backend/providers/openai_compatible.py
backend/schemas/ai_runtime.py
backend/models/capability.py
backend/models/usage.py
backend/api/ai_runtime.py
```

### Backend Files to Modify
```
backend/models/provider.py          # Add new columns
backend/providers/__init__.py       # Update registration
backend/services/chat_service.py    # Use AI Runtime
backend/services/provider_service.py # Add capability/usage methods
backend/api/providers.py            # Add new endpoints
backend/config.py                   # Add AI_RUNTIME_ENABLED flag
```

### Frontend Files to Create
```
frontend/src/components/Providers/CapabilityBadge.tsx
frontend/src/components/Providers/UsageStats.tsx
frontend/src/components/Providers/ModelCache.tsx
frontend/src/api/ai-runtime.ts
```

### Frontend Files to Modify
```
frontend/src/components/Providers/ProviderForm.tsx
frontend/src/components/Providers/ProviderCard.tsx
frontend/src/pages/ProvidersPage.tsx
frontend/src/types/provider.ts
```
