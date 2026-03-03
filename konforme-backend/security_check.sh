#!/bin/bash
set -e

echo "=== Konforme Security Check ==="
echo ""

echo "[1/3] Running safety (dependency vulnerability check)..."
pip install safety --quiet 2>/dev/null
safety check -r requirements.txt || echo "  Warning: safety found issues"
echo ""

echo "[2/3] Running bandit (static analysis)..."
pip install bandit --quiet 2>/dev/null
bandit -r . -x ./.venv,./tests --severity-level medium || echo "  Warning: bandit found issues"
echo ""

echo "[3/3] Running detect-secrets (credential scanning)..."
pip install detect-secrets --quiet 2>/dev/null
detect-secrets scan . --exclude-files '\.env\.example' || echo "  Warning: detect-secrets found issues"
echo ""

echo "=== Security check complete ==="
