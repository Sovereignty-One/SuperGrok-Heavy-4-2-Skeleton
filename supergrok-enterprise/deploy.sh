#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' 'Local SuperGrok Enterprise build'

major="$(node -p "process.versions.node.split('.')[0]")"
if [ "$major" -lt 24 ]; then
  printf 'Node 24+ required; found %s\n' "$(node --version)" >&2
  exit 1
fi

npm ci
npm run build
test -f dist/index.html
test -f dist/src/main.js
printf 'Local build passed with %s\n' "$(node --version)"
