# Energy Tracking IoT Platform - Makefile
# ==============================================================================

# Variables
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yml
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
DOCKER_COMPOSE_DEFAULT = docker-compose

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help setup dev prod down clean logs test lint format backup restore

# ==============================================================================
# HELP
# ==============================================================================

help: ## Show this help message
	@echo "$(BLUE)Energy Tracking IoT Platform$(NC)"
	@echo "=============================="
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# ==============================================================================
# SETUP & INITIALIZATION
# ==============================================================================

setup: ## Initial project setup
	@echo "$(BLUE)Setting up Energy Tracking IoT Platform...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(RED)Please edit .env file with your configuration before proceeding!$(NC)"; \
	else \
		echo "$(GREEN).env file already exists$(NC)"; \
	fi
	@mkdir -p data/{postgres,influxdb,redis,grafana,mosquitto}
	@mkdir -p logs/{api-gateway,data-ingestion,data-processing,analytics,notification}
	@mkdir -p infrastructure/{grafana/dashboards,mosquitto/config,nginx/conf.d}
	@echo "$(GREEN)Project structure created successfully!$(NC)"

init-dev: setup ## Initialize development environment
	@echo "$(BLUE)Initializing development environment...$(NC)"
	@$(DOCKER_COMPOSE_DEV) pull
	@$(DOCKER_COMPOSE_DEV) build --no-cache
	@echo "$(GREEN)Development environment ready!$(NC)"

init-prod: setup ## Initialize production environment
	@echo "$(BLUE)Initializing production environment...$(NC)"
	@$(DOCKER_COMPOSE_PROD) pull
	@$(DOCKER_COMPOSE_PROD) build --no-cache
	@echo "$(GREEN)Production environment ready!$(NC)"

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "$(YELLOW)Services available at:$(NC)"
	@echo "  - Dashboard: http://localhost:3000"
	@echo "  - API Gateway: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Grafana: http://localhost:3001 (admin/admin123)"
	@echo "  - InfluxDB: http://localhost:8086"
	@echo "  - PgAdmin: http://localhost:5050"
	@echo "  - Redis Commander: http://localhost:8081"

dev-build: ## Build and start development environment
	@echo "$(BLUE)Building and starting development environment...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up -d --build
	@echo "$(GREEN)Development environment built and started!$(NC)"

dev-logs: ## Show development logs
	@$(DOCKER_COMPOSE_DEV) logs -f

dev-shell: ## Access development shell for a service (usage: make dev-shell SERVICE=api-gateway)
	@$(DOCKER_COMPOSE_DEV) exec $(SERVICE) /bin/bash

dev-restart: ## Restart development environment
	@echo "$(BLUE)Restarting development environment...$(NC)"
	@$(DOCKER_COMPOSE_DEV) restart
	@echo "$(GREEN)Development environment restarted!$(NC)"

# ==============================================================================
# PRODUCTION
# ==============================================================================

prod: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup' first!$(NC)"; \
		exit 1; \
	fi
	@$(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)Production environment started!$(NC)"

prod-build: ## Build and start production environment
	@echo "$(BLUE)Building and starting production environment...$(NC)"
	@$(DOCKER_COMPOSE_PROD) up -d --build
	@echo "$(GREEN)Production environment built and started!$(NC)"

prod-logs: ## Show production logs
	@$(DOCKER_COMPOSE_PROD) logs -f

prod-shell: ## Access production shell for a service (usage: make prod-shell SERVICE=api-gateway)
	@$(DOCKER_COMPOSE_PROD) exec $(SERVICE) /bin/bash

prod-restart: ## Restart production environment
	@echo "$(BLUE)Restarting production environment...$(NC)"
	@$(DOCKER_COMPOSE_PROD) restart
	@echo "$(GREEN)Production environment restarted!$(NC)"

# ==============================================================================
# MANAGEMENT
# ==============================================================================

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE_DEV) down 2>/dev/null || true
	@$(DOCKER_COMPOSE_PROD) down 2>/dev/null || true
	@$(DOCKER_COMPOSE_DEFAULT) down 2>/dev/null || true
	@echo "$(GREEN)All services stopped!$(NC)"

