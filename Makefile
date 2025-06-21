.PHONY: help install install-dev run run-docker test lint format clean

help: ## Show this help
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements/prod.txt

install-dev: ## Install development dependencies
	pip install -r requirements/dev.txt

run: ## Run application locally
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-docker: ## Run application in Docker
	cd docker/prod && docker-compose up -d

stop-docker: ## Stop Docker containers
	cd docker/prod && docker-compose down

logs: ## Show Docker logs
	cd docker/prod && docker-compose logs -f

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html

lint: ## Run linting
	flake8 app/
	mypy app/

format: ## Format code
	black app/
	isort app/

format-check: ## Check code formatting
	black --check app/
	isort --check-only app/

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage

docker-build: ## Build Docker image
	cd docker/prod && docker-compose build --no-cache

docker-clean: ## Clean Docker images and containers
	docker system prune -f
	docker volume prune -f

setup: ## Complete project setup
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements/dev.txt
	cp env.example .env
	@echo "Project configured! Activate virtual environment: source .venv/bin/activate"

dev: ## Run in development mode
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug