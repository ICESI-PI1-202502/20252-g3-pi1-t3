from pathlib import Path
import sys, os
from django.conf.urls import handler404
from dotenv import load_dotenv

handler404 = "universitaryWellbeing.views.custom_404"
 
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['mi-bienestar-universitario.onrender.com','127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://mi-bienestar-universitario.onrender.com']

CSRF_COOKIE_SECURE = True  # Ensures CSRF cookie is only sent over HTTPS
CSRF_COOKIE_SAMESITE = 'None'

# Application definition
#project\BienestarUniversitario\settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'universitaryWellbeing.apps.UniversitarywellbeingConfig',
    'Analytics_Reports',  
    'management_CADI',
    'searchActivities',
    'tournaments',
    'social_projects',
    'notificaciones',
    'appointments', 

]

SITE_ID = 1
 

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'universitaryWellbeing.middleware.AsignarGrupoMiddleware',
]

ROOT_URLCONF = 'BienestarUniversitario.urls'

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
                'universitaryWellbeing.context_processors.notificaciones_context',
                'universitaryWellbeing.context_processors.user_rol',  # ← Sin 'e' al final

            ],
        },
    },
]

WSGI_APPLICATION = 'BienestarUniversitario.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


DATABASES = {
   'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("NAME"),
        'USER': os.environ.get("USER"),
        'PASSWORD': os.environ.get("PASSWORD"),
        'HOST': os.environ.get("HOST"),
        'PORT': '5432',
        'CONN_MAX_AGE': 0,
        'OPTIONS': {'sslmode': 'require'},
   }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

 #  Zona horaria de Colombia
TIME_ZONE = 'America/Bogota'
USE_TZ = True

# Habilitar internacionalización
USE_I18N = True

# Habilitar localización de fechas
USE_L10N = True

# IMPORTANTE: Usar zonas horarias (todas las fechas serán timezone-aware)
USE_TZ = True




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIR = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'LOCATION': BASE_DIR / 'media',
    },
    
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# ------------------------------
# Configuración de login/logout
# ------------------------------
LOGIN_URL = "/"              # login view
LOGIN_REDIRECT_URL = "/home/"   # where to send after login
LOGOUT_REDIRECT_URL = "/"       # where to send after logout

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if any(cmd in sys.argv for cmd in ["test", "pytest"]):
    INSTALLED_APPS += ["tournaments.tests"]
    # Desactiva migraciones del app real que está en conflicto
    #MIGRATION_MODULES = {"universitaryWellbeing": None}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jhonjhonshon4@gmail.com'
EMAIL_HOST_PASSWORD = 'aeoa zaaf gykq uetb'
DEFAULT_FROM_EMAIL = 'BU App <jhonjhonshon4@gmail.com>'

# Mejor práctica: usar variables de entorno
# EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

PASSWORD_RESET_TIMEOUT = 3600  # 1 hora (en segundos)

# Celery y Redis
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Timezone
CELERY_TIMEZONE = 'America/Bogota'
CELERY_ENABLE_UTC = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Notificaciones existentes (cada 1 minuto)
    'generar-notificaciones-diarias': {
        'task': 'notificaciones.tasks.generar_notificaciones_horarios_task',
        'schedule': crontab(minute='*/1'),
    },
    
     #  AGREGAR SOLO: Reconocimientos (RF8.1 - Premios)
    'verificar-reconocimientos-alcanzados': {
        'task': 'Analytics_Reports.tasks.verificar_y_otorgar_reconocimientos',
        'schedule': crontab(minute='*/1'),  # Diario 8 PM
    },
    
    #  AGREGAR: Inasistencias (RF8.1 - Inasistencias)
    'verificar-inasistencias-inscritos': {
        'task': 'Analytics_Reports.tasks.verificar_inasistencias_inscritos',
        'schedule': crontab(minute='*/1'),  # Diario 10 PM
    },
    
    #  AGREGAR: Encuestas (RF8.2)
    'enviar-encuestas-retroalimentacion': {
        'task': 'Analytics_Reports.tasks.enviar_encuestas_retroalimentacion',
        'schedule': crontab(minute='*/1'),  # Diario 6 PM
    },
}


if any(cmd in sys.argv for cmd in ("test", "pytest")):
    # Solo desactivar migraciones de tus apps, nunca de Django
    MIGRATION_MODULES = {
        "universitaryWellbeing": None,
        "appointments": None,
        "social_projects": None,
        "tournaments": None,
        "management_CADI": None,
        "searchActivities": None,
        "Analytics_Reports": None,
    }

    # Limpiar tests previos
    INSTALLED_APPS = [app for app in INSTALLED_APPS if ".tests" not in app]

    args = " ".join(sys.argv)

    if " social_projects" in args or args.endswith("social_projects"):
        INSTALLED_APPS += ["social_projects.tests.apps.SocialProjectsTestsConfig"]
    elif " tournaments" in args or args.endswith("tournaments"):
        INSTALLED_APPS += ["tournaments.tests.apps.TournamentsTestsConfig"]
    elif "management_CADI" in args or args.endswith("management_CADI"):
        INSTALLED_APPS += ["management_CADI.tests.apps.ManagementCADITestsConfig"]
    elif " searchActivities" in args or args.endswith("searchActivities"):
        INSTALLED_APPS += ["searchActivities.tests.apps.SearchActivitiesTestsConfig"]
    elif " appointments" in args or args.endswith("appointments"):
        INSTALLED_APPS += ["appointments.tests.apps.AppointmentsTestsConfig"]
    elif "Analytics_Reports" in args or args.endswith("Analytics_Reports"):
        INSTALLED_APPS += ["Analytics_Reports.tests.apps.AnalyticsReportsTestsConfig"]

    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    STATIC_ROOT = BASE_DIR / ".test-static"


# Configuración para tests
import sys

if 'test' in sys.argv:
    # Deshabilitar migraciones de apps con managed=False
    MIGRATION_MODULES = {
        'universitaryWellbeing': None,
        'notificaciones': None,
        'appointments': None,
        'management_CADI': None,
        'searchActivities': None,
        'tournaments': None,
        'social_projects': None,
    }



 