"""Testing overrides. Fast, deterministic, isolated."""
from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

# Rate limiting is a production concern; a full test session makes more login
# attempts than the production limits allow (10/min) and would flakily throttle.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000/min",
    "user": "1000/min",
    "login": "1000/min",
    "otp": "1000/min",
}

# Silence logs in test runs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}
