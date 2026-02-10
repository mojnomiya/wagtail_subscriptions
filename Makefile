.PHONY: help lint format check test clean coverage

help:
	@echo "Available commands:"
	@echo "  make lint      - Run all linters (flake8, pylint, mypy, bandit)"
	@echo "  make format    - Format code with black and isort"
	@echo "  make check     - Check code formatting without changes"
	@echo "  make test      - Run tests with pytest"
	@echo "  make coverage  - Run tests with coverage report"
	@echo "  make clean     - Remove build artifacts"

lint:
	@echo "Running flake8..."
	python -m flake8 wagtail_subscriptions/ tests/
	@echo "Running pylint..."
	-python -m pylint wagtail_subscriptions/
	@echo "Running mypy..."
	-python -m mypy wagtail_subscriptions/
	@echo "Running bandit..."
	-python -m bandit -r wagtail_subscriptions/ -ll

format:
	@echo "Running black..."
	python -m black wagtail_subscriptions/ tests/
	@echo "Running isort..."
	python -m isort wagtail_subscriptions/ tests/

check:
	@echo "Checking black..."
	python -m black --check wagtail_subscriptions/ tests/
	@echo "Checking isort..."
	python -m isort --check-only wagtail_subscriptions/ tests/

test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ --cov=wagtail_subscriptions --cov-report=term --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
