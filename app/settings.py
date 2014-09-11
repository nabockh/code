"""
Django settings for bedade project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from __future__ import absolute_import
# ^^^ The above is required if you want to import from the celery
# library.  If you don't have this then `from celery.schedules import`
# becomes `proj.celery.schedules` in Python 2.x since it allows
# for relative imports by default.

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rq&+0u=wxl0qr-@a3rp3iwhh^k8pxknq$=ar&j8(a34jr5#cf='


# Celery settings

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

METRICS = True

ALLOWED_HOSTS = ['*']

SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    'cms',  # django CMS itself
    'mptt',  # utilities for implementing a modified pre-order traversal tree
    'menus',  # helper for model independent hierarchical website navigation
    'south',  # intelligent schema and data migrations
    'sekizai',  # for javascript and css management
    'dbtemplates',
    'core',
    'djangocms_admin_style',
    'djangocms_text_ckeditor',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'bootstrapform',
    'djcelery_email',
    'social',
    'social_auth',
    'metrics',
    'bm',
    'formadmin',
    'bootstrap3',
)

INSTALLED_APPS += ('django_jenkins',)
JENKINS_TASKS = ('django_jenkins.tasks.run_pylint',
                 'django_jenkins.tasks.run_pep8',
                 'django_jenkins.tasks.run_pyflakes',
                 'django_jenkins.tasks.with_coverage',)

TEMPLATE_LOADERS = (

    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'dbtemplates.loader.Loader',
    'core.utils.ReserveLoader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'social_auth.middleware.SocialAuthExceptionMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'cms.context_processors.cms_settings',
    'sekizai.context_processors.sekizai',
    'core.context_prepocessos.contact_form',
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
MESSAGE_FIRST_ANSWER = 50
MESSAGE_LOGOUT = 51
MESSAGE_BETA = 52
MESSAGE_BETA_INVITE = 53
MESSAGE_TAGS = {
    MESSAGE_FIRST_ANSWER: 'first_answer',
    MESSAGE_LOGOUT: 'logout',
    MESSAGE_BETA: 'beta',
    MESSAGE_BETA_INVITE: 'beta_invite',
}

ROOT_URLCONF = 'app.urls'

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'bedade',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
]

TIME_ZONE = 'Europe/Kiev'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR,  'templates'),
)

ADMINS = (
    # ('Volodymyr', 'volodymyr.trotsyshyn@perfectial.com'),
    ('Volodymyr', 'devova@gmail.com'),
    #('Petro', 'petro.zdeb@perfectial.com'),
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s',
            'datefmt': '%y %b %d, %H:%M:%S',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/web_worker.log',
            # 'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            # 'formatter': 'simple'
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/celery.log',
            # 'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'bedade.background': {
            'handlers': ['celery', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

CMS_TEMPLATES = (
    ('base.html', 'Base'),
    ('layout/dashboard_two_column_5_7.html', 'Two Columns 5-7 (Dashboard)'),
    ('layout/two_column_5_7.html', 'Two Columns 5-7'),
    ('layout/two_column_7_5.html', 'Two Columns 7-5'),
    ('layout/three_column_4_4_4.html', 'Three Columns 4-4-4'),
)

CMS_PLACEHOLDER_CONF = {
    'Page Content': {
        'plugins': ['BootstrapContainerPlugin'],
    },
}

CMS_CASCADE_PLUGINS = ('bootstrap3',)

CMS_TOOLBARS = [
    # CMS Toolbars
    'cms.cms_toolbar.PlaceholderToolbar',
    'cms.cms_toolbar.BasicToolbar',
    'cms.cms_toolbar.PageToolbar',

    # 3rd Party Toolbar
    'core.cms_toolbar.PopupsToolbar',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

AUTHENTICATION_BACKENDS = (
#    'social.backend.beta.BetaBackend',
    'social_auth.backends.contrib.linkedin.LinkedinBackend',
    'app.backend.case_insensitive.CaseInsensitiveModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.beta_login',
    'social.pipeline.contacts_validation',
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details',
    'social.pipeline.load_extra_data',
)

#LINKEDIN_CONSUMER_KEY = '77ib04b5abd803'
#LINKEDIN_CONSUMER_SECRET = '2HuRj68wed7IPndy'
LINKEDIN_CONSUMER_KEY = '77pi0tgejrq7si'
LINKEDIN_CONSUMER_SECRET = 'ZneKr9tbVPSSrm5O'

LINKEDIN_SCOPE = ['r_basicprofile', 'r_emailaddress', 'r_network', 'w_messages']
LINKEDIN_EXTRA_FIELD_SELECTORS = ['email-address', 'headline', 'industry', 'location:(country)', 'positions']
LINKEDIN_OAUTH2_EXTRA_DATA = [('id', 'id'), ]

LOGIN_REDIRECT_URL = "/"
LOGIN_ERROR_URL = "/beta"
LOGIN_URL = '/'
LOGIN_REAL_URL = '/login/linkedin'

EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', 'devova')
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', 'bedadesmtp')
DEFAULT_FROM_EMAIL = 'Bedade <info@bedade.com>'

SOCIAL_AUTH_COMPLETE_URL_NAME = 'social_complete'
FIRST_TIME_USER_REDIRECT_URL = '/dashboard'
REGISTERED_USER_REDIRECT_URL = '/dashboard'

CSRF_FAILURE_VIEW = 'core.views.csrf_failure'

try:
    from local_settings import *
except ImportError:
    pass


BENCHMARK_DURATIONS_DAYS = 3