clean: down ## Stop services and remove volumes
	@echo "$(YELLOW)Cleaning up containers, networks, and volumes...$(NC)"
	@$(DOCKER_COMPOSE_DEV) down -v --remove-orphans 2>/dev/null || true
	@$(DOCKER_COMPOSE_PROD) down -v --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-all: clean ## Complete cleanup including images
	@echo "$(YELLOW)Removing all project images...$(NC)"
	@docker images | grep energy- | awk '{print $$3}' | xargs -r docker rmi -f
	@echo "$(GREEN)Complete cleanup finished!$(NC)"

status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@echo "$(YELLOW)Development:$(NC)"
	@$(DOCKER_COMPOSE_DEV) ps 2>/dev/null || echo "  Development environment not running"
	@echo "$(YELLOW)Production:$(NC)"
	@$(DOCKER_COMPOSE_PROD) ps 2>/dev/null || echo "  Production environment not running"

# ==============================================================================
# LOGS & MONITORING
# ==============================================================================

logs: ## Show logs for all services (usage: make logs ENV=dev|prod)
	@if [ "$(ENV)" = "prod" ]; then \
		$(DOCKER_COMPOSE_PROD) logs -f; \
	else \
		$(DOCKER_COMPOSE_DEV) logs -f; \
	fi

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=api-gateway ENV=dev|prod)
	@if [ "$(ENV)" = "prod" ]; then \
		$(DOCKER_COMPOSE_PROD) logs -f $(SERVICE); \
	else \
		$(DOCKER_COMPOSE_DEV) logs -f $(SERVICE); \
	fi

# ==============================================================================
# DATABASE OPERATIONS
# ==============================================================================

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m alembic upgrade head
	@echo "$(GREEN)Database migrations completed!$(NC)"

db-reset: ## Reset database (DANGER: This will delete all data)
	@echo "$(RED)WARNING: This will delete ALL database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(YELLOW)Resetting database...$(NC)"; \
		$(DOCKER_COMPOSE_DEV) exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS energy_tracking_dev;"; \
		$(DOCKER_COMPOSE_DEV) exec postgres psql -U postgres -c "CREATE DATABASE energy_tracking_dev;"; \
		make db-migrate; \
		echo "$(GREEN)Database reset completed!$(NC)"; \
	fi

db-backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backup
	@$(DOCKER_COMPOSE_DEV) exec postgres pg_dump -U postgres energy_tracking_dev > backup/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created in backup/ directory$(NC)"

db-restore: ## Restore database from backup (usage: make db-restore BACKUP=backup/db_backup_20240101_120000.sql)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)Usage: make db-restore BACKUP=path/to/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring database from $(BACKUP)...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec -T postgres psql -U postgres energy_tracking_dev < $(BACKUP)
	@echo "$(GREEN)Database restored successfully!$(NC)"

# ==============================================================================
# TESTING
# ==============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m pytest tests/ -v
	@$(DOCKER_COMPOSE_DEV) exec data-ingestion python -m pytest tests/ -v
	@$(DOCKER_COMPOSE_DEV) exec data-processing python -m pytest tests/ -v
	@$(DOCKER_COMPOSE_DEV) exec analytics python -m pytest tests/ -v
	@echo "$(GREEN)All tests completed!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@python -m pytest tests/unit/ -v -m unit
	@echo "$(GREEN)Unit tests completed!$(NC)"

test-integration: ## Run integration tests (requires services running)
	@echo "$(BLUE)Running integration tests...$(NC)"
	@python -m pytest tests/integration/ -v -m integration
	@echo "$(GREEN)Integration tests completed!$(NC)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running end-to-end tests...$(NC)"
	@python -m pytest tests/integration/ -v -m e2e
	@echo "$(GREEN)End-to-end tests completed!$(NC)"

test-service: ## Run tests for specific service (usage: make test-service SERVICE=api-gateway)
	@echo "$(BLUE)Running tests for $(SERVICE)...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec $(SERVICE) python -m pytest tests/ -v
	@echo "$(GREEN)Tests for $(SERVICE) completed!$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@python -m pytest tests/ --cov=services --cov-report=html --cov-report=term --cov-fail-under=80
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd frontend && npm test -- --run
	@echo "$(GREEN)Frontend tests completed!$(NC)"

test-frontend-coverage: ## Run frontend tests with coverage
	@echo "$(BLUE)Running frontend tests with coverage...$(NC)"
	@cd frontend && npm run test:coverage
	@echo "$(GREEN)Frontend coverage report generated!$(NC)"

test-performance: ## Run performance tests with Locust
	@echo "$(BLUE)Running performance tests...$(NC)"
	@pip install locust
	@locust -f tests/performance/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
	@echo "$(GREEN)Performance tests completed!$(NC)"

test-security: ## Run security tests
	@echo "$(BLUE)Running security tests...$(NC)"
	@pip install bandit safety
	@bandit -r services/
	@safety check
	@python -m pytest tests/security/ -v
	@echo "$(GREEN)Security tests completed!$(NC)"

test-install-deps: ## Install test dependencies
	@echo "$(BLUE)Installing test dependencies...$(NC)"
	@pip install -r test-requirements.txt
	@echo "$(GREEN)Test dependencies installed!$(NC)"

test-all: test-install-deps test-unit test-integration test-frontend ## Run all test suites
	@echo "$(GREEN)All test suites completed successfully!$(NC)"

# Performance testing
test-performance: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	@python tests/performance/run_performance_tests.py --scenario smoke --start-services --cleanup
	@echo "$(GREEN)Performance tests completed!$(NC)"

test-performance-all: ## Run all performance test scenarios
	@echo "$(BLUE)Running all performance test scenarios...$(NC)"
	@python tests/performance/run_performance_tests.py --scenario all --start-services --cleanup
	@echo "$(GREEN)All performance tests completed!$(NC)"

test-performance-stress: ## Run stress performance tests
	@echo "$(BLUE)Running stress performance tests...$(NC)"
	@python tests/performance/run_performance_tests.py --scenario stress --start-services --cleanup
	@echo "$(GREEN)Stress performance tests completed!$(NC)"

test-performance-endurance: ## Run endurance performance tests
	@echo "$(BLUE)Running endurance performance tests...$(NC)"
	@python tests/performance/run_performance_tests.py --scenario endurance --start-services --cleanup
	@echo "$(GREEN)Endurance performance tests completed!$(NC)"

# Health checks for testing
test-health: ## Check if all services are healthy for testing
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)API Gateway unhealthy$(NC)"
	@curl -f http://localhost:8005/health || echo "$(RED)Auth Service unhealthy$(NC)"
	@curl -f http://localhost:8001/health || echo "$(RED)Data Ingestion unhealthy$(NC)"
	@curl -f http://localhost:8002/health || echo "$(RED)Data Processing unhealthy$(NC)"
	@curl -f http://localhost:8003/health || echo "$(RED)Analytics unhealthy$(NC)"
	@curl -f http://localhost:8004/health || echo "$(RED)Notification unhealthy$(NC)"
	@echo "$(GREEN)Health check completed!$(NC)"

health-detailed: ## Get detailed health status from all services
	@echo "$(BLUE)Getting detailed health status...$(NC)"
	@echo "$(YELLOW)Auth Service:$(NC)"
	@curl -s http://localhost:8005/health | python -m json.tool || echo "Service not available"
	@echo "\n$(YELLOW)API Gateway:$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Service not available"
	@echo "\n$(YELLOW)Data Ingestion:$(NC)"
	@curl -s http://localhost:8001/health | python -m json.tool || echo "Service not available"
	@echo "\n$(YELLOW)Data Processing:$(NC)"
	@curl -s http://localhost:8002/health | python -m json.tool || echo "Service not available"
	@echo "\n$(YELLOW)Analytics:$(NC)"
	@curl -s http://localhost:8003/health | python -m json.tool || echo "Service not available"
	@echo "\n$(YELLOW)Notification:$(NC)"
	@curl -s http://localhost:8004/health | python -m json.tool || echo "Service not available"
	@echo "$(GREEN)Detailed health check completed!$(NC)"

