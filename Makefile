.PHONY: dev dev-bare test lint typecheck check migrate migrate-new db-reset clean help

BACKEND_DIR = backend
FRONTEND_DIR = frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Development ──────────────────────────────────────────────────────────────

dev: ## Start all services via Docker Compose
	docker compose up --build

dev-bare: ## Start backend + frontend without Docker (local dev)
	@echo "Starting backend..."
	cd $(BACKEND_DIR) && uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
	@echo "Starting frontend..."
	cd $(FRONTEND_DIR) && npm run dev &
	@wait

stop: ## Stop Docker Compose services
	docker compose down

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run all pending database migrations
	cd $(BACKEND_DIR) && python -m alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new NAME="add_users")
	cd $(BACKEND_DIR) && python -m alembic revision --autogenerate -m "$(NAME)"

db-reset: ## Drop and recreate database, run all migrations
	cd $(BACKEND_DIR) && rm -f data/delegates.db && python -m alembic upgrade head

# ─── Quality ──────────────────────────────────────────────────────────────────

test: ## Run backend tests
	cd $(BACKEND_DIR) && python -m pytest -x -v

test-cov: ## Run backend tests with coverage
	cd $(BACKEND_DIR) && python -m pytest -x -v --cov=. --cov-report=term-missing

lint: ## Lint backend + frontend
	cd $(BACKEND_DIR) && python -m ruff check .
	cd $(FRONTEND_DIR) && npx next lint

lint-fix: ## Auto-fix lint issues
	cd $(BACKEND_DIR) && python -m ruff check --fix .

typecheck: ## TypeScript type check
	cd $(FRONTEND_DIR) && npx tsc --noEmit

check: lint typecheck test ## Run all checks (lint + typecheck + tests)

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/.next
	rm -rf $(FRONTEND_DIR)/node_modules/.cache
