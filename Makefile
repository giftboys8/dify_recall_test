# Makefile for Dify KB Recall Testing Tool

.PHONY: help install install-dev test test-unit test-integration lint format clean build run-test run-web setup

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

# Docker targets (if needed)
docker-build:
	docker build -t dify-kb-tester .

docker-run:
	docker run -p 8080:8080 dify-kb-tester