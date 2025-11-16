# Jaseci Learning Companion - Development Makefile
# Author: Cavin Otieno

.PHONY: help install dev build test lint format clean docker-up docker-down deploy

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE_FILE=infrastructure/docker/dev/docker-compose.yml
FRONTEND_DIR=frontend/web-dashboard
BACKEND_DIR=services
REPO_NAME=jaseci-learning-companion

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[0;33m
BLUE=\033[0;34m
MAGENTA=\033[0;35m
CYAN=\033[0;36m
NC=\033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(CYAN)Jaseci Learning Companion - Development Commands$(NC)"
	@echo "$(CYAN)=============================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Usage Examples:$(NC)"
	@echo "  make install          # Install dependencies"
	@echo "  make dev             # Start development environment"
	@echo "  make test-all        # Run all tests"
	@echo "  make docker-up       # Start with Docker Compose"
	@echo ""

# Development Environment Setup
install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@echo "$(YELLOW)Backend dependencies...$(NC)"
	cd $(BACKEND_DIR) && pip install -r requirements.txt
	@echo "$(YELLOW)Frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✅ Dependencies installed successfully$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@echo "$(YELLOW)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

# Development Commands
dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@echo "$(YELLOW)Starting database services...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d postgres redis neo4j elasticsearch nats
	@echo "$(YELLOW)Waiting for services to be ready...$(NC)"
	sleep 30
	@echo "$(YELLOW)Running database migrations...$(NC)"
	make migrate
	@echo "$(YELLOW)Starting application services...$(NC)"
	@echo "$(MAGENTA)Note: Start backend services manually in separate terminals:$(NC)"
	@echo "  - cd services/core/api_gateway && uvicorn main:app --reload"
	@echo "  - cd services/orchestrator && python -m orchestrator.main"
	@echo "  - cd $(FRONTEND_DIR) && npm run dev"
	@echo "$(GREEN)✅ Development environment ready$(NC)"

dev-full: ## Start full development environment with all services
	@echo "$(BLUE)Starting full development environment...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) up --build
	@echo "$(GREEN)✅ Full development environment ready$(NC)"

# Docker Commands
docker-up: ## Start all services with Docker Compose
	@echo "$(BLUE)Starting services with Docker Compose...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Services started$(NC)"
	@echo "$(CYAN)Access points:$(NC)"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Gateway: http://localhost:8000"
	@echo "  - Grafana: http://localhost:3001"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Jaeger: http://localhost:16686"
	@echo "  - Neo4j Browser: http://localhost:7474"

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-logs: ## Show Docker Compose logs
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

docker-clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup complete$(NC)"

# Database Commands
migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	cd $(BACKEND_DIR) && python scripts/migrate.py
	@echo "$(GREEN)✅ Migrations complete$(NC)"

migrate-rollback: ## Rollback database migrations
	@echo "$(YELLOW)Rolling back database migrations...$(NC)"
	cd $(BACKEND_DIR) && python scripts/migrate_rollback.py
	@echo "$(GREEN)✅ Migration rollback complete$(NC)"

seed-data: ## Seed database with sample data
	@echo "$(BLUE)Seeding database with sample data...$(NC)"
	cd $(BACKEND_DIR) && python scripts/seed_data.py
	@echo "$(GREEN)✅ Data seeding complete$(NC)"

# Testing Commands
test-all: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	make test-unit
	make test-integration
	make test-e2e
	@echo "$(GREEN)✅ All tests completed$(NC)"

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	@echo "$(YELLOW)Backend unit tests...$(NC)"
	cd $(BACKEND_DIR) && python -m pytest tests/unit/ -v --cov=services --cov-report=html
	@echo "$(YELLOW)Frontend unit tests...$(NC)"
	cd $(FRONTEND_DIR) && npm run test:ci
	@echo "$(GREEN)✅ Unit tests completed$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	cd $(BACKEND_DIR) && python -m pytest tests/integration/ -v
	@echo "$(GREEN)✅ Integration tests completed$(NC)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running end-to-end tests...$(NC)"
	cd $(FRONTEND_DIR) && npm run test:e2e
	@echo "$(GREEN)✅ E2E tests completed$(NC)"

test-performance: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	cd tests/performance && python load_test.py
	@echo "$(GREEN)✅ Performance tests completed$(NC)"

test-security: ## Run security tests
	@echo "$(BLUE)Running security tests...$(NC)"
	@echo "$(YELLOW)Backend security scan...$(NC)"
	cd $(BACKEND_DIR) && bandit -r services/ -f json -o security-report.json
	@echo "$(YELLOW)Dependencies vulnerability scan...$(NC)"
	cd $(BACKEND_DIR) && safety check --json --output safety-report.json
	@echo "$(GREEN)✅ Security tests completed$(NC)"

# Code Quality Commands
lint: ## Run linting on all code
	@echo "$(BLUE)Running code linting...$(NC)"
	@echo "$(YELLOW)Backend linting...$(NC)"
	cd $(BACKEND_DIR) && flake8 services/ --count --statistics
	@echo "$(YELLOW)Frontend linting...$(NC)"
	cd $(FRONTEND_DIR) && npm run lint
	@echo "$(GREEN)✅ Linting completed$(NC)"

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	@echo "$(YELLOW)Backend formatting...$(NC)"
	cd $(BACKEND_DIR) && black . && isort .
	@echo "$(YELLOW)Frontend formatting...$(NC)"
	cd $(FRONTEND_DIR) && npm run lint:fix
	@echo "$(GREEN)✅ Code formatting completed$(NC)"

format: ## Format code with Prettier and Black
	@echo "$(BLUE)Formatting code...$(NC)"
	@echo "$(YELLOW)Backend formatting...$(NC)"
	cd $(BACKEND_DIR) && black . && isort .
	@echo "$(YELLOW)Frontend formatting...$(NC)"
	cd $(FRONTEND_DIR) && npm run format
	@echo "$(GREEN)✅ Code formatting completed$(NC)"

type-check: ## Run TypeScript type checking
	@echo "$(BLUE)Running TypeScript type checking...$(NC)"
	cd $(FRONTEND_DIR) && npm run type-check
	@echo "$(GREEN)✅ Type checking completed$(NC)"

# Build Commands
build: ## Build the application
	@echo "$(BLUE)Building application...$(NC)"
	@echo "$(YELLOW)Building frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run build
	@echo "$(YELLOW)Building backend...$(NC)"
	cd $(BACKEND_DIR) && python -m build
	@echo "$(GREEN)✅ Build completed$(NC)"

build-docker: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker build -f infrastructure/docker/dev/Dockerfile.frontend -t $(REPO_NAME)-frontend:latest ./$(FRONTEND_DIR)
	docker build -f infrastructure/docker/dev/Dockerfile.backend -t $(REPO_NAME)-backend:latest .
	@echo "$(GREEN)✅ Docker images built$(NC)"

# Development Server Commands
frontend-dev: ## Start frontend development server
	@echo "$(BLUE)Starting frontend development server...$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

backend-dev: ## Start backend development server
	@echo "$(BLUE)Starting backend development server...$(NC)"
	cd services/core/api_gateway && uvicorn main:app --reload --host 0.0.0.0 --port 8000

orchestrator-dev: ## Start orchestrator development server
	@echo "$(BLUE)Starting orchestrator development server...$(NC)"
	cd services/orchestrator && python -m orchestrator.main

# Monitoring and Observability
monitoring-up: ## Start monitoring stack
	@echo "$(BLUE)Starting monitoring stack...$(NC)"
	docker-compose -f infrastructure/docker/dev/docker-compose.yml up -d prometheus grafana jaeger kibana
	@echo "$(GREEN)✅ Monitoring stack started$(NC)"
	@echo "$(CYAN)Access points:$(NC)"
	@echo "  - Grafana: http://localhost:3000"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Jaeger: http://localhost:16686"
	@echo "  - Kibana: http://localhost:5601"

monitoring-down: ## Stop monitoring stack
	@echo "$(BLUE)Stopping monitoring stack...$(NC)"
	docker-compose -f infrastructure/docker/dev/docker-compose.yml stop prometheus grafana jaeger kibana
	@echo "$(GREEN)✅ Monitoring stack stopped$(NC)"

# Database Management
db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "$(RED)WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose -f $(DOCKER_COMPOSE_FILE) stop postgres
	docker volume rm $(REPO_NAME)_postgres_data || true
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d postgres
	sleep 10
	make migrate
	@echo "$(GREEN)✅ Database reset complete$(NC)"

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	docker exec jaseci-postgres pg_dump -U jaseci_user jaseci_learning > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup created$(NC)"

# Security
security-scan: ## Run comprehensive security scan
	@echo "$(BLUE)Running comprehensive security scan...$(NC)"
	@echo "$(YELLOW)Running Bandit security scan...$(NC)"
	bandit -r $(BACKEND_DIR)/ -f json -o security-report.json
	@echo "$(YELLOW)Running Safety vulnerability check...$(NC)"
	safety check --json --output safety-report.json
	@echo "$(YELLOW)Scanning for secrets...$(NC)"
	truffleHog --directory . --json > secrets-report.json || true
	@echo "$(GREEN)✅ Security scan completed$(NC)"
	@echo "$(CYAN)Reports generated:$(NC)"
	@echo "  - security-report.json"
	@echo "  - safety-report.json"
	@echo "  - secrets-report.json"

# Performance
profile-backend: ## Profile backend performance
	@echo "$(BLUE)Profiling backend performance...$(NC)"
	cd $(BACKEND_DIR) && python -m cProfile -o profile.prof main.py
	@echo "$(GREEN)✅ Backend profile saved to profile.prof$(NC)"

profile-frontend: ## Profile frontend bundle
	@echo "$(BLUE)Analyzing frontend bundle...$(NC)"
	cd $(FRONTEND_DIR) && npm run analyze
	@echo "$(GREEN)✅ Frontend bundle analysis complete$(NC)"

# Documentation
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	cd docs && python -m http.server 8001
	@echo "$(GREEN)✅ Documentation available at http://localhost:8001$(NC)"

docs-build: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	cd docs && mkdocs build
	@echo "$(GREEN)✅ Documentation built in site/ directory$(NC)"

# Deployment
deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	kubectl apply -f infrastructure/kubernetes/staging/
	@echo "$(GREEN)✅ Deployment to staging initiated$(NC)"

deploy-production: ## Deploy to production environment
	@echo "$(RED)Deploying to PRODUCTION environment!$(NC)"
	@read -p "Are you sure? (yes/NO): " confirm && [ "$$confirm" = "yes" ]
	kubectl apply -f infrastructure/kubernetes/production/
	@echo "$(GREEN)✅ Deployment to production initiated$(NC)"

# Cleanup
clean: ## Clean up build artifacts
	@echo "$(BLUE)Cleaning up build artifacts...$(NC)"
	@echo "$(YELLOW)Cleaning frontend...$(NC)"
	cd $(FRONTEND_DIR) && rm -rf .next out dist
	@echo "$(YELLOW)Cleaning backend...$(NC)"
	cd $(BACKEND_DIR) && rm -rf build dist *.egg-info
	@echo "$(YELLOW)Cleaning Python cache...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(BLUE)Performing complete cleanup...$(NC)"
	rm -rf node_modules
	rm -rf .next
	rm -rf .pytest_cache
	rm -rf coverage
	@echo "$(GREEN)✅ Complete cleanup finished$(NC)"

# Health Checks
health-check: ## Check all service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(YELLOW)Checking database connectivity...$(NC)"
	curl -f http://localhost:5432 > /dev/null 2>&1 && echo "✅ PostgreSQL: Healthy" || echo "❌ PostgreSQL: Unhealthy"
	@echo "$(YELLOW)Checking API gateway...$(NC)"
	curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✅ API Gateway: Healthy" || echo "❌ API Gateway: Unhealthy"
	@echo "$(YELLOW)Checking frontend...$(NC)"
	curl -f http://localhost:3000 > /dev/null 2>&1 && echo "✅ Frontend: Healthy" || echo "❌ Frontend: Unhealthy"
	@echo "$(YELLOW)Checking Redis...$(NC)"
	redis-cli -h localhost -p 6379 ping > /dev/null 2>&1 && echo "✅ Redis: Healthy" || echo "❌ Redis: Unhealthy"
	@echo "$(YELLOW)Checking Neo4j...$(NC)"
	curl -f http://localhost:7474 > /dev/null 2>&1 && echo "✅ Neo4j: Healthy" || echo "❌ Neo4j: Unhealthy"
	@echo "$(GREEN)✅ Health check completed$(NC)"

# Status
status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) ps