# ==============================================================================
# API DOCUMENTATION
# ==============================================================================

docs-generate: ## Generate API documentation from all services
	@echo "$(BLUE)Generating API documentation...$(NC)"
	@python scripts/generate_api_docs.py
	@echo "$(GREEN)API documentation generated!$(NC)"

docs-serve: ## Serve aggregated API documentation
	@echo "$(BLUE)Starting documentation server...$(NC)"
	@cd docs/api && python -m http.server 8080 &
	@echo "$(GREEN)Documentation server started at http://localhost:8080$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8080; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8080; \
	fi

docs-export-postman: ## Export API documentation as Postman collection
	@echo "$(BLUE)Exporting Postman collection...$(NC)"
	@python scripts/generate_api_docs.py
	@echo "$(GREEN)Postman collection exported to docs/api/postman_collection.json$(NC)"

docs-validate: ## Validate all OpenAPI specifications
	@echo "$(BLUE)Validating OpenAPI specifications...$(NC)"
	@pip install openapi-spec-validator
	@cd docs/api && for file in *.json; do \
		echo "Validating $$file..."; \
		openapi-spec-validator "$$file" || echo "$(RED)Validation failed for $$file$(NC)"; \
	done
	@echo "$(GREEN)OpenAPI validation completed!$(NC)"

# ==============================================================================
# CODE QUALITY
# ==============================================================================

lint: ## Run linting on all services
	@echo "$(BLUE)Running linting...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m flake8 app/
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m black --check app/
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m isort --check-only app/
	@echo "$(GREEN)Linting completed!$(NC)"

format: ## Format code in all services
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m black app/
	@$(DOCKER_COMPOSE_DEV) exec api-gateway python -m isort app/
	@$(DOCKER_COMPOSE_DEV) exec data-ingestion python -m black app/
	@$(DOCKER_COMPOSE_DEV) exec data-ingestion python -m isort app/
	@$(DOCKER_COMPOSE_DEV) exec data-processing python -m black app/
	@$(DOCKER_COMPOSE_DEV) exec data-processing python -m isort app/
	@$(DOCKER_COMPOSE_DEV) exec analytics python -m black app/
	@$(DOCKER_COMPOSE_DEV) exec analytics python -m isort app/
	@echo "$(GREEN)Code formatting completed!$(NC)"

# ==============================================================================
# DATA OPERATIONS
# ==============================================================================

generate-data: ## Generate sample IoT data for testing
	@echo "$(BLUE)Generating sample data...$(NC)"
	@$(DOCKER_COMPOSE_DEV) --profile tools up data-generator
	@echo "$(GREEN)Sample data generation started!$(NC)"

stop-data-generation: ## Stop data generation
	@echo "$(YELLOW)Stopping data generation...$(NC)"
	@$(DOCKER_COMPOSE_DEV) stop data-generator
	@echo "$(GREEN)Data generation stopped!$(NC)"

# ==============================================================================
# MONITORING
# ==============================================================================

monitor: ## Open monitoring dashboards
	@echo "$(BLUE)Opening monitoring dashboards...$(NC)"
	@echo "$(YELLOW)Grafana: http://localhost:3001$(NC)"
	@echo "$(YELLOW)InfluxDB: http://localhost:8086$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:3001; \
		open http://localhost:8086; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3001; \
		xdg-open http://localhost:8086; \
	else \
		echo "$(RED)Please open the URLs manually$(NC)"; \
	fi

# ==============================================================================
# DEPLOYMENT
# ==============================================================================

