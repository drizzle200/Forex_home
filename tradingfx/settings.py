"""
Django settings for tradingfx project - LOCAL DEVELOPMENT ONLY
"""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = 'django-insecure-n8daet-k0j71klc-g=mz610sxpz3i20d=y-pjabh#k*7xgow_j'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1','0.0.0.0','fxhome.fly.dev']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'trade',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tradingfx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tradingfx.wsgi.application'

# Database - SQLite (local file)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

# Static files
# At the bottom of your settings.py, add:

# Static files (CSS, JavaScript, Images)
BASE_DIR = Path(__file__).resolve().parent.parent

# URL for static files
STATIC_URL = '/static/'

# Where Django collects static files for production
STATIC_ROOT = BASE_DIR / "staticfiles"

# Additional static directories
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# For development, ensure this is set
DEBUG = True


LOGIN_URL = '/login/'  # or whatever your login URL path is

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



