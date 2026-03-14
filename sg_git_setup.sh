#!/usr/bin/env bash

# ══════════════════════════════════════════════════════════════════

# SuperGrok v82 — GitHub SSH Push Setup

# Repos:

# ssh://git@github.com:Appel420/Sovereignty-AI-Studio.git

# ssh://git@github.com:Sovereignty-One/SuperGrok-Heavy-4-2-Skeleton.git

# 

# Run once to configure remotes, then use dashboard GitHub panel

# ══════════════════════════════════════════════════════════════════

set -euo pipefail

SG_FILE=“SuperGrok_v82_FINAL.html”
BRANCH=“main”

echo “══ SuperGrok v82 · Git Setup ══”

# ── Verify SSH agent / key ──────────────────────────────────────

if ! ssh-add -l &>/dev/null 2>&1; then
echo “⚠️  SSH agent not running or no key loaded.”
echo “   Run: ssh-add ~/.ssh/id_ed25519  (or your key path)”
echo “   Then re-run this script.”
exit 1
fi

# ── Init repo if needed ─────────────────────────────────────────

if [ ! -d .git ]; then
git init
git checkout -b main 2>/dev/null || git checkout main
echo “✅ Git repo initialized”
fi

# ── Add .gitignore ──────────────────────────────────────────────

cat > .gitignore << ‘GITIGNORE’
.env
.sg_master_key
node_modules/
logs/
*.log
*.pyc
**pycache**/
.DS_Store
*.pem
*.key
*.crt
GITIGNORE
echo “✅ .gitignore written”

# ── Configure remotes ──────────────────────────────────────────

git remote remove appel420 2>/dev/null || true
git remote remove sovereignty-one 2>/dev/null || true

git remote add appel420       git@github.com:Appel420/Sovereignty-AI-Studio.git
git remote add sovereignty-one git@github.com:Sovereignty-One/SuperGrok-Heavy-4-2-Skeleton.git

echo “✅ Remotes configured:”
git remote -v

# ── Stage and commit ───────────────────────────────────────────

git add -A
git diff –cached –quiet && echo “Nothing to commit” && exit 0

MSG=“chore: SuperGrok v82 — port unification 9898, auth fix, SG_MEMORY, SG_AGENTS, SG_WATCHER, GitHub panel”
git commit -m “$MSG”
echo “✅ Committed: $MSG”

# ── Push both ─────────────────────────────────────────────────

echo “”
echo “Pushing to Appel420/Sovereignty-AI-Studio…”
git push appel420 $BRANCH –force-with-lease 2>&1 || git push appel420 $BRANCH 2>&1
echo “✅ Pushed to Appel420”

echo “”
echo “Pushing to Sovereignty-One/SuperGrok-Heavy-4-2-Skeleton…”
git push sovereignty-one $BRANCH –force-with-lease 2>&1 || git push sovereignty-one $BRANCH 2>&1
echo “✅ Pushed to Sovereignty-One”

echo “”
echo “══ DONE ══”
echo “Dashboard → GitHub Sync panel for future pushes via bridge”
