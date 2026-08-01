"""
Django settings for netvault project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-6a1w=8+xt(6d$3vy^0$ke!ts6cw*nt=)nu-2*5$g2$1kfmk-b0',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true'

ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h]

# Token condiviso per la API interna di gestione utenti (accounts/), usata
# dal Portale per creare/modificare/eliminare account da remoto. L'endpoint
# è raggiungibile solo da localhost (regola Nginx), il token è una difesa
# aggiuntiva. Generarlo con: python -c "import secrets; print(secrets.token_urlsafe(32))"
INTERNAL_API_TOKEN = os.environ.get('INTERNAL_API_TOKEN', '')

# Anagrafica clienti condivisa: vive nel Portale (clienti/api/internal/),
# qui teniamo solo il client_id (UUID) sugli oggetti e risolviamo nome/
# indirizzo chiamando questa API in tempo reale. Generare PORTAL_API_TOKEN
# con lo stesso valore di INTERNAL_API_TOKEN nel .env del Portale.
PORTAL_INTERNAL_BASE_URL = os.environ.get('PORTAL_INTERNAL_BASE_URL', '')
PORTAL_API_TOKEN = os.environ.get('PORTAL_API_TOKEN', '')
# URL pubblico del Portale, solo per il link "Clienti (Portale)" in sidebar.
PORTAL_PUBLIC_URL = os.environ.get('PORTAL_PUBLIC_URL', '')

# Chiave Fernet per cifrare a riposo le credenziali salvate (password
# apparati, password reti wireless). Vedi rete/fields.py.
MASTER_ENCRYPTION_KEY = os.environ.get('MASTER_ENCRYPTION_KEY')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rete',
    'accounts',
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

ROOT_URLCONF = 'netvault.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'rete.context_processors.portal_public_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'netvault.wsgi.application'


# Database — SQLite: volumi piccoli (clienti, sezioni, apparati, parametri,
# credenziali, reti).

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'cliente-list'
LOGOUT_REDIRECT_URL = 'login'

if not DEBUG:
    # Il VPS è dietro Nginx che termina TLS e inoltra a Gunicorn su
    # localhost: senza questo header Django non saprebbe che la richiesta
    # originale era HTTPS.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static & media files

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
