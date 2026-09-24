import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-e54je2=18dsu3prnz6#0c@n#d=95qmsh8%e^36y99mtc*=aj@o'

# SECURITY WARNING: don't run with debug turned on in production!


## Firebase key --
FCM_SERVER_KEY = '1:136688303447:android:2a6ac7e9441dc22920d212'



DEBUG = True

## for app ---
#DEBUG = False
ALLOWED_HOSTS = ["*",'127.0.0.1:8000']



## - start - this for app
APPEND_SLASH = False

## -end - approval app


# ALLOWED_HOSTS = ['demo.incomitbd.com','www.demo.incomitbd.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'properties',
    'documents',
    'projects',
    'crm',
    'products',
    'accounting',
    'purchase',
    'hrm',
    'inventories',
    'sales',
    'rest_framework',
    'corsheaders',
    'erp_api',
    'restaurant',
    'restahrm',
    'restaccounting',
    'tenant',
    'tasks',
    'tracker',
    'office_inventory',
    'whatsapp',
    'pos',
    'menu_app',
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/' 

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'real_estate_erp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
             BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'menu_app.context_processors.sidebar_menu',
            ],
        },
    },
]

WSGI_APPLICATION = 'real_estate_erp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


CORS_ALLOW_ALL_ORIGINS = True 
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
# }

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'URL_FIELD_NAME': 'url',
    'EXCEPTION_HANDLER': 'erp_api.exceptions.custom_exception_handler',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'incomitbd2_bricks',
#         'USER': 'incomitbd2_bricks',
#         'PASSWORD': 'k8^e1n,vQkiq)xq!',
#         'HOST': 'localhost',
#         'PORT': '3306',
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }


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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


APPEND_SLASH = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# Directory to collect static files
#STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Directories where static files are stored within the project
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_ROOT = '/home/incomitbd2/demo.incomitbd.com/media'
STATIC_ROOT = '/home/incomitbd2/demo.incomitbd.com/static'


#MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # "media" folder in your project root
MEDIA_URL = '/media/'  # URL for accessing media files

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
