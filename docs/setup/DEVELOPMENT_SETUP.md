# NEXUS V3 - Development Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn
- Git

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd NEXUS-V3
```

### 2. Install Dependencies

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head

# Frontend
cd ../frontend
npm install
cp .env.example .env
```

### 3. Start Development Servers

```bash
# From the project root
node scripts/dev.js
```

This starts both backend (http://localhost:8000) and frontend (http://localhost:5173) with a single command.

Press Ctrl+C to stop both services.

### 4. Using Make (Alternative)

```bash
# Install all dependencies
make install

# Setup environment files
make setup

# Start both services
make dev
```

## Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Development Commands

```bash
# Backend
make run-backend      # Start backend
make test-backend     # Run tests
make lint-backend     # Lint code
make format-backend   # Format code
make migrate          # Run migrations

# Frontend
make run-frontend     # Start dev server
make test-frontend    # Run tests
make lint-frontend    # Lint code
make format-frontend  # Format code
make type-check       # Type check

# All
make test             # Run all tests
make lint             # Lint all
make format           # Format all
```

## Project Structure

```
backend/
├── api/          # API routes
├── models/       # Database models
├── schemas/      # Pydantic schemas
├── services/     # Business logic
├── repositories/ # Data access
├── utils/        # Utilities
└── tests/        # Tests

frontend/
└── src/
    ├── api/      # API client
    ├── types/    # TypeScript types
    ├── components/ # React components
    ├── pages/    # Page components
    └── assets/   # Styles and images
```

## Troubleshooting

### Backend won't start
- Check Python version (3.11+)
- Verify virtual environment is activated
- Ensure dependencies are installed
- Check port 8000 is available

### Frontend won't start
- Check Node.js version (18+)
- Delete node_modules and reinstall
- Check port 5173 is available
- Verify VITE_API_URL in .env

### Database errors
- Ensure data directory exists
- Check DATABASE_URL in .env
- Run migrations: `alembic upgrade head`

### CORS errors
- Verify CORS_ORIGINS in backend .env
- Check frontend is running on allowed origin
- Review backend CORS middleware config

## IDE Setup

### VS Code
- Install Python extension
- Install ESLint extension
- Install Prettier extension
- Install Tailwind CSS IntelliSense

### Recommended Settings
- Format on save: Enabled
- Lint on save: Enabled
- Use workspace settings

## Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Run linters
5. Commit with clear message
6. Push and create PR
