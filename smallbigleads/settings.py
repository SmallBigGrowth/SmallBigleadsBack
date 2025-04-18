"""
Django settings for smallbigleads project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from decouple import config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-60wzru63+3m$!=h$3&)7_0@7t8jlldufkm%0sk@kjb*==z8g@b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'oauth',
    "corsheaders",
    'jwt_utils',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'subscriptions',
    'contact'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smallbigleads.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smallbigleads.wsgi.application'

REST_FRAMEWORK = {
    # 'DEFAULT_AUTHENTICATION_CLASSES': [
    #     'rest_framework_simplejwt.authentication.JWTAuthentication',
    # ],
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.IsAuthenticated',
    # ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASE_NAME = config("DATABASE_NAME")
DATABASE_USER = config("DATABASE_USER")
DATABASE_PASSWORD = config("DATABASE_PASSWORD")
DATABASE_HOST = config("DATABASE_HOST")
DATABASE_PORT = config("DATABASE_PORT", default="5432")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'users.User'


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'BLACKLIST_AFTER_ROTATION': True,
}
# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "logtail": {
            "class": "logtail.LogtailHandler",
            "source_token": config("BETTERSTACK_LOGGER_KEY"),
            "level": "INFO"
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "": {
            "handlers": ["logtail", "console"],
            "level": "INFO",
            "propagate": True
        },
        "django": {
            "handlers": ["logtail", "console"],
            "level": "INFO",
            "propagate": False
        }
    }
}

EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST=config("EMAIL_HOST")
EMAIL_PORT=config("EMAIL_PORT")
EMAIL_USE_TLS=config("EMAIL_USE_TLS")
EMAIL_HOST_USER=config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD=config("EMAIL_HOST_PASSWORD")
FRONTEND_URL = 'http://localhost:3000'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

import os
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Yeh folder static files collect karega
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Optional: Agar aapne custom static files rakhe hain
]
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field\

# Better Contact API Settings
BETTER_CONTACT_API_KEY = config("BETTER_CONTACT_API_KEY")
HUNTER_API_KEY = config("HUNTER_API_KEY")
APOLLO_API_KEY = config("APOLLO_API_KEY")

DATAGMA_API_KEY = config("DATAGMA_API_KEY")
SNOV_API_KEY = "your_snov_api_key"
FINDTHATLEAD_API_KEY = "your_findthatlead_api_key"
SOCIETEINFO_API_KEY = "your_societeinfo_api_key"
PROSPEO_API_KEY = "your_prospeo_api_key"
CONTACTOUT_API_KEY = "your_contactout_api_key"
ICYPEAS_API_KEY = "your_icypeas_api_key"
ENROW_API_KEY = "your_enrow_api_key"
ANYMAILFINDER_API_KEY = "your_anymailfinder_api_key"
ROCKETREACH_API_KEY = "your_rocketreach_api_key"
PEOPLE_DATA_LABS_API_KEY = "your_people_data_labs_api_key"
ENRICHSO_API_KEY = "your_enrichso_api_key"
KENDO_API_KEY = "your_kendo_api_key"
NIMBLER_API_KEY = "your_nimbler_api_key"
TOMBA_API_KEY = "your_tomba_api_key"
TRUEINBOX_API_KEY = "your_trueinbox_api_key"
FORAGER_API_KEY = "your_forager_api_key"
USEBOUNCER_API_KEY = "your_usebouncer_api_key"
CLEON1_API_KEY = "your_cleon1_api_key"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
RAZORPAY_KEY_ID=config("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET=config("RAZORPAY_KEY_SECRET")

CORS_ALLOWED_ORIGINS = [
    "https://smallbigleadsfront2.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000"

]