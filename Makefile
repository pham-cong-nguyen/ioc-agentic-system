# Makefile for IOC Agentic System
# Simplifies common development tasks

.PHONY: help install dev docker-up docker-down docker-logs db-init test clean format lint

# Default target
help:
	@echo "IOC Agentic System - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies in virtual environment"
	@echo "  make docker-up     - Start all services with Docker Compose"
	@echo "  make docker-down   - Stop all Docker services"
	@echo "  make db-init       - Initialize database with sample data"
	@echo ""
	@echo "Development:"
	@echo "  make dev           - Run development server"
	@echo "  make docker-logs   - View Docker logs"
	@echo "  make test          - Run tests"
	@echo "  make format        - Format code with black"
	@echo "  make lint          - Lint code with flake8"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Clean temporary files"
	@echo "  make reset-db      - Reset database (WARNING: deletes all data)"
	@echo ""

# Install dependencies
install:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Installing dependencies..."
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r backend/requirements.txt
	@echo "✓ Installation complete"

# Run development server
dev:
	@echo "Starting development server..."
	. venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8862

# Docker Compose commands
docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "✓ Services started"
	@echo ""
	@echo "Access points:"
	@echo "  - API: http://localhost:8862"
	@echo "  - Docs: http://localhost:8862/api/v1/docs"
	@echo "  - Frontend: http://localhost:80"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "✓ Services stopped"

docker-logs:
	docker-compose logs -f

docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Build complete"

# Database commands
db-init:
	@echo "Initializing database..."
	python scripts/init_db.py
	@echo "✓ Database initialized with sample data"

db-init-docker:
	@echo "Initializing database (Docker)..."
	docker-compose exec backend python scripts/init_db.py
	@echo "✓ Database initialized"

reset-db:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		make db-init-docker; \
	fi

# Testing
test:
	@echo "Running tests..."
	. venv/bin/activate && pytest -v

test-coverage:
	@echo "Running tests with coverage..."
	. venv/bin/activate && pytest --cov=backend --cov-report=html --cov-report=term

# Code quality
format:
	@echo "Formatting code with black..."
	. venv/bin/activate && black backend/ config/ tests/
	@echo "✓ Code formatted"

lint:
	@echo "Linting code..."
	. venv/bin/activate && flake8 backend/ config/ --max-line-length=120
	@echo "✓ Lint complete"

# Maintenance
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "✓ Cleanup complete"

# Environment setup
env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp .env.example .env; \
		echo "✓ .env file created"; \
		echo ""; \
		echo "⚠ Please edit .env and add your API keys"; \
	else \
		echo ".env file already exists"; \
	fi

# Quick start
quickstart: env docker-up db-init-docker
	@echo ""
	@echo "✓ Quick start complete! 🎉"
	@echo ""
	@echo "Access the application:"
	@echo "  - API Docs: http://localhost:8862/api/v1/docs"
	@echo "  - Frontend: http://localhost:80"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env and add your LLM API key"
	@echo "  2. Restart services: make docker-down && make docker-up"
	@echo "  3. View logs: make docker-logs"

# Health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8862/health | python3 -m json.tool || echo "✗ Backend not responding"
	@echo ""
