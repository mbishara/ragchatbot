#!/usr/bin/env bash
# Run all code quality checks from the repo root

set -e

cd "$(dirname "$0")/.."

echo "=== Formatting check (black) ==="
uv run black --check backend/

echo ""
echo "=== Tests (pytest) ==="
cd backend && uv run pytest tests/ -v
