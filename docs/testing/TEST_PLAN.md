# NEXUS V3 - Test Plan

## Phase 1: Project Foundation

### Backend Tests

#### Unit Tests
- [x] Configuration loading
- [x] Database connection
- [x] Health check endpoint
- [ ] Model creation (future)
- [ ] Service layer (future)
- [ ] Repository layer (future)

#### Integration Tests
- [x] Health endpoint integration
- [ ] API endpoints (future)
- [ ] Database migrations (future)

### Frontend Tests

#### Component Tests
- [x] Test setup configured
- [ ] Layout components (future)
- [ ] Page components (future)
- [ ] API client (future)

#### Integration Tests
- [ ] API integration (future)
- [ ] Routing (future)

### Manual Testing Checklist

- [x] Backend starts without errors
- [x] Frontend starts without errors
- [x] Health endpoint returns 200 OK
- [x] Database migrations run successfully
- [x] API connectivity works
- [x] Frontend builds without errors
- [x] No linting errors
- [x] No TypeScript errors

## Test Execution

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm test
```

## Coverage Targets

- Backend: 80%+
- Frontend: 70%+

## Phase 2: AI Provider Runtime

### Backend Tests

#### Unit Tests
- [ ] Provider registry registration and retrieval
- [ ] Provider interface implementation (all 5 providers)
- [ ] API key encryption/decryption
- [ ] Provider service CRUD operations
- [ ] Provider repository queries
- [ ] Health check logic
- [ ] Model discovery logic

#### Integration Tests
- [ ] Provider API endpoints (all 9 endpoints)
- [ ] Provider creation with encrypted API key
- [ ] Provider update and deletion
- [ ] Health check endpoint
- [ ] Model discovery endpoint
- [ ] Database relationships (Provider-Model)

### Frontend Tests

#### Component Tests
- [ ] ProviderCard component rendering
- [ ] ProviderList component rendering
- [ ] ProviderForm validation
- [ ] ProviderStatus indicator
- [ ] ProvidersPage integration

#### Integration Tests
- [ ] Provider API client
- [ ] React Query mutations
- [ ] Form submission flow
- [ ] Error handling

### Manual Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Provider API endpoints respond correctly
- [ ] Provider CRUD operations work
- [ ] API key encryption works
- [ ] Health check functionality works
- [ ] Model discovery works
- [ ] Frontend provider page loads
- [ ] Provider form validation works
- [ ] Test connection button works
- [ ] No console errors

## Test Execution

```bash
# Backend
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend
cd frontend
npm test
```

## Coverage Targets

- Backend: 80%+
- Frontend: 70%+
