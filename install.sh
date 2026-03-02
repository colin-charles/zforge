#!/usr/bin/env bash
# zforge CLI installer
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/colin-charles/zforge/main/install.sh)
set -e

INSTALL_DIR="${HOME}/.zforge"
REPO_URL="https://github.com/colin-charles/zforge"

echo "=[ zforge installer ]================================"
echo ""

if command -v zforge &>/dev/null; then
    echo ">> zforge already installed: $(zforge --version 2>/dev/null)"
    echo ">> To update: cd ${INSTALL_DIR} && git pull && pip install -e ."
    exit 0
fi

command -v git >/dev/null 2>&1 || { echo "ERROR: git required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required"; exit 1; }

if [ -d "${INSTALL_DIR}/.git" ]; then
    echo ">> Updating existing install at ${INSTALL_DIR}..."
    cd "${INSTALL_DIR}" && git pull --quiet
else
    echo ">> Cloning zforge to ${INSTALL_DIR}..."
    git clone --quiet "${REPO_URL}" "${INSTALL_DIR}"
fi

echo ">> Setting up Python environment..."
cd "${INSTALL_DIR}"
python3 -m venv venv
source venv/bin/activate
pip install -q -e .

echo ""
echo "====================================================="
echo "  zforge installed!"
echo ""
echo "  Activate:  source ${INSTALL_DIR}/venv/bin/activate"
echo "  Run:       zforge --version"
echo "  Guide:     https://zero-forge.org/start/"
echo "====================================================="
