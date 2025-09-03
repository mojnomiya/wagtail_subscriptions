# Contributing to Wagtail Subscriptions

We welcome contributions! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/your-username/wagtail-subscriptions.git
cd wagtail-subscriptions
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e .[dev]
```

4. Run tests to ensure everything works:
```bash
pytest
```

## Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting

Run these before submitting:
```bash
black wagtail_subscriptions tests
isort wagtail_subscriptions tests
flake8 wagtail_subscriptions tests
```

## Testing

- Write tests for new features
- Ensure all tests pass: `pytest`
- Check coverage: `coverage run -m pytest && coverage report`
- Aim for 90%+ test coverage

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with tests
3. Run the full test suite
4. Update documentation if needed
5. Submit a pull request with a clear description

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include Python/Django/Wagtail versions
- Provide minimal reproduction steps
- Include relevant error messages

## Documentation

- Update docstrings for new/changed functions
- Add examples for new features
- Update README.md if needed
- Build docs locally: `sphinx-build -b html docs docs/_build/html`

## Release Process

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release after merge
5. GitHub Actions will publish to PyPI

Thank you for contributing!