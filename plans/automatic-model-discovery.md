# NEXUS V3 - Automatic Model Discovery Implementation Plan

## Current State Analysis

### Existing Implementation
- ProviderForm: Basic form with manual model name input
- ProviderModelSelector: Loads models from backend, has "Sync Models" button
- Backend: `discover_models()` in ProviderService, OpenAI-compatible provider has `list_models()`
- Database: Models stored with provider_id, name, display_name, max_tokens, supports_streaming

### Gaps
1. No searchable Base URL field
2. No automatic discovery trigger based on provider type
3. Default Model is a simple text input, not a dropdown
4. No provider-specific discovery strategies
5. No caching/refresh mechanism
6. Chat doesn't auto-load models on provider selection

## Implementation Plan

### Phase 1: Backend - Model Discovery Enhancement

#### Task 1.1: Update Provider Models for Discovery
**File:** `backend/providers/*.py`
- Ensure all provider types implement `list_models()`:
  - `openai_compatible`: GET {base_url}/models ✓ (exists)
  - `openai`: GET https://api.openai.com/v1/models
  - `anthropic`: GET https://api.anthropic.com/v1/models
  - `gemini`: Use Google discovery endpoint
  - `groq`: GET https://api.groq.com/openai/v1/models
  - `openrouter`: GET https://openrouter.ai/api/v1/models
  - `ollama`: GET {base_url}/api/tags ✓ (exists)
  - `lmstudio`: GET {base_url}/v1/models
  - `nvidia_nim`: GET {base_url}/models
  - `azure_openai`: GET {base_url}/openai/deployments
  - `mistral`: GET https://api.mistral.ai/v1/models
  - `together_ai`: GET https://api.together.xyz/v1/models
  - `deepseek`: GET https://api.deepseek.com/v1/models
  - `cohere`: GET https://api.cohere.com/v1/models
  - `xai`: GET https://api.x.ai/v1/models
  - `perplexity`: GET https://api.perplexity.ai/v1/models
  - `custom`: GET {base_url}/models

#### Task 1.2: Enhance Model Schema
**File:** `backend/models/model.py`
- Add fields: `context_length`, `supports_vision`, `supports_reasoning`, `is_deprecated`
- Update Model class with new columns

#### Task 1.3: Update Model Discovery Service
**File:** `backend/services/provider_service.py`
- Enhance `discover_models()` to:
  - Handle provider-specific discovery
  - Update existing models instead of duplicating
  - Set additional model metadata
  - Return discovered models with full details

#### Task 1.4: Add Model Cache Endpoint
**File:** `backend/api/providers.py`
- Add `GET /providers/{provider_id}/models/cached` - returns cached models without re-fetching
- Add `POST /providers/{provider_id}/models/refresh` - force refresh from provider

### Phase 2: Frontend - Provider Form Redesign

#### Task 2.1: Update Provider Types
**File:** `frontend/src/types/provider.ts`
- Add `ModelCapabilities` interface: context_length, supports_vision, supports_reasoning, is_deprecated
- Update `Model` interface with new fields

#### Task 2.2: Create SearchableSelect Component
**File:** `frontend/src/components/common/SearchableSelect.tsx` (new)
- Reusable searchable dropdown component
- Props: options, value, onChange, placeholder, disabled
- Features: filter options, keyboard navigation, clear selection

#### Task 2.3: Redesign ProviderForm
**File:** `frontend/src/components/Providers/ProviderForm.tsx`
Changes:
1. Replace Base URL input with searchable URL field
2. Add "Discover Models" button (disabled until base_url + api_key valid)
3. Add model discovery status indicator
4. Replace Default Model text input with SearchableSelect dropdown
5. Show discovered models list with capabilities
6. Add "Refresh Models" button if models already discovered
7. Show loading state during discovery
8. Handle discovery errors with toast

State additions:
- `discoveredModels`: Model[]
- `isDiscovering`: boolean
- `discoveryError`: string | null
- `hasDiscovered`: boolean

#### Task 2.4: Update ProviderForm Submission
- On submit, if models were discovered, include them
- If default_model selected from dropdown, use that value
- Don't block form submission if discovery fails

### Phase 3: Frontend - Chat Integration

#### Task 3.1: Auto-load Models on Provider Selection
**File:** `frontend/src/components/Chat/ProviderModelSelector.tsx`
Changes:
1. When provider changes, automatically fetch models
2. Show loading state while fetching
3. Populate model dropdown with fetched models
4. Disable Send button until model selected
5. Show model count and discovery status

#### Task 3.2: Enhance Model Display
**File:** `frontend/src/components/Chat/ProviderModelSelector.tsx`
- Show model capabilities in dropdown:
  - Context length
  - Streaming support
  - Vision support
  - Reasoning support
- Show deprecated warning for deprecated models

### Phase 4: Testing & Verification

#### Task 4.1: Backend Tests
- Test model discovery for each provider type
- Test model caching
- Test refresh endpoint
- Test error handling

#### Task 4.2: Frontend Tests
- Test ProviderForm discovery flow
- Test SearchableSelect component
- Test Chat auto-load models
- Test error states

#### Task 4.3: Integration Tests
- Test full flow: create provider → discover models → select in chat
- Test refresh models
- Test error recovery

## Acceptance Criteria Checklist

- [ ] Models are discovered automatically when "Discover Models" clicked
- [ ] Default Model is a searchable dropdown populated with discovered models
- [ ] Chat uses discovered models only (no manual entry)
- [ ] Build passes
- [ ] Lint passes
- [ ] Type-check passes
- [ ] Existing providers with models continue to work
- [ ] Discovery failures show toast, keep form editable
- [ ] Refresh Models button available for previously discovered providers
- [ ] Send button disabled until model selected

## Files to Modify

### Backend
1. `backend/models/model.py` - Add new model fields
2. `backend/providers/*.py` - Ensure all providers implement list_models()
3. `backend/services/provider_service.py` - Enhance discovery
4. `backend/api/providers.py` - Add cache/refresh endpoints
5. `backend/schemas/model.py` - Update schemas

### Frontend
1. `frontend/src/types/provider.ts` - Update interfaces
2. `frontend/src/components/common/SearchableSelect.tsx` - New component
3. `frontend/src/components/Providers/ProviderForm.tsx` - Major redesign
4. `frontend/src/components/Chat/ProviderModelSelector.tsx` - Auto-load models
5. `frontend/src/api/providers.ts` - Add new API methods

## Estimated Complexity

- Backend: Medium (mostly adding discovery endpoints to existing providers)
- Frontend: High (form redesign, new component, state management)
- Testing: Medium
