#!/usr/bin/env bash
# Auto-format all Python code with black

set -e

cd "$(dirname "$0")/.."

echo "=== Formatting with black ==="
uv run black backend/
