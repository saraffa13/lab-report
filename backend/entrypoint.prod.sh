#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput --settings=config.settings.production

echo "[entrypoint] Bootstrapping admin (idempotent)..."
python manage.py bootstrap_admin --settings=config.settings.production || true

echo "[entrypoint] Creating trial lab (idempotent)..."
python manage.py create_trial_lab --settings=config.settings.production || true

echo "[entrypoint] Starting gunicorn on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
