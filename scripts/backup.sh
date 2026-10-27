#!/usr/bin/env bash
# Daily backup for the docker-compose deployment: Postgres dump, media volume,
# and the .env (without it the encrypted social tokens cannot be decrypted).
# Usage: scripts/backup.sh [/path/to/backups]   (default: ./backups)
# Cron example (02:30 daily, keep 14 days):
#   30 2 * * * cd /opt/brightbean-studio && scripts/backup.sh /var/backups/brightbean >> /var/log/brightbean-backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."
DEST="${1:-./backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
mkdir -p "$DEST"

$COMPOSE exec -T postgres pg_dump -U postgres --no-owner brightbean | gzip > "$DEST/db-$STAMP.sql.gz"
$COMPOSE run --rm --no-deps -T --entrypoint tar app -czf - -C /app/media . > "$DEST/media-$STAMP.tar.gz"
cp .env "$DEST/env-$STAMP"
chmod 600 "$DEST/env-$STAMP"

find "$DEST" -maxdepth 1 -type f -mtime +"$KEEP_DAYS" -delete
echo "$(date -Is) backup ok: $(du -sh "$DEST" | cut -f1) in $DEST"
