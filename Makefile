.PHONY: help lint format check test clean coverage build

help:
	@echo "Available commands:"
	@echo "  make lint      - Run all linters (flake8, pylint, mypy, bandit)"
	@echo "  make format    - Format code with black and isort"
	@echo "  make check     - Check code formatting without changes"
	@echo "  make test      - Run tests with pytest"
	@echo "  make coverage  - Run tests with coverage report"
	@echo "  make build     - Build package for distribution"
	@echo "  make clean     - Remove build artifacts"

lint:
	@echo "Running flake8..."
	uv run python -m flake8 wagtail_subscriptions/ tests/
	@echo "Running pylint..."
	-uv run python -m pylint wagtail_subscriptions/
	@echo "Running mypy..."
	-uv run python -m mypy wagtail_subscriptions/
	@echo "Running bandit..."
	-uv run python -m bandit -r wagtail_subscriptions/ -ll

format:
	@echo "Running black..."
	uv run python -m black wagtail_subscriptions/ tests/
	@echo "Running isort..."
	uv run python -m isort wagtail_subscriptions/ tests/

check:
	@echo "Checking black..."
	uv run python -m black --check wagtail_subscriptions/ tests/
	@echo "Checking isort..."
	uv run python -m isort --check-only wagtail_subscriptions/ tests/

test:
	uv run python -m pytest tests/ -v

coverage:
	uv run python -m pytest tests/ --cov=wagtail_subscriptions --cov-report=term --cov-report=html

build:
	@echo "Building package..."
	uv pip install --upgrade build twine
	uv run python -m build
	uv run twine check dist/*
	@echo "✅ Build complete"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
