# NEXUS V3 - Phase 2: AI Provider Runtime

## Overview

This document describes the implementation of Phase 2: AI Provider Runtime for NEXUS V3.

## Objectives

- Implement provider abstraction layer with base interface
- Support 5 AI providers: OpenRouter, Groq, Ollama, Gemini, LM Studio
- Add health monitoring for providers
- Enable model discovery
- Create provider management API with CRUD operations
- Build frontend provider management page
- Implement API key encryption for secure storage

## Completed Tasks

### 1. Provider Interface and Registry

- `backend/providers/base.py` - Abstract base provider class with:
  - `BaseProvider` abstract class defining the provider interface
  - `ProviderType` enum (OPENROUTER, GROQ, OLLAMA, GEMINI, LMSTUDIO)
  - `HealthStatus` enum (ACTIVE, INACTIVE, ERROR, CHECKING)
  - Abstract methods: `chat()`, `stream()`, `health_check()`, `list_models()`, `get_provider_type()`

- `backend/providers/__init__.py` - Provider registry with:
  - `ProviderRegistry` class for registering and retrieving providers
  - `_register_providers()` function to auto-register all providers

### 2. Provider Implementations

- `backend/providers/openrouter.py` - OpenRouter provider implementation
- `backend/providers/groq.py` - Groq provider implementation
- `backend/providers/ollama.py` - Ollama provider implementation (local HTTP API)
- `backend/providers/gemini.py` - Gemini provider implementation
- `backend/providers/lmstudio.py` - LM Studio provider implementation (local HTTP API)

### 3. Backend Service Layer

- `backend/services/provider_service.py` - Provider service with:
  - CRUD operations for providers
  - `test_connection()` - Test provider connectivity
  - `discover_models()` - Fetch available models from provider
  - API key encryption/decryption using Fernet

- `backend/repositories/provider_repository.py` - Provider repository with:
  - Generic CRUD operations
  - `find_by_type()` - Find provider by type
  - `find_active()` - Find active providers

### 4. API Endpoints

- `backend/api/providers.py` - Provider API endpoints:
  - `GET /providers` - List all providers
  - `POST /providers` - Create new provider
  - `GET /providers/{id}` - Get provider details
  - `PUT /providers/{id}` - Update provider
  - `DELETE /providers/{id}` - Delete provider
  - `POST /providers/{id}/test` - Test provider connection
  - `POST /providers/{id}/models` - Discover models from provider
  - `GET /providers/{id}/models` - List provider models
  - `DELETE /providers/{id}/models/{model_id}` - Delete model

### 5. Database Models

- `backend/models/provider.py` - Updated with:
  - `ProviderType` enum
  - `ProviderStatus` enum
  - Relationship to Model (`models`)
  - Fields: name, type, base_url, api_key (encrypted), health_status, last_checked

- `backend/models/model.py` - Updated with:
  - Relationship to Provider (`provider`)
  - Fields: name, provider_id, context_length, pricing

### 6. Frontend Implementation

- `frontend/src/api/providers.ts` - Provider API client
- `frontend/src/types/provider.ts` - TypeScript interfaces
- `frontend/src/components/Providers/ProviderCard.tsx` - Provider display card
- `frontend/src/components/Providers/ProviderList.tsx` - Grid list of providers
- `frontend/src/components/Providers/ProviderForm.tsx` - Add/edit provider form
- `frontend/src/components/Providers/ProviderStatus.tsx` - Status indicator
- `frontend/src/pages/ProvidersPage.tsx` - Provider management page
- `frontend/src/App.tsx` - Updated with `/providers` route
- `frontend/src/components/Layout/Sidebar.tsx` - Updated navigation

## Directory Structure

```
NEXUS-V3/
├── backend/
│   ├── providers/
│   │   ├── __init__.py          # Registry and factory
│   │   ├── base.py              # Base provider interface
│   │   ├── openrouter.py        # OpenRouter implementation
│   │   ├── groq.py              # Groq implementation
│   │   ├── ollama.py            # Ollama implementation
│   │   ├── gemini.py            # Gemini implementation
│   │   └── lmstudio.py          # LM Studio implementation
│   ├── services/
│   │   └── provider_service.py  # Provider business logic
│   ├── repositories/
│   │   └── provider_repository.py # Provider data access
│   ├── schemas/
│   │   ├── provider.py          # Provider schemas
│   │   └── model.py             # Model schemas
│   └── api/
│       └── providers.py         # Provider API endpoints
└── frontend/
    └── src/
        ├── api/
        │   └── providers.ts     # Provider API client
        ├── types/
        │   └── provider.ts      # TypeScript interfaces
        ├── components/
        │   └── Providers/       # Provider components
        └── pages/
            └── ProvidersPage.tsx # Provider management page
```

## Technology Stack

### Backend
- FastAPI - Web framework
- SQLAlchemy 2.0 - ORM
- Pydantic - Data validation
- Cryptography (Fernet) - API key encryption
- httpx - HTTP client for provider APIs

### Frontend
- React 18 - UI library
- TypeScript - Type safety
- Tailwind CSS - Styling
- React Query - Server state management
- Axios - HTTP client

## Key Features

### Provider Abstraction
- Abstract base class ensures consistent interface across all providers
- Registry pattern allows easy addition of new providers
- Each provider implements: chat, stream, health_check, list_models

### API Key Security
- API keys encrypted using Fernet symmetric encryption
- Keys stored encrypted in database
- Decrypted only when needed for provider communication

### Health Monitoring
- Each provider has health status (ACTIVE, INACTIVE, ERROR, CHECKING)
- Health check can be triggered manually via API
- Last checked timestamp tracked

### Model Discovery
- Automatic model discovery from provider APIs
- Models stored in database with provider relationship
- Supports context length and pricing information

### Frontend Management
- Grid layout for provider cards
- Status indicators with color coding
- Add/edit provider modal form
- Test connection button
- Model discovery functionality
- Responsive design

## API Endpoints

### Provider Endpoints
- `GET /api/v1/providers` - List all providers
- `POST /api/v1/providers` - Create provider
- `GET /api/v1/providers/{id}` - Get provider
- `PUT /api/v1/providers/{id}` - Update provider
- `DELETE /api/v1/providers/{id}` - Delete provider
- `POST /api/v1/providers/{id}/test` - Test connection
- `POST /api/v1/providers/{id}/models` - Discover models
- `GET /api/v1/providers/{id}/models` - List models
- `DELETE /api/v1/providers/{id}/models/{model_id}` - Delete model

## Testing

### Backend Tests
- Provider registry tests
- Provider service tests
- Provider API endpoint tests
- API key encryption/decryption tests

### Frontend Tests
- Provider component tests
- Provider form validation tests
- API client tests

## Security Considerations

- API keys encrypted at rest using Fernet
- CORS configured for specific origins
- Input validation via Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM

## Performance Considerations

- Provider health checks are async
- Model discovery caches results in database
- Frontend uses React Query for efficient data fetching
- Lazy loading for provider components

## Future Enhancements

- Provider fallback logic (automatic failover)
- Load balancing across providers
- Rate limiting per provider
- Usage tracking and analytics
- Provider cost estimation
- Batch model operations
- Provider configuration templates
