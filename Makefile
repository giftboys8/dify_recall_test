# Makefile for Dify KB Recall Testing Tool

.PHONY: help install install-dev test test-unit test-integration lint format clean build run-test run-web setup docker-build docker-up docker-down docker-dev docker-logs docker-clean docker-restart docker-shell docker-status

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install the package and dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build the package"
	@echo "  run-test     - Run recall testing"
	@echo "  run-web      - Start web interface"
	@echo "  setup        - Initial project setup"
	@echo ""
	@echo "Docker targets:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up    - Start all services with Docker Compose"
	@echo "  docker-down  - Stop all Docker services"
	@echo "  docker-dev   - Start development environment"
	@echo "  docker-logs  - View Docker logs"
	@echo "  docker-clean - Clean Docker images and volumes"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install -r requirements.txt

# Testing
test: test-unit test-integration

test-unit:
	pytest tests/unit/ -v --cov=src --cov-report=html

test-integration:
	pytest tests/integration/ -v

# Code quality
lint:
	flake8 src/ tests/ --max-line-length=100
	mypy src/

format:
	black src/ tests/ --line-length=100

# Build and clean
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

# Run commands
run-test:
	python main.py test --config config/default.json --test-file tests/test_cases/sample.csv --generate-viz

run-web:
	python main.py web-server --port 8080

# Setup
setup:
	@echo "Setting up project..."
	mkdir -p data/input data/output/results
	mkdir -p logs
	chmod +x scripts/*.sh
	@echo "Project setup complete!"

# Development helpers
dev-server:
	python main.py web-server --host 0.0.0.0 --port 8080

quick-test:
	python main.py quick-start

# Docker targets
docker-build:
	@echo "Building Docker image..."
	docker-compose build

docker-up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started. Access the application at:"
	@echo "  - Main app: http://localhost:8080"
	@echo "  - API: http://localhost:5000"
	@echo "  - Streamlit: http://localhost:8501"

docker-down:
	@echo "Stopping all services..."
	docker-compose down

docker-dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d
	@echo "Development environment started with hot reload enabled"

docker-logs:
	@echo "Viewing application logs..."
	docker-compose logs -f kb-app

docker-clean:
	@echo "Cleaning Docker images and volumes..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

docker-restart:
	@echo "Restarting application..."
	docker-compose restart kb-app

docker-shell:
	@echo "Opening shell in application container..."
	docker-compose exec kb-app bash

docker-status:
	@echo "Docker services status:"
	docker-compose ps