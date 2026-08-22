from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────
# Chargement automatique du fichier .env
# ─────────────────────────────────────────────────────
def _charger_env(env_path):
    if not env_path.exists():
        return
    with open(env_path, encoding='utf-8') as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#') or '=' not in ligne:
                continue
            cle, _, valeur = ligne.partition('=')
            cle = cle.strip()
            valeur = valeur.strip().strip('"').strip("'")
            if cle and cle not in os.environ:
                os.environ[cle] = valeur


_charger_env(BASE_DIR / '.env')

# ─────────────────────────────────────────────────────
# SECRETS — toujours via variables d'environnement
# ─────────────────────────────────────────────────────
_default_key = 'django-insecure-edugroupe-dev-only-CHANGE-IN-PRODUCTION'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', _default_key)

if SECRET_KEY == _default_key and os.environ.get('DJANGO_DEBUG', 'True') != 'True':
    raise RuntimeError(
        "DJANGO_SECRET_KEY doit être définie en production via variable d'environnement."
    )

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()]

# ─────────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'eleves',
    'enseignants',
    'emploi_du_temps',
    'notes',
    'presences',
    'paiements',
    'rapports',
]

# ─────────────────────────────────────────────────────
# MIDDLEWARE — rate limiting inclus
# ─────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'eleves.middleware.LoginRateLimitMiddleware',
    'eleves.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'groupe_scolaire.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'eleves.context_processors.groupe_scolaire',
                'eleves.context_processors.user_role',
                'eleves.context_processors.notifications',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'groupe_scolaire.wsgi.application'

# ─────────────────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────────────────
if os.environ.get('DB_ENGINE') == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'edugroupe'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─────────────────────────────────────────────────────
# MOT DE PASSE
# ─────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────────────
# INTERNATIONALISATION
# ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────────
# FICHIERS STATIQUES ET MÉDIAS
# ─────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Taille maximale des uploads (5 Mo)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────
# CACHE — mémoire locale (dev), Redis recommandé en prod
# ─────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,
    }
}

# ─────────────────────────────────────────────────────
# AUTHENTIFICATION & SESSIONS
# ─────────────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Session expire après 2h d'inactivité
SESSION_COOKIE_AGE = 7200
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Réinitialisation mot de passe expire en 1h
PASSWORD_RESET_TIMEOUT = 3600

# Tentatives de login max avant blocage temporaire (géré par middleware)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_BLOCK_DURATION = 300  # 5 minutes

# ─────────────────────────────────────────────────────
# SÉCURITÉ — Headers et cookies
# ─────────────────────────────────────────────────────
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

CSRF_COOKIE_HTTPONLY = False  # Doit rester False pour que JS puisse lire le token
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# En production (HTTPS) — activer ces options via variable d'environnement
if os.environ.get('DJANGO_HTTPS', 'False') == 'True':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ─────────────────────────────────────────────────────
# LOGGING — Audit trail
# ─────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'audit': {
            'format': '[%(asctime)s] AUDIT %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 Mo
            'backupCount': 5,
            'formatter': 'audit',
            'encoding': 'utf-8',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'edugroupe.audit': {
            'handlers': ['audit_file', 'console'] if DEBUG else ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'edugroupe.security': {
            'handlers': ['security_file', 'console'] if DEBUG else ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Créer le dossier logs s'il n'existe pas
import pathlib
pathlib.Path(BASE_DIR / 'logs').mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────
# EMAIL — notifications aux parents
# ─────────────────────────────────────────────────────
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL', 'no-reply@edugroupe.local'
)

# ─────────────────────────────────────────────────────
# SAUVEGARDES — mot de passe AES-256 (optionnel)
# ─────────────────────────────────────────────────────
# Définir BACKUP_PASSWORD dans .env pour activer le chiffrement
BACKUP_PASSWORD = os.environ.get('BACKUP_PASSWORD', '')
