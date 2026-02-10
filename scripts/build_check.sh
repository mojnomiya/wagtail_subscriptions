#!/bin/bash
set -e

echo "=== Build Verification ==="
uv pip install --upgrade build twine
uv run python -m build
uv run twine check dist/*
echo "✅ Package ready for deployment"
