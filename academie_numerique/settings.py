"""
Django settings for Academie Numerique project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production-very-secret-key-2025')

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'ninja',
    'corsheaders',
    'storages',
]

LOCAL_APPS = [
    'accounts',
    'core',
    'exams',
    'compositions',
    'correction',
    'bulletins',
    'notifications',
    'ai_engine',
    'certifications',
    'qcm',
    'plagiat',
    'gamification',
    'audittrail',
    'webhooks',
    'subscriptions',
    'cours',
    'devoirs',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'academie_numerique.urls'

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
                'core.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'academie_numerique.wsgi.application'

# Database
DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite3')

if DB_ENGINE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('DB_NAME', 'db.sqlite3'),
        }
    }
elif DB_ENGINE == 'postgresql':
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL', ''),
            conn_max_age=600
        )
    }
else: # mysql
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'academie_numerique'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('ar', 'العربية'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloud Storage for production (Render) - Choose ONE: S3, Cloudinary, or local
USE_S3_STORAGE = os.environ.get('USE_S3_STORAGE', 'False').lower() == 'true'
USE_CLOUDINARY_STORAGE = os.environ.get('USE_CLOUDINARY_STORAGE', 'False').lower() == 'true'

# Option 1: AWS S3 / DigitalOcean Spaces / MinIO
if USE_S3_STORAGE:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

# Option 2: Cloudinary (easier, free tier, no credit card)
elif USE_CLOUDINARY_STORAGE:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    # Support both CLOUDINARY_URL and individual credentials
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
    if CLOUDINARY_URL:
        # Parse CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
        import re
        match = re.match(r'cloudinary://(\d+):([\w]+)@([\w]+)', CLOUDINARY_URL)
        if match:
            CLOUDINARY_STORAGE = {
                'CLOUD_NAME': match.group(3),
                'API_KEY': match.group(1),
                'API_SECRET': match.group(2),
            }
        else:
            # Fallback to individual env vars
            CLOUDINARY_STORAGE = {
                'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
                'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
                'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
            }
    else:
        # Use individual env vars
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
            'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
            'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
        }
    
    MEDIA_URL = f'https://res.cloudinary.com/{CLOUDINARY_STORAGE["CLOUD_NAME"]}/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Google OAuth (configure via Render environment variables)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/accounts/google/callback/')

# Site URL for QR codes and external links (configure via Render)
SITE_URL = os.environ.get('SITE_URL', 'https://academie-composition.onrender.com')

# WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ═══ IA CONFIGURATION ═══
# Multi-provider avec fallback automatique : Groq → Gemini → Mistral → DeepSeek
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'groq')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

# Email via Resend API (free 3000/day, HTTP API, no SMTP timeout)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY', '')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', 're_bvSDVttk_NUo6pqFZNLgudshNoKgctVuy')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Académie Numérique <onboarding@resend.dev>')

# Role Passwords (configurable via env)
ROLE_PASSWORD_ADMIN = os.environ.get('ROLE_PASSWORD_ADMIN', 'admin2025')
ROLE_PASSWORD_CP = os.environ.get('ROLE_PASSWORD_CP', 'cp2026')
ROLE_PASSWORD_PROF = os.environ.get('ROLE_PASSWORD_PROF', 'prof2026')

# Session & Security
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG

# Laravel SSO Integration
LARAVEL_API_URL = os.environ.get('LARAVEL_API_URL', 'http://localhost:8000')

# Redis (background task queue — no Celery)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Auth backends
AUTHENTICATION_BACKENDS = [
    'accounts.laravel_auth.LaravelAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production Security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'compositions': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Ensure logs directory exists
os.makedirs(BASE_DIR / 'logs', exist_ok=True)