"""Settings for the RPG support project."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default=env("SECRET_KEY", default="unsafe-development-key-change-me"))
DEBUG = env.bool("DJANGO_DEBUG", default=env.bool("DEBUG"))
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"]))
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "campaigns",
    "dashboard",
    "characters",
    "inventory",
    "ships",
    "maps",
    "history",
    "enemies",
    "encounters",
    "combat",
    "audio_panel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "audio_panel.context_processors.master_audio_panel",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
PROTECTED_MEDIA_ROOT = Path(env("PROTECTED_MEDIA_ROOT", default=str(MEDIA_ROOT)))
MAX_CHARACTER_LEVEL = env.int("MAX_CHARACTER_LEVEL", default=20)
MAX_IMAGE_UPLOAD_SIZE = env.int("MAX_IMAGE_UPLOAD_SIZE", default=5 * 1024 * 1024)
MAX_FILE_UPLOAD_SIZE = env.int("MAX_FILE_UPLOAD_SIZE", default=10 * 1024 * 1024)
MAX_DOCUMENT_UPLOAD_SIZE = env.int("MAX_DOCUMENT_UPLOAD_SIZE", default=20 * 1024 * 1024)
MAX_AUDIO_UPLOAD_SIZE = env.int("MAX_AUDIO_UPLOAD_SIZE", default=100 * 1024 * 1024)
PROTECTED_MEDIA_MODE = env("PROTECTED_MEDIA_MODE", default="django")
PROTECTED_MEDIA_ACCEL_PREFIX = env("PROTECTED_MEDIA_ACCEL_PREFIX", default="/_protected_media/")
X_ACCEL_REDIRECT_ENABLED = env.bool("X_ACCEL_REDIRECT_ENABLED", default=PROTECTED_MEDIA_MODE == "x-accel")
MAX_AUDIO_ASSET_UPLOAD_SIZE = env.int("MAX_AUDIO_ASSET_UPLOAD_SIZE", default=MAX_AUDIO_UPLOAD_SIZE)
MAX_ENEMY_IMAGE_UPLOAD_SIZE = env.int("MAX_ENEMY_IMAGE_UPLOAD_SIZE", default=5 * 1024 * 1024)
ENCOUNTER_BALANCE = {
    "difficulty_multipliers": {"easy": 0.7, "medium": 1.0, "hard": 1.35},
    "complexity_weights": {"simple": 1, "moderate": 2, "complex": 4},
    "action_economy_multipliers": ((1, 1.0), (2, 1.1), (5, 1.25), (12, 1.5)),
    "max_generated_enemies": 12,
    "action_economy_warning_ratio": 2,
    "operational_load_warning": 12,
}
COMBAT_NARRATIVE_HP_THRESHOLDS = {"normal": 50, "wounded": 25}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Production-safe defaults remain configurable so local development keeps working.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=21600)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
LOGGING = {
    "version": 1, "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
