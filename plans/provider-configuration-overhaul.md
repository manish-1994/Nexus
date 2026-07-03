# Provider Configuration Overhaul - Implementation Plan

## Current State Analysis

### Backend
- `ProviderType` enum: OPENROUTER, GROQ, OLLAMA, GEMINI, LMSTUDIO, OPENAI_COMPATIBLE
- `Provider` model has all necessary fields
- `ProviderService` handles CRUD + test_connection + discover_models
- `ProviderRepository` basic CRUD
- No model discovery automation for OpenAI-compatible endpoints
- Capabilities stored as JSON text blob

### Frontend
- `ProviderForm`: static form, no dynamic fields
- `ProviderList`: basic card display
- `ProviderCard`: minimal info
- No provider icons
- No capability badges
- No validation beyond HTML5 required

## Gaps to Close

1. Provider type dropdown missing many types
2. Form doesn't adjust fields per provider type
3. No auto-discovery for OpenAI-compatible base_url/models
4. No provider icons
5. Capabilities not displayed
6. Limited validation
7. Chat page shows all providers, not just active/configured

## Implementation Plan

### Phase 1: Backend Foundation

#### Task 1: Expand ProviderType Enum
- Add: ANTHROPIC, OPENAI, NVIDIA_NIM, AZURE_OPENAI, MISTRAL, TOGETHER_AI, DEEPSEEK, COHERE, XAI, PERPLEXITY, CUSTOM
- Keep existing values for backward compatibility
- File: `backend/models/provider.py`

#### Task 2: Add Validation Service
- Create `backend/services/provider_validation_service.py`
- Validate: name uniqueness, URL format, API key required for non-local providers
- Return structured validation errors

#### Task 3: Enhance Model Discovery
- Update `ProviderService.discover_models()` to support OpenAI-compatible auto-discovery
- Add `GET {base_url}/models` fetcher
- Save discovered models to database
- File: `backend/services/provider_service.py`

#### Task 4: Add Provider Config Schema
- Create `backend/schemas/provider_config.py`
- Define per-type configuration requirements
- Which fields are required/optional per provider type

### Phase 2: Frontend Form Overhaul

#### Task 5: Dynamic Provider Form
- Rewrite `ProviderForm.tsx` to adjust fields based on provider type
- Local providers (Ollama, LM Studio): hide API key field
- OpenAI-compatible: show base_url prominently, auto-discover button
- Cloud providers: show API key, optional base_url
- Add validation UI (red borders, error messages)
- File: `frontend/src/components/Providers/ProviderForm.tsx`

#### Task 6: Provider Icons
- Create icon mapping component
- Use emoji/SVG icons per provider type
- Display in ProviderCard and sidebar
- File: `frontend/src/components/Providers/ProviderIcon.tsx` (new)

#### Task 7: Capability Badges
- Enhance `CapabilityBadge` component
- Show: Streaming, Vision, Function Calling, Reasoning, Embeddings
- Color-coded by support status
- File: `frontend/src/components/Providers/CapabilityBadge.tsx`

#### Task 8: Enhanced Provider Card
- Add icon, capabilities, model count, health status
- Better layout with metadata
- File: `frontend/src/components/Providers/ProviderCard.tsx`

### Phase 3: API & Type Updates

#### Task 9: Update API Schemas
- Add validation error response schema
- Ensure all 16 provider types exposed
- File: `backend/schemas/provider.py`

#### Task 10: Update Frontend Types
- Add ProviderType enum to TypeScript
- Update Provider interface
- File: `frontend/src/types/provider.ts`

#### Task 11: Update API Client
- Add validation endpoint
- Ensure discover_models returns proper types
- File: `frontend/src/api/providers.ts`

### Phase 4: Chat Page Integration

#### Task 12: Filter Active Providers
- Update `ProviderModelSelector` to only show active providers
- Show only providers with valid configuration
- File: `frontend/src/components/Chat/ProviderModelSelector.tsx`

### Phase 5: Migration & Testing

#### Task 13: Database Migration
- No schema changes needed (type column already exists)
- Update existing provider types to new enum values if needed
- Verify no data loss

#### Task 14: Comprehensive Testing
- Test each provider type form
- Test validation rules
- Test model discovery
- Test capability detection
- Backend tests: all pass
- Frontend: lint, type-check, build pass

## Files to Modify

### Backend
1. `backend/models/provider.py` - Expand ProviderType enum
2. `backend/services/provider_validation_service.py` - New validation service
3. `backend/services/provider_service.py` - Enhance discover_models
4. `backend/schemas/provider.py` - Update schemas
5. `backend/api/providers.py` - Add validation endpoint

### Frontend
1. `frontend/src/types/provider.ts` - Add ProviderType enum
2. `frontend/src/components/Providers/ProviderForm.tsx` - Dynamic form
3. `frontend/src/components/Providers/ProviderIcon.tsx` - New icon component
4. `frontend/src/components/Providers/CapabilityBadge.tsx` - Enhanced badges
5. `frontend/src/components/Providers/ProviderCard.tsx` - Enhanced card
6. `frontend/src/components/Chat/ProviderModelSelector.tsx` - Filter active providers
7. `frontend/src/api/providers.ts` - Update API client

## Execution Order

1. Backend enum expansion (backward compatible)
2. Validation service
3. Enhanced model discovery
4. Frontend type updates
5. Dynamic form
6. Icons and badges
7. Chat page filtering
8. Testing and verification

## Risk Mitigation

- All changes are additive or backward compatible
- Existing provider types remain valid
- No database schema changes required
- Form defaults to current behavior for unknown types
- Validation is opt-in via new endpoint
