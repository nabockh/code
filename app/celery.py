from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings
from django.db import connection

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery('app')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


if 'system_keys' in connection.introspection.table_names():
    from core.models import SystemKey
    smtp_keys = SystemKey.get_keys('SendGrid SMTP')
    settings.EMAIL_HOST_USER = smtp_keys['EMAIL_HOST_USER']
    settings.EMAIL_HOST_PASSWORD= smtp_keys['EMAIL_HOST_PASSWORD']


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
