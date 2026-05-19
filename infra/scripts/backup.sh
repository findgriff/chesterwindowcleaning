#!/bin/bash
set -euo pipefail
DB=/var/lib/chesterwc/app.db
OUT_DIR=/var/backups/chesterwc
TS=$(date -u +%Y-%m-%d)
mkdir -p "$OUT_DIR"
sqlite3 "$DB" ".backup '$OUT_DIR/db-$TS.sqlite'"
gzip -f "$OUT_DIR/db-$TS.sqlite"
find "$OUT_DIR" -name 'db-*.sqlite.gz' -mtime +30 -delete
