import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
import dotenv

# Build paths inside the project.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
dotenv.load_dotenv(BASE_DIR / ".env")

# Debug setting
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

# Security settings
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "local-only-development-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required when DEBUG is False."
        )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,testserver,.onrender.com",
    ).split(",")
    if host.strip()
]

# Render automatically provides this environment variable.
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]
if render_hostname:
    origin = f"https://{render_hostname}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

additional_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if additional_csrf:
    for origin in additional_csrf.split(","):
        origin_clean = origin.strip()
        if origin_clean and origin_clean not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin_clean)


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    "cloudinary_storage",
    "myapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "myapp.middleware.RequestLoggingMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "myproject.wsgi.application"


# Database: SQLite locally, PostgreSQL on Render via DATABASE_URL
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# Static files: CSS, JavaScript and other assets
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Cloudinary Media Storage Configuration
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET", ""),
}

USE_CLOUDINARY = bool(
    os.environ.get("CLOUDINARY_CLOUD_NAME")
    and os.environ.get("CLOUDINARY_API_KEY")
    and os.environ.get("CLOUDINARY_API_SECRET")
)

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"
        if USE_CLOUDINARY
        else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Compatibility aliases for third-party packages (e.g. django-cloudinary-storage)
STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]
DEFAULT_FILE_STORAGE = STORAGES["default"]["BACKEND"]


# Uploaded media files (e.g. transaction receipts)
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))


# Email configuration standardized using EMAIL_BACKEND
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)


# Authentication redirects
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/transactions/"
LOGOUT_REDIRECT_URL = "/"


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# MongoDB configuration for Chat History and User Feedback
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "spendwise")

# Third-party Exchange Rate API configuration
EXCHANGE_RATE_API_URL = os.environ.get(
    "EXCHANGE_RATE_API_URL",
    "https://open.er-api.com/v6/latest/USD",
)
EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY", "")

# Production Security Enhancements
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = (
        os.environ.get("SECURE_SSL_REDIRECT", "False").lower() == "true"
    )
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "True").lower() == "true"
    )
    CSRF_COOKIE_SECURE = (
        os.environ.get("CSRF_COOKIE_SECURE", "True").lower() == "true"
    )
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
