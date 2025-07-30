# AI Virtual Agent Kickstart – root-level Makefile
# Run `make help` to see available targets.

.PHONY: help dev backend frontend llamastack stop install install-backend install-frontend \
        build build-frontend lint lint-backend lint-frontend test test-unit test-int compose-up compose-down image-build

# -----------------------------------------------------------------------------
# Helper
# -----------------------------------------------------------------------------
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		sed -e 's/^[^:]*:.*## //'

# -----------------------------------------------------------------------------
# Development (runs local_dev scripts)
# -----------------------------------------------------------------------------

# Start backend, frontend, and LlamaStack (detached)
dev: ## Run backend, frontend, and LlamaStack together
	./scripts/dev/run_local.sh

backend: ## Run backend dev server with hot-reload (uvicorn)
	./scripts/dev/local_backend.sh

frontend: ## Run frontend Vite dev server
	./scripts/dev/local_frontend.sh

llamastack: ## Run local LlamaStack server (for dev)
	./scripts/dev/local_llamastack.sh

stop: ## Stop all dev services started via ./scripts/dev scripts
	./scripts/dev/stop_local.sh

# -----------------------------------------------------------------------------
# Build helpers (build without installing)
# -----------------------------------------------------------------------------
build-frontend: ## Build frontend application for production
	cd frontend && npm run build

# -----------------------------------------------------------------------------
# Installation helpers
# -----------------------------------------------------------------------------
install-deps: install-backend-deps install-frontend-deps ## Install backend & frontend dependencies

install-backend-deps: ## Create Python venv and install backend requirements
	python -m venv venv && . venv/bin/activate && pip install -r backend/requirements.txt

install-frontend-deps: ## Install Node dependencies
	cd frontend && npm install

# -----------------------------------------------------------------------------
# Quality & Tests
# -----------------------------------------------------------------------------
lint-backend: ## Run backend linters (pre-commit)
	cd backend && pre-commit run --all-files --show-diff-on-failure || true

lint-frontend: ## Run frontend linters (eslint & prettier)
	cd frontend && npm run lint

lint: lint-backend lint-frontend ## Run all linters

test-unit: ## Run backend unit tests
	pytest -q

test-int: ## Run integration tests (tavern)
	./scripts/ci/run_tests.sh

test: lint test-unit test-int ## Run full test & lint suite

# -----------------------------------------------------------------------------
# Container / Compose helpers
# -----------------------------------------------------------------------------
compose-up: ## Start services with podman/docker compose
	podman compose --file compose.yaml up -d

compose-down: ## Stop compose services
	podman compose --file compose.yaml down

image-build: ## Build application container image
	podman build -t ai-virtual-assistant:dev .
