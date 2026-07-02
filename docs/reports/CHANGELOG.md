# NEXUS V3 - Changelog

## [0.6.0] - 2026-07-02 - Phase 3: AI Runtime Gateway (LOCKED)

### Added
- AI Runtime Gateway as unified entry point for all AI communication
- OpenAI-compatible provider supporting all OpenAI-compatible APIs
- Capability detection and caching system
- Usage tracking and cost estimation
- Model metadata cache with TTL
- CapabilityBadge component for frontend
- Badge component for reusable UI elements
- AI Runtime API endpoints
- Capability and Usage database models

### Changed
- Chat Service now routes through AI Runtime Gateway
- Provider registry includes OpenAICompatibleProvider
- ProviderType enum includes OPENAI_COMPATIBLE
- Provider model extended with new fields (default_model, timeout, priority, custom_headers, max_retries, organization_id, capabilities)
- Frontend provider management enhanced with capability display

### Fixed
- N/A

### Security
- N/A

## [0.5.0] - 2026-07-02 - Phase 2: Chat Module (LOCKED)

### Added
- End-to-end chat send pipeline with SSE streaming
- Absolute backend URL in chat API client for reliable streaming
- Final acceptance test verification for Chat Workspace

### Changed
- Chat Module status: Complete → Locked
- Project status updated to reflect locked Chat Workspace

### Fixed
- Critical: chat send pipeline used relative URL `/api/v1/chat` which resolved to Vite dev server instead of FastAPI backend, causing "Sending..." state to hang indefinitely
- Fixed by using absolute backend URL `http://localhost:8000/api/v1/chat` in `frontend/src/api/chat.ts`

### Security
- N/A

## [0.4.0] - 2026-07-01 - Phase 1.5: Application Shell

### Added
- Permanent application shell with TopBar, Sidebar, and StatusBar
- Responsive navigation with grouped sections (Core, Intelligence, Workspace, Tools, System)
- Dashboard page with system status overview and quick access links
- Placeholder pages for Memory, Planner, Workflows, Workspace, and Tools
- Breadcrumb navigation in TopBar
- Global search input (placeholder)
- Theme toggle button
- Notifications indicator
- User menu button
- Backend and database status indicators in StatusBar
- Mobile hamburger menu with overlay sidebar
- Collapsible sidebar for tablet devices
- ARIA labels and keyboard navigation support

### Changed
- Updated Layout component to integrate new shell structure
- Enhanced Sidebar with icons and grouped navigation sections
- Updated routing to include all new pages
- Replaced HomePage with DashboardPage as default route

### Fixed
- N/A

### Security
- N/A

## [0.3.0] - 2026-07-01 - Phase 2: Chat Module

### Added
- Conversation management API (CRUD operations)
- Message sending and streaming API
- Server-Sent Events (SSE) streaming support
- Chat service layer with provider integration
- Conversation and message repositories
- Chat Pydantic schemas
- Frontend chat API client
- Chat page with conversation sidebar
- Message list with streaming display
- Message input with provider/model selection
- Conversation rename and delete functionality
- Real-time message streaming in UI
- Auto-scroll during streaming
- Message persistence in SQLite

### Changed
- Updated API router to include chat endpoints
- Updated frontend navigation to include Chat page
- Updated CORS configuration to support port 5174

### Fixed
- Chat schema timestamp type mismatch (str -> datetime)
- TypeScript build errors in ProviderStatus, ChatPage, ProvidersPage

### Security
- Input validation via Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM

## [0.2.1] - 2026-07-01 - Bug Fix: CORS Origin Mismatch

### Fixed
- Frontend-backend communication failure caused by CORS origin mismatch
- Updated backend CORS configuration to include port 5174
- Frontend on port 5174 can now communicate with backend on port 8000

## [0.2.0] - 2026-07-01 - Phase 2: AI Provider Runtime

### Added
- Provider abstraction layer with BaseProvider abstract class
- Provider registry for managing provider implementations
- 5 AI provider implementations:
  - OpenRouter provider
  - Groq provider
  - Ollama provider (local HTTP API)
  - Gemini provider
  - LM Studio provider (local HTTP API)
- Provider service layer with CRUD operations
- Provider repository for data access
- Provider API endpoints (9 endpoints)
- API key encryption using Fernet
- Health monitoring system for providers
- Model discovery functionality
- Database relationships between Provider and Model
- Frontend provider management page
- Provider card, list, form, and status components
- React Query integration for provider data

### Changed
- Updated database models with Provider-Model relationships
- Updated API router to include provider endpoints
- Updated frontend navigation to include Providers page

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- API keys encrypted at rest using Fernet symmetric encryption
- CORS configuration maintained from Phase 1

## [0.1.0] - 2026-07-01 - Phase 1: Project Foundation

### Added
- Initial project structure
- Backend FastAPI application with health endpoint
- Frontend React + Vite + TypeScript application
- SQLite database configuration with SQLAlchemy
- Alembic migration setup
- Base models, schemas, services, repositories
- API client and health check integration
- Testing framework (pytest, vitest)
- Docker Compose configuration
- Makefile with development commands
- Comprehensive documentation

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- API key encryption utilities added
- CORS configuration implemented
