"""Test settings for ControlPanel test suite.

Inherits from ControlPanel.settings and configures safe in-memory test defaults.
"""
import os

# Fallback environment variables before importing settings
os.environ.setdefault("IPOL_HOST", "localhost")
os.environ.setdefault("IPOL_URL", "http://localhost:8000")

from ControlPanel.settings import *  # noqa: F401, F403

# Force in-memory SQLite database so disk db.sqlite3 is never touched
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Fast password hasher for test execution speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email backend for inspecting django.core.mail.outbox in tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Keep DEBUG false so view error handlers behave realistically
DEBUG = False

# Allow all hosts in test requests
ALLOWED_HOSTS = ["*"]