deploy: ## Deploy to production (requires proper configuration)
	@echo "$(BLUE)Deploying to production...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Building production images...$(NC)"
	@$(DOCKER_COMPOSE_PROD) build
	@echo "$(YELLOW)Starting production services...$(NC)"
	@$(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)Production deployment completed!$(NC)"

# ==============================================================================
# CI/CD SIMULATION
# ==============================================================================

ci-simulate: ## Simulate complete CI/CD pipeline locally
	@echo "$(BLUE)Simulating CI/CD pipeline...$(NC)"
	@powershell -ExecutionPolicy Bypass -File simulate-ci.ps1 -Stage all -CleanUp
	@echo "$(GREEN)CI simulation completed!$(NC)"

ci-quick: ## Quick CI check (lint + unit tests + security)
	@echo "$(BLUE)Running quick CI checks...$(NC)"
	@python quick-ci.py --stages all
	@echo "$(GREEN)Quick CI completed!$(NC)"

ci-lint: ## Simulate lint stage only
	@echo "$(BLUE)Simulating lint stage...$(NC)"
	@python quick-ci.py --stages lint
	@echo "$(GREEN)Lint simulation completed!$(NC)"

ci-unit: ## Simulate unit test stage only
	@echo "$(BLUE)Simulating unit test stage...$(NC)"
	@python quick-ci.py --stages unit
	@echo "$(GREEN)Unit test simulation completed!$(NC)"

ci-security: ## Simulate security test stage only
	@echo "$(BLUE)Simulating security stage...$(NC)"
	@python quick-ci.py --stages security
	@echo "$(GREEN)Security simulation completed!$(NC)"

ci-integration: ## Simulate integration tests with services
	@echo "$(BLUE)Simulating integration tests...$(NC)"
	@powershell -ExecutionPolicy Bypass -File simulate-ci.ps1 -Stage integration
	@echo "$(GREEN)Integration test simulation completed!$(NC)"

ci-e2e: ## Simulate end-to-end tests
	@echo "$(BLUE)Simulating E2E tests...$(NC)"
	@powershell -ExecutionPolicy Bypass -File simulate-ci.ps1 -Stage e2e
	@echo "$(GREEN)E2E simulation completed!$(NC)"

ci-docker: ## Simulate Docker build stage
	@echo "$(BLUE)Simulating Docker builds...$(NC)"
	@powershell -ExecutionPolicy Bypass -File simulate-ci.ps1 -Stage docker
	@echo "$(GREEN)Docker build simulation completed!$(NC)"

ci-performance: ## Simulate performance tests
	@echo "$(BLUE)Simulating performance tests...$(NC)"
	@powershell -ExecutionPolicy Bypass -File simulate-ci.ps1 -Stage performance
	@echo "$(GREEN)Performance test simulation completed!$(NC)"

ci-pre-commit: ## Pre-commit CI check (quick validation before committing)
	@echo "$(BLUE)Running pre-commit CI checks...$(NC)"
	@python quick-ci.py --stages lint,unit --continue-on-failure
	@echo "$(GREEN)Pre-commit checks completed!$(NC)"

ci-validate: ## Validate CI pipeline configuration
	@echo "$(BLUE)Validating CI pipeline configuration...$(NC)"
	@python .github/scripts/validate_pipeline.py
	@echo "$(GREEN)CI validation completed!$(NC)"

# ==============================================================================
# UTILITY COMMANDS
# ==============================================================================

update: ## Update all services to latest versions
	@echo "$(BLUE)Updating services...$(NC)"
	@$(DOCKER_COMPOSE_DEV) pull
	@$(DOCKER_COMPOSE_PROD) pull
	@echo "$(GREEN)Services updated!$(NC)"

config: ## Show current configuration
	@echo "$(BLUE)Current Configuration:$(NC)"
	@echo "$(YELLOW)Development:$(NC)"
	@$(DOCKER_COMPOSE_DEV) config
	@echo "$(YELLOW)Production:$(NC)"
	@$(DOCKER_COMPOSE_PROD) config

# Default target
.DEFAULT_GOAL := help
