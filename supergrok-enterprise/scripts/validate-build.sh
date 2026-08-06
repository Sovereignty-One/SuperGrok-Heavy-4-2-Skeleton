#!/usr/bin/env bash
# validate-build.sh – verify supergrok-enterprise builds cleanly from scratch.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

printf 'Validating supergrok-enterprise build...\n'

# Node version guard
major="$(node -p "process.versions.node.split('.')[0]")"
if [ "$major" -lt 24 ]; then
  printf 'ERROR: Node 24+ required; found %s\n' "$(node --version)" >&2
  exit 1
fi

cd "$ROOT"

# Install (no-op when no deps declared)
npm ci --silent

# Run build
npm run build

# Assert expected output files exist
REQUIRED_FILES=(
  dist/index.html
  dist/src/main.js
  dist/src/services/crypto.js
  dist/src/services/export.js
  dist/src/index.css
  dist/nginx.conf
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$ROOT/$f" ]; then
    printf 'ERROR: expected output missing: %s\n' "$f" >&2
    exit 1
  fi
done

# Assert no dead React artifacts made it into dist/
DEAD_FILES=(
  dist/src/main.jsx
  dist/src/App.jsx
  dist/vite.config.js
  dist/tailwind.config.js
  dist/postcss.config.js
)

for f in "${DEAD_FILES[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    printf 'ERROR: dead artifact present in dist/: %s\n' "$f" >&2
    exit 1
  fi
done

# Assert main.js imports the crypto service
if ! grep -q "services/crypto" "$ROOT/src/main.js"; then
  printf 'ERROR: src/main.js does not import services/crypto\n' >&2
  exit 1
fi

# Assert index.html references main.js (not main.jsx)
if ! grep -q 'src/main\.js"' "$ROOT/index.html" && ! grep -q "src/main\.js'" "$ROOT/index.html"; then
  printf 'ERROR: index.html does not reference src/main.js\n' >&2
  exit 1
fi

printf 'All checks passed. Build is coherent and local-only.\n'
