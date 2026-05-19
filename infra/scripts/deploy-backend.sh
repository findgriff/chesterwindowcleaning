#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

rsync -a --delete \
  --exclude '__pycache__' --exclude '.pytest_cache' --exclude 'tests' \
  "${REPO_ROOT}/backend/" dev:/opt/chesterwc/backend/
ssh dev 'systemctl restart chesterwc-backend'
sleep 1
ssh dev 'systemctl is-active chesterwc-backend' || {
  echo "✗ service did not start" >&2
  ssh dev 'journalctl -u chesterwc-backend -n 50 --no-pager' >&2
  exit 1
}
echo "✓ backend deployed and active"
