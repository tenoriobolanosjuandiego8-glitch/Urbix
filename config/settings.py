"""
Configuración de Django para el proyecto URBIX.
Movilidad Inteligente en Popayán.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv es opcional; si no está instalado, se puede seguir
    # usando variables de entorno del sistema operativo directamente.
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad / entorno
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'inseguro-clave-de-desarrollo-cambiar-en-produccion-URBIX-2026'
)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

if not DEBUG and SECRET_KEY.startswith('inseguro-clave-de-desarrollo'):
    raise RuntimeError(
        'DJANGO_SECRET_KEY no está configurada (o sigue con el valor de ejemplo) '
        'y DJANGO_DEBUG=False. Define una clave real en tu archivo .env antes de '
        'desplegar a producción — nunca uses la clave de ejemplo fuera de tu computador.'
    )

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    h for h in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if h
]

if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Terceros
    'rest_framework',
    'rest_framework.authtoken',

    # Apps propias de URBIX
    'accounts',
    'buses',
    'routes',
    'gps',
    'map',
    'restaurants',
    'hotels',
    'tourism',
    'events',
    'notifications',
    'dashboard',
    'reports',
    'interactions',
    'api',
    'assistant',
    'business',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.security_middleware.SecurityHeadersMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.ActivityLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notifications',
                'business.context_processors.pending_businesses',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Base de datos
# Desarrollo: SQLite (por defecto, cero configuración)
# Producción: PostgreSQL. Si existe la variable DATABASE_URL (Render la
# Si no, usa las variables DJANGO_DB_* manuales, o SQLite si no hay nada.
import dj_database_url

if os.environ.get('DATABASE_URL'):
    database_url = os.environ['DATABASE_URL']
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=database_url.startswith(('postgres://', 'postgresql://')),
        )
    }
elif os.environ.get('DJANGO_DB_ENGINE') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DJANGO_DB_NAME', 'urbix'),
            'USER': os.environ.get('DJANGO_DB_USER', 'urbix'),
            'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', ''),
            'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
            'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
elif os.environ.get('DJANGO_DB_ENGINE') in ('mysql', 'mariadb'):
    # PyMySQL se hace pasar por el driver mysqlclient (evita compilar en C,
    # que en Windows suele fallar igual que nos pasó con Pillow).
    import pymysql
    pymysql.install_as_MySQLdb()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DJANGO_DB_NAME', 'urbix'),
            'USER': os.environ.get('DJANGO_DB_USER', 'urbix'),
            'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', ''),
            'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
            'PORT': os.environ.get('DJANGO_DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
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

# Autenticación
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:redirect'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Internacionalización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Archivos estáticos y multimedia
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # usado por collectstatic en producción
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Correo (para verificación / recuperación de contraseña)
# En desarrollo se imprime en consola; en producción usar SMTP real.
if os.environ.get('DJANGO_EMAIL_BACKEND') == 'smtp':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '')
    EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = True
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'URBIX <no-responder@urbix.co>'

# Asistente IA (chatbot + búsqueda inteligente) — usa la API de Claude.
# La clave se lee directamente de la variable de entorno ANTHROPIC_API_KEY
# en assistant/ai.py (no hace falta duplicarla aquí), pero la dejamos
# documentada: agrégala a tu archivo .env como:
#   ANTHROPIC_API_KEY=sk-ant-...

# Seguridad adicional para producción (se activa cuando DEBUG=False)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SSL_REDIRECT', 'False') == 'True'
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Registro de errores y actividad (logging)
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'activity_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'activity.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'error_file'], 'level': 'INFO'},
        'urbix.activity': {'handlers': ['activity_file'], 'level': 'INFO', 'propagate': False},
    },
}

# Paginación por defecto usada por las vistas de listados
URBIX_PAGE_SIZE = 9

# Django REST Framework — API pensada para una futura app móvil
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
