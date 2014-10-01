from __future__ import absolute_import
import traceback
from app import settings
from core.utils import celery_log

from celery import shared_task
from django.contrib.auth.models import User
from social import providers
from social.backend import linkedin
from social.models import Contact
from celery.schedules import crontab
from celery.task import periodic_task
# from celery.utils.log import get_task_logger
# logger = get_task_logger('celery')

import logging
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('django.request')


@shared_task
def import_linkedin_contacts(user):
    print 'first time login linkedin import started'
    contacts = linkedin.get_contacts(user)
    for contact_data in contacts:
        Contact.create(user, providers.LINKEDIN, **contact_data)


@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def periodic_import_linkedin_contacts():
    """
    periodic task for import of linked in
    contacts for all users with social profile.
    Execute on the first day of every month.
    """
    print 'periodic linkedin import started'
    auth_users = User.objects.all()
    for user in auth_users:
        if user.social_profile.first():
            contacts = linkedin.get_contacts(user)
            for contact_data in contacts:
                Contact.create(user, providers.LINKEDIN, **contact_data)