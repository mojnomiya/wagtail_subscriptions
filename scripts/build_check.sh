#!/bin/bash
set -e

echo "=== Build Verification ==="
python -m pip install --upgrade pip build twine
python -m build
twine check dist/*
echo "✅ Package ready for deployment"
