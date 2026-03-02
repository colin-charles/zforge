#!/usr/bin/env bash
# install.sh — ZeroForge Skill Dev toolkit installer
# Estimated time: 10-30 seconds (no large downloads required)
set -e

echo "🔴 Installing ZeroForge Skill Dev toolkit..."
echo "⏱  Estimated time: 10-30 seconds"
echo ""

echo "🐍 Installing Python packages..."
pip install -q requests pathlib

echo "🔧 Making scripts executable..."
chmod +x "$(dirname $0)/scripts/"*.py 2>/dev/null || true

echo ""
echo "✅ ZeroForge CLI installed!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Run this to get started:"
echo ""
echo "    zforge hello"
echo ""
echo "  Full guide: https://zero-forge.org/start/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
