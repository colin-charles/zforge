#!/usr/bin/env bash
# zforge CLI installer
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/colin-charles/zforge/main/install.sh)
set -e

echo "=[ zforge installer ]================================"
echo ""

# Require python3
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required"; exit 1; }

# Upgrade if already installed
if command -v zforge &>/dev/null; then
    CURRENT=$(zforge --version 2>/dev/null || echo "unknown")
    echo ">> zforge already installed: $CURRENT"
    echo ">> Upgrading to latest..."
    pip install --upgrade zforge
    echo ""
    echo ">> Updated to: $(zforge --version 2>/dev/null)"
    echo "====================================================="
    exit 0
fi

echo ">> Installing zforge from PyPI..."
pip install zforge

echo ""
echo "====================================================="
echo "  zforge installed successfully!"
echo ""
echo "  Run:       zforge --version"
echo "  New skill: zforge new my-skill"
echo "  Guide:     https://zero-forge.org/start/"
echo "====================================================="
