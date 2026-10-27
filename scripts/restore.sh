#!/usr/bin/env bash
# Restore a backup made by scripts/backup.sh into a fresh compose stack.
# Usage: scripts/restore.sh backups/db-STAMP.sql.gz backups/media-STAMP.tar.gz
# Put the matching env-STAMP file in place as .env BEFORE running this.
set -euo pipefail
cd "$(dirname "$0")/.."
DB="$1"; MEDIA="$2"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
$COMPOSE up -d postgres
until $COMPOSE exec -T postgres pg_isready -U postgres >/dev/null 2>&1; do sleep 2; done
$COMPOSE exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS brightbean;" -c "CREATE DATABASE brightbean;"
gunzip -c "$DB" | $COMPOSE exec -T postgres psql -U postgres -q brightbean
$COMPOSE run --rm --no-deps -T --entrypoint sh app -c "rm -rf /app/media/* && tar -xzf - -C /app/media" < "$MEDIA"
$COMPOSE up -d
echo "restore done; log in and check Social accounts are still CONNECTED (same .env required)"
