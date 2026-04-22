# LabReport Pro — Deployment

## Local development

```bash
cp .env.example .env
docker compose up --build
```

Services:
- Backend API: http://localhost:8000 (admin at /admin/, docs at /api/docs/)
- Frontend: http://localhost:5173
- Postgres: localhost:5432 (user/pass/db from .env)
- Redis: localhost:6379

Run one-off Django commands:
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
```

Run tests:
```bash
docker compose exec backend pytest
```

## Production (overview — details expanded in Phase 6)

Use `docker-compose.prod.yml` with a separate `.env.production` file.
Must set, at minimum:

- `DJANGO_SECRET_KEY` — long random string
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=yourdomain.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com`
- `DATABASE_URL=postgres://...`
- `REDIS_URL=redis://...`
- `SENTRY_DSN=...` (optional)

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

Nginx terminates TLS and reverse-proxies to backend + frontend. A
`deploy/nginx.prod.conf` file will ship in Phase 6 along with
Let's Encrypt wiring and a backup runbook.

## Backups

- Daily `pg_dump` snapshots (automated in Phase 6 via a Celery beat job
  or a system cron, depending on host).
- Media directory (`backend_media` volume) to object storage.
- Retention: 30 days rolling, monthly archives held longer.
