import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Core env-driven settings
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me")  # MUST be overridden in prod
DEBUG = os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")

PROJECT_NAME = os.environ.get("PROJECT_NAME", "Sager Interview Task")

# ALLOWED_HOSTS: comma-separated in env
# Example: "127.0.0.1,localhost,myapp.up.railway.app"
allowed_hosts = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(",") if h.strip()]

# If you want to be safe on Railway, you can also allow the Railway public domain dynamically:
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

# Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",

    # Local
    "drones",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # If you use WhiteNoise for static files in Docker/Railway, enable it:
    # "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cfehome.urls"  ###

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
            ],
        },
    },
]

WSGI_APPLICATION = "cfehome.wsgi.application"  ###

# Database

DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    ssl_require = os.getenv("DB_SSL_REQUIRE", "1") == "1"
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=ssl_require,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# If using WhiteNoise, set:
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# DRF + Swagger
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Sager Interview Task API",
    "DESCRIPTION": "Drone telemetry backend",
    "VERSION": "1.0.0",
}


# DEBUG should come from env in real deployments
# e.g. DEBUG=True locally, DEBUG=False on Railway
# DEBUG = config("DEBUG", default=False, cast=bool)   # if using decouple
# or:
DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

# Railway (and most platforms) run Django behind a reverse proxy that terminates HTTPS.
# This tells Django "treat requests as HTTPS when the proxy says so".
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Only enforce strict security in production
if not DEBUG:
    # Redirect HTTP -> HTTPS (safe in prod because Railway provides HTTPS at the edge)
    SECURE_SSL_REDIRECT = True

    # HSTS (be careful: browsers cache this)
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))  # 1 year default
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Secure cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # CSRF trusted origins (comma-separated)
    # Example env:
    # CSRF_TRUSTED_ORIGINS=https://yourapp.up.railway.app,https://yourdomain.com
    csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
    if csrf_origins:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(",") if o.strip()]
else:
    # Local dev / Docker: DO NOT redirect to https (you’re serving plain http)
    SECURE_SSL_REDIRECT = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"




# """
# Django settings for cfehome project.

# Generated by 'django-admin startproject' using Django 6.0.2.

# For more information on this file, see
# https://docs.djangoproject.com/en/6.0/topics/settings/

# For the full list of settings and their values, see
# https://docs.djangoproject.com/en/6.0/ref/settings/
# """
# from datetime import timedelta
# from dotenv import load_dotenv

# load_dotenv() 

# from decouple import config
# from django.core.management.utils import get_random_secret_key
# import os
# from pathlib import Path
# import sys
# import dj_database_url

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
# REPO_DIR = BASE_DIR.parent
# TEMPLATES_DIR = BASE_DIR / "templates"
# TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# PROJECT_NAME = config("PROJECT_NAME", default="Unset Project Name")

# # Quick-start development settings - unsuitable for production
# # See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# #default backend is console email backend which prints emails to the console
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config("EMAIL_HOST", cast=str, default=None)
# EMAIL_PORT = config("EMAIL_PORT", cast=str, default='587') # Recommended
# EMAIL_HOST_USER = config("EMAIL_HOST_USER", cast=str, default=None)
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", cast=str, default=None)
# EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)  # Use EMAIL_PORT 587 for TLS
# EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool, default=False)  # EUse MAIL_PORT 465 for SSL

# #via gmail
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# SERVER_EMAIL = EMAIL_HOST_USER
# ADMIN_USER_NAME=config("ADMIN_USER_NAME", default="Admin user")
# ADMIN_USER_EMAIL=config("ADMIN_USER_EMAIL", default=None)

# MANAGERS=[]
# ADMINS=[]
# if all([ADMIN_USER_NAME, ADMIN_USER_EMAIL]):
#     ADMINS +=[
#         (f'{ADMIN_USER_NAME}', f'{ADMIN_USER_EMAIL}')
#     ]
#     MANAGERS=ADMINS


# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = config("DJANGO_SECRET_KEY", cast=str, default=get_random_secret_key())

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config("DJANGO_DEBUG", cast=bool, default = False) 

# ALLOWED_HOSTS = [
#     ".railway.app", "djangofirst.com"]

# CSRF_TRUSTED_ORIGINS = [
#     "https://*.railway.app", "https://*.djangofirst.com"]


# #when DEBUG is False, we want to ensure that cookies are only sent over HTTPS connections for security reasons
# CSRF_COOKIE_SECURE = not DEBUG
# SESSION_COOKIE_SECURE= not DEBUG



# if DEBUG:
#     ALLOWED_HOSTS = ["*"]


# # Application definition

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'commando',
#     'drones',
#     "rest_framework",
#     "rest_framework_simplejwt",
#     "drf_spectacular",
# ]

# if DEBUG:
#     INSTALLED_APPS.append("whitenoise.runserver_nostatic")

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'cfehome.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [TEMPLATES_DIR],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'cfehome.wsgi.application'


# # Database
# # https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# DATABASE_URL = config("DATABASE_URL", cast=str, default="")
# if DATABASE_URL:
#     import dj_database_url
#     if DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
#         DATABASES= {
#             "default":dj_database_url.config(
#                 default=DATABASE_URL)}

# # Password validation
# # https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# # https://docs.djangoproject.com/en/6.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True

# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/6.0/howto/static-files/

# STATIC_URL = "static/"

# #send static files to this directory when we run collectstatic
# #locked files that do not change during runtime
# #external static file server
# STATIC_ROOT = BASE_DIR / "static_root"
# STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# #retain a copy of static files in our repo for development and debugging purposes
# #unlocked files that can change during dev
# STATICFILES_DIRS = [
#     BASE_DIR / "staticfiles"
# ]
    
# STORAGES = {
#     # ...
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }

# # Default primary key field type
# #for new models, use BigAutoField which is a 64-bit integer that can handle a larger number of records than the default AutoField which is a 32-bit integer
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# REST_FRAMEWORK = {
#     "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
#     "DEFAULT_AUTHENTICATION_CLASSES": (
#         "rest_framework_simplejwt.authentication.JWTAuthentication",
#     ),
#     "DEFAULT_PERMISSION_CLASSES": (
#         "rest_framework.permissions.IsAuthenticated",
#     ),
# }

# #for API documentation generation with drf-spectacular
# SPECTACULAR_SETTINGS = {
#     "TITLE": "Sager Interview Task API",
#     "DESCRIPTION": "Drone telemetry backend",
#     "VERSION": "1.0.0",
#     # Makes Swagger keep the token after refresh (nice UX)
#     "SWAGGER_UI_SETTINGS": {
#         "persistAuthorization": True,
#     },
#     # Explicit bearer auth in schema (so Swagger shows the lock properly)
#     "SECURITY": [{"bearerAuth": []}],
#     "COMPONENTS": {
#         "securitySchemes": {
#             "bearerAuth": {
#                 "type": "http",
#                 "scheme": "bearer",
#                 "bearerFormat": "JWT",
#             }
#         }
#     },
# }

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
# }

# # MQTT settings
# MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
# MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
# MQTT_TOPIC = os.getenv("MQTT_TOPIC", "drones/telemetry")
# MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
# MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")



# NO_FLY_ZONES = [
#     {
#         "name": "Airport Zone",
#         "lat": 31.99,
#         "lng": 35.98,
#         "radius_km": 2.0,
#     },
# ]