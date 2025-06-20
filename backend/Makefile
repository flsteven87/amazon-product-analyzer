install:
	pip install uv
	uv sync

set-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make set-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ] && [ "$(ENV)" != "test" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production, test"; \
		exit 1; \
	fi
	@echo "Setting environment to $(ENV)"
	@bash -c "source scripts/set_env.sh $(ENV)"

prod:
	@echo "Starting server in production environment"
	@bash -c "source scripts/set_env.sh production && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

staging:
	@echo "Starting server in staging environment"
	@bash -c "source scripts/set_env.sh staging && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

dev:
	@echo "Starting server in development environment"
	@bash -c "source scripts/set_env.sh development && uv run uvicorn app.main:app --reload --port 8000"

# Core system commands
test-core:
	@echo "Testing core multi-agent system"
	@bash -c "source scripts/set_env.sh development && uv run python -c \"from app.core.graph.workflow import create_analysis_workflow; print('✅ Core system imports OK')\""

health:
	@echo "Checking API health"
	@curl -s http://localhost:8000/health | uv run python -m json.tool || echo "❌ API not responding"

# Streamlit commands
streamlit:
	@echo "Starting Streamlit testing interface"
	@bash -c "source scripts/set_env.sh development && uv run streamlit run streamlit_app.py --server.port 8501"

streamlit-dev:
	@echo "Starting Streamlit in development mode"
	@bash -c "source scripts/set_env.sh development && uv run streamlit run streamlit_app.py --server.port 8501 --server.runOnSave true"

# Full stack commands
full-stack:
	@echo "Starting full stack (API + Streamlit)"
	@echo "Starting API in background..."
	@bash -c "source scripts/set_env.sh development && uv run uvicorn app.main:app --reload --port 8000" &
	@sleep 3
	@echo "Starting Streamlit..."
	@bash -c "source scripts/set_env.sh development && uv run streamlit run streamlit_app.py --server.port 8501"

# Database commands
db-stats:
	@bash -c "source scripts/set_env.sh development && uv run python -m app.cli db-stats"

db-truncate:
	@bash -c "source scripts/set_env.sh development && uv run python -m app.cli db-truncate"

db-delete-asin:
	@if [ -z "$(ASIN)" ]; then \
		echo "ASIN is not set. Usage: make db-delete-asin ASIN=B0BZXLMM3H"; \
		exit 1; \
	fi
	@bash -c "source scripts/set_env.sh development && uv run python -m app.cli db-delete --asin $(ASIN)"

db-delete-task:
	@if [ -z "$(TASK_ID)" ]; then \
		echo "TASK_ID is not set. Usage: make db-delete-task TASK_ID=uuid-here"; \
		exit 1; \
	fi
	@bash -c "source scripts/set_env.sh development && uv run python -m app.cli db-delete --task-id $(TASK_ID)"

# Code quality commands
lint:
	@echo "Running linter with uv"
	@bash -c "source scripts/set_env.sh development && uv run ruff check ."

format:
	@echo "Formatting code with uv"
	@bash -c "source scripts/set_env.sh development && uv run ruff format ."

check:
	@echo "Running format and lint checks"
	@bash -c "source scripts/set_env.sh development && uv run ruff format . && uv run ruff check ."

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache

docker-build:
	docker build -t fastapi-langgraph-template .

docker-build-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-build-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/build-docker.sh $(ENV)

docker-run:
	docker run -p 8000:8000 fastapi-langgraph-template

docker-run-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-run-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/run-docker.sh $(ENV)

docker-logs:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-logs ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/logs-docker.sh $(ENV)

docker-stop:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-stop ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/stop-docker.sh $(ENV)

# Docker Compose commands for the entire stack
docker-compose-up:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-up ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	APP_ENV=$(ENV) docker-compose up -d

docker-compose-down:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-down ENV=development|staging|production"; \
		exit 1; \
	fi
	APP_ENV=$(ENV) docker-compose down

docker-compose-logs:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-logs ENV=development|staging|production"; \
		exit 1; \
	fi
	APP_ENV=$(ENV) docker-compose logs -f

# Help
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  install: Install dependencies"
	@echo "  set-env ENV=<environment>: Set environment variables (development, staging, production, test)"
	@echo "  run ENV=<environment>: Set environment and run server"
	@echo "  prod: Run server in production environment"
	@echo "  staging: Run server in staging environment"
	@echo "  dev: Run server in development environment"
	@echo "  test-core: Test core multi-agent system imports"
	@echo "  health: Check API health status"
	@echo "  streamlit: Start Streamlit testing interface"
	@echo "  streamlit-dev: Start Streamlit in development mode"
	@echo "  full-stack: Start both API and Streamlit"
	@echo "  db-stats: Show database statistics"
	@echo "  db-truncate: Truncate all database tables (DANGEROUS!)"
	@echo "  db-delete-asin ASIN=<asin>: Delete all data for specific ASIN"
	@echo "  db-delete-task TASK_ID=<id>: Delete all data for specific task"
	@echo "  lint: Run code linter"
	@echo "  format: Format code"
	@echo "  check: Run format and lint checks"
	@echo "  clean: Clean up"
	@echo "  docker-build: Build default Docker image"
	@echo "  docker-build-env ENV=<environment>: Build Docker image for specific environment"
	@echo "  docker-run: Run default Docker container"
	@echo "  docker-run-env ENV=<environment>: Run Docker container for specific environment"
	@echo "  docker-logs ENV=<environment>: View logs from running container"
	@echo "  docker-stop ENV=<environment>: Stop and remove container"
	@echo "  docker-compose-up: Start the entire stack (API, Prometheus, Grafana)"
	@echo "  docker-compose-down: Stop the entire stack"
	@echo "  docker-compose-logs: View logs from all services"