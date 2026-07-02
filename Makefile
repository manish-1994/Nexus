.PHONY: help install install-backend install-frontend run-backend run-frontend test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend type-check migrate docker-up docker-down clean setup

help:
	@echo "NEXUS V3 Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies"
	@echo "  make setup            Complete project setup"
	@echo ""
	@echo "Development:"
	@echo "  make run-backend      Start backend server (http://localhost:8000)"
	@echo "  make run-frontend     Start frontend dev server (http://localhost:5173)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Run backend tests"
	@echo "  make test-frontend    Run frontend tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run all linters"
	@echo "  make lint-backend     Run backend linter (flake8)"
	@echo "  make lint-frontend    Run frontend linter (eslint)"
	@echo "  make format           Format all code"
	@echo "  make format-backend   Format backend code (black, isort)"
	@echo "  make format-frontend  Format frontend code (prettier)"
	@echo "  make type-check       Run type checking (mypy, tsc)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          Run database migrations"
	@echo "  make migrate-create   Create new migration (use MSG='description')"
	@echo "  make migrate-rollback Rollback last migration"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start Docker services"
	@echo "  make docker-down      Stop Docker services"
	@echo "  make docker-clean     Remove Docker volumes and containers"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make help             Show this help message"

# Setup
install: install-backend install-frontend
	@echo "All dependencies installed successfully"

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv .venv
	cd backend && .venv\Scripts\activate && pip install --upgrade pip
	cd backend && .venv\Scripts\activate && pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

setup:
	@echo "Setting up NEXUS V3..."
	cp backend/.env.example backend/.env
	cp frontend/.env.example frontend/.env
	@echo "Environment files created. Please update with your configuration."

# Development
run-backend:
	@echo "Starting backend server..."
	cd backend && .venv\Scripts\activate && uvicorn app:app --reload --port 8000 --host 0.0.0.0

run-frontend:
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev

# Testing
test: test-backend test-frontend
	@echo "All tests completed"

test-backend:
	@echo "Running backend tests..."
	cd backend && .venv\Scripts\activate && pytest tests/ -v --cov=app --cov-report=html

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test -- --run

# Code Quality
lint: lint-backend lint-frontend
	@echo "All linting completed"

lint-backend:
	@echo "Running backend linter..."
	cd backend && .venv\Scripts\activate && flake8 app.py api/ services/ repositories/ models/ schemas/ utils/ --max-line-length=120 --exclude=__pycache__

lint-frontend:
	@echo "Running frontend linter..."
	cd frontend && npm run lint

format: format-backend format-frontend
	@echo "All formatting completed"

format-backend:
	@echo "Formatting backend code..."
	cd backend && .venv\Scripts\activate && black app.py api/ services/ repositories/ models/ schemas/ utils/ tests/ --line-length=120
	cd backend && .venv\Scripts\activate && isort app.py api/ services/ repositories/ models/ schemas/ utils/ tests/

format-frontend:
	@echo "Formatting frontend code..."
	cd frontend && npm run format

type-check: type-check-backend type-check-frontend
	@echo "All type checking completed"

type-check-backend:
	@echo "Running backend type checker..."
	cd backend && .venv\Scripts\activate && mypy app.py api/ services/ repositories/ models/ schemas/ utils/ --ignore-missing-imports

type-check-frontend:
	@echo "Running frontend type checker..."
	cd frontend && npm run type-check

# Database
migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-rollback:
	@echo "Rolling back last migration..."
	cd backend && alembic downgrade -1

# Docker
docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "Services started. Backend: http://localhost:8000, Frontend: http://localhost:5173"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

# Utilities
clean:
	@echo "Cleaning project..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "Clean completed"
