# syntax=docker/dockerfile:1.7
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# WeasyPrint runtime dependencies (Pango, Cairo, GDK-PixBuf, fonts)
# plus libpq for psycopg.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
      libcairo2 libgdk-pixbuf-2.0-0 \
      shared-mime-info \
      libffi-dev \
      libpq5 libpq-dev \
      fonts-dejavu-core fonts-liberation \
      curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ /app/requirements/

# ---------- development image ----------
FROM base AS development
RUN pip install --upgrade pip && pip install -r requirements/development.txt
COPY . /app/
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---------- production image ----------
FROM base AS production
RUN pip install --upgrade pip && pip install -r requirements/production.txt
COPY . /app/
# SECRET_KEY is required by settings at import time; use a dummy just for collectstatic.
RUN DJANGO_SECRET_KEY=build-time-dummy \
    python manage.py collectstatic --noinput --settings=config.settings.production || true
RUN chmod +x /app/entrypoint.prod.sh
EXPOSE 8000
CMD ["/app/entrypoint.prod.sh"]
