#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

rsync -a --delete \
  --exclude '.DS_Store' --exclude '*.swp' \
  "${REPO_ROOT}/site/" dev:/opt/chesterwc/site/
ssh dev 'systemctl reload caddy'
echo "✓ site deployed"
