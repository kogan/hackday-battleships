import logging
import os

import environ

log = logging.getLogger(__name__)
mandatory_settings = ["DATABASE_URL", "SECRET_KEY"]

# If our mandatory settings aren't all already defined as environment variables
# try pulling them from Secret Manager
if not all(k in os.environ.keys() for k in set(mandatory_settings)):
    from utils import sm_helper

    secrets = sm_helper.access_secrets(mandatory_settings)
    os.environ.update(secrets)

env = environ.Env(DEBUG=(bool, False))


root = environ.Path(__file__) - 3
SITE_ROOT = root()

DEBUG = env("DEBUG", default=False)
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = env("SECRET_KEY", default=None)
if SECRET_KEY is None:
    log.warning("SECRET_KEY is not set! Using dev key.")
    SECRET_KEY = "dev-key-123"

# handle raw host(s), or http(s):// host(s), or no host.
if "CURRENT_HOST" in os.environ:
    HOSTS = []
    for h in env.list("CURRENT_HOST"):
        if "://" in h:
            h = h.split("://")[1]
        HOSTS.append(h)
else:
    HOSTS = ["django", "localhost"]

ALLOWED_HOSTS = HOSTS

# Enable Django security precautions if *not* running locally
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "cloudships",
    "django_extensions",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_ROOT = "/app/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATIC_HOST = "/"
STATIC_URL = "/static/"

MEDIA_ROOT = "media/"  # where files are stored on the local FS (in this case)
MEDIA_URL = "/media/"  # what is prepended to the image URL (in this case)


ROOT_URLCONF = "cloudships.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "cloudships.wsgi.application"

DATABASES = {"default": env.db(default="postgres:///cloudships")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Melbourne"
USE_I18N = True
USE_L10N = True
USE_TZ = True


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication"],
}

DISPATCH_URL = env("DISPATCH_URL", default="http:///")

CORS_ORIGIN_ALLOW_ALL = True
