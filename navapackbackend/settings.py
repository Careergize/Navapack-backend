import os
import dj_database_url
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security / environment-driven settings -------------------------------
# NEVER hardcode SECRET_KEY or leave DEBUG=True in production.
# Set SECRET_KEY and DEBUG as real App Settings in Azure App Service
# (Configuration -> Application settings), not just in your local .env.
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-change-this-secret-key-before-production"
)
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Restrict this in production instead of '*'. Include your Azure hostname
# and custom domain so Django's host-header check doesn't reject requests.
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "navapack-backend.azurewebsites.net,navapacksolutions.com,www.navapacksolutions.com,localhost,127.0.0.1",
).split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "products",
    "Auth",
]

# CorsMiddleware must sit as high as possible, and before CommonMiddleware.
# This ordering is already correct.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "navapackbackend.urls"

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

WSGI_APPLICATION = "navapackbackend.wsgi.application"
ASGI_APPLICATION = "navapackbackend.asgi.application"

# --- Database ---------------------------------------------------------------
# If this raises on startup (DATABASE_URL missing on Azure), Django never
# boots and NO response -- including CORS headers -- will ever be sent.
# Double-check DATABASE_URL is set under Azure App Service -> Configuration
# -> Application settings, since load_dotenv() only reads a local .env file
# and does nothing on Azure.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS --------------------------------------------------------------------
# Frontend origins allowed to call this API.
CORS_ALLOWED_ORIGINS = [
    "https://www.navapacksolutions.com",
    "https://navapacksolutions.com",
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # CRA / Next.js default
    "https://navapack-backend.azurewebsites.net",
]

# If you allow credentials (cookies, HTTP Auth, tokens via authorization headers)
CORS_ALLOW_CREDENTIALS = True

# --- CSRF ----------------------------------------------------------------
# Needed in addition to CORS_ALLOWED_ORIGINS if you ever POST from the
# frontend using session auth / cookies (not needed for pure token auth,
# but harmless to include and saves a headache later).
CSRF_TRUSTED_ORIGINS = [
    "https://www.navapacksolutions.com",
    "https://navapacksolutions.com",
    "https://navapack-backend.azurewebsites.net",
]