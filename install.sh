#!/usr/bin/env bash
# Dokima Installer — one-command setup
# Usage: curl -sSL https://get.dokima.dev | bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

err() { echo -e "${RED}[✗]${NC} $*"; exit 1; }
log() { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }

# ── Config (override via env) ────────────────────────────────────────
PANEL_REPO="${PANEL_REPO:-https://github.com/siongsheng/dokima.git}"
PANEL_DIR="${PANEL_DIR:-$HOME/.local/share/dokima}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"

# ── 1. Dependency Checks ────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || err "Python 3.6+ required but not found. Install Python: https://python.org"
command -v gh      >/dev/null 2>&1 || err "GitHub CLI (gh) required but not found. Install: https://cli.github.com"
command -v hermes  >/dev/null 2>&1 || err "Hermes Agent required but not found. Install: https://hermes-agent.nousresearch.com"

log "All prerequisites found: python3, gh, hermes"

# ── 2. Clone / Update Repo ──────────────────────────────────────────
if [ -d "$PANEL_DIR/.git" ]; then
    log "Repository exists — pulling latest"
    git -C "$PANEL_DIR" pull --ff-only 2>/dev/null || warn "Could not pull (dirty tree? skipping)"
else
    log "Cloning dokima to $PANEL_DIR"
    mkdir -p "$(dirname "$PANEL_DIR")"
    git clone "$PANEL_REPO" "$PANEL_DIR"
fi

# ── 3. Symlink dokima ───────────────────────────────────────────────
mkdir -p "$BIN_DIR"
if [ -L "$BIN_DIR/dokima" ] || [ -f "$BIN_DIR/dokima" ]; then
    log "dokima already linked in $BIN_DIR"
else
    ln -sf "$PANEL_DIR/dokima" "$BIN_DIR/dokima"
    log "Linked dokima → $BIN_DIR/dokima"
fi

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo "  Dokima installed: $BIN_DIR/dokima"
echo ""
echo "  Next steps:"
echo "    dokima --help"
echo "    See docs/setup.md for full configuration"
