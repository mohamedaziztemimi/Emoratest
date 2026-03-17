.PHONY: help install install-backend install-ml install-frontend lint lint-backend lint-ml lint-frontend format format-backend format-ml test test-backend test-ml dev-backend dev-frontend migrate migration

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Install ──────────────────────────────────────────────

install: install-backend install-ml install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	cd backend && pip install -e ".[dev]"

install-ml: ## Install ML dependencies
	cd ml && pip install -e ".[dev]"

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# ── Lint ─────────────────────────────────────────────────

lint: lint-backend lint-ml lint-frontend ## Lint all projects

lint-backend: ## Lint backend with ruff
	cd backend && ruff check .

lint-ml: ## Lint ML with ruff
	cd ml && ruff check .

lint-frontend: ## Lint frontend with ESLint
	cd frontend && npm run lint

# ── Format ───────────────────────────────────────────────

format: format-backend format-ml ## Format all Python code

format-backend: ## Format backend with ruff
	cd backend && ruff format . && ruff check --fix .

format-ml: ## Format ML with ruff
	cd ml && ruff format . && ruff check --fix .

# ── Test ─────────────────────────────────────────────────

test: test-backend test-ml ## Run all tests

test-backend: ## Run backend tests
	cd backend && pytest -v

test-ml: ## Run ML tests
	cd ml && pytest -v

# ── Database ─────────────────────────────────────────────

migrate: ## Run Alembic migrations to latest
	cd backend && alembic upgrade head

migration: ## Create new Alembic migration (usage: make migration msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

# ── Dev servers ──────────────────────────────────────────

dev-backend: ## Start backend dev server
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev
