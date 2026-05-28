#!/usr/bin/env sh
set -eu

cd /app

python - <<'PY'
import os
import sys

from app.db_url import (
    database_hostname,
    is_incomplete_render_host,
    raw_database_url_from_env,
)

url = raw_database_url_from_env()
if not url:
    print("ERROR: Set DATABASE_URL or DATABASE_EXTERNAL_URL.", file=sys.stderr)
    sys.exit(1)

host = database_hostname(url) or "unknown"
print(f"Configured database host: {host}")

if os.getenv("RENDER") and is_incomplete_render_host(host):
    print(
        "ERROR: Database host looks incomplete for Render "
        f"({host!r}). Use External Database URL in DATABASE_EXTERNAL_URL, "
        "or unlink the old Postgres resource from this web service.",
        file=sys.stderr,
    )
    sys.exit(1)
PY

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
