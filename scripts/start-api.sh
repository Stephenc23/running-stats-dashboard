#!/usr/bin/env sh
set -eu

cd /app

DB_HOST="$(python - <<'PY'
import os
from urllib.parse import urlparse

url = os.getenv("DATABASE_URL", "")
if not url:
    print("missing")
else:
    try:
        print(urlparse(url).hostname or "unknown")
    except Exception:
        print("unknown")
PY
)"

if [ "$DB_HOST" = "missing" ]; then
  echo "ERROR: DATABASE_URL is not set."
  exit 1
fi

echo "Configured database host: $DB_HOST"

if [ "${RENDER:-}" != "" ] && [ "$DB_HOST" = "db" ]; then
  echo "ERROR: DATABASE_URL points to host 'db', which only works in docker-compose."
  echo "Set DATABASE_URL to your Render Postgres internal/external hostname."
  exit 1
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  MIGRATION_ATTEMPTS="${MIGRATION_ATTEMPTS:-8}"
  MIGRATION_DELAY_SECONDS="${MIGRATION_DELAY_SECONDS:-3}"
  attempt=1
  while [ "$attempt" -le "$MIGRATION_ATTEMPTS" ]; do
    echo "Running database migrations (attempt $attempt/$MIGRATION_ATTEMPTS)..."
    if alembic upgrade head; then
      break
    fi

    if [ "$attempt" -eq "$MIGRATION_ATTEMPTS" ]; then
      echo "ERROR: migrations failed after $MIGRATION_ATTEMPTS attempts."
      exit 1
    fi

    echo "Migration failed; retrying in ${MIGRATION_DELAY_SECONDS}s..."
    sleep "$MIGRATION_DELAY_SECONDS"
    attempt=$((attempt + 1))
  done
fi

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
