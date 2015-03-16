from __future__ import absolute_import
import traceback
from app import settings
from core.utils import celery_log

from celery import shared_task
from django.contrib.auth.models import User
from social import providers
from social.backend import linkedin
from social.models import Contact, ContactOwners
from celery.schedules import crontab
from celery.task import periodic_task
# from celery.utils.log import get_task_logger
# logger = get_task_logger('celery')

import logging
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('bedade.background')


@shared_task
def import_linkedin_contacts(user):
    print 'first time login linkedin import started'
    contacts = linkedin.get_contacts(user)
    for contact_data in contacts:
        Contact.create(user, providers.LINKEDIN, **contact_data)

@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def periodic_import_linkedin_contacts():
    print 'periodic linkedin import started'
    auth_user_ids = User.objects.values_list('id', flat=True)
    for user_id in auth_user_ids:
        periodic_import_linkedin_contacts_for_user.delay(user_id)
    clear_unused_contacts.delay()

@shared_task
@celery_log
def periodic_import_linkedin_contacts_for_user(user_id):
    """
    periodic task for import of linked in
    contacts for particular user with social profile.
    """
    user = User.objects.filter(id=user_id).first()
    if user and user.social_auth.first():
        logger.info('Importing contacts for %s' % user)
        contacts = linkedin.get_contacts(user)
        num_contacts = len(contacts)
        contacts = {c['id']: c for c in contacts if c['id'] != 'private'}
        contact_codes = set(contacts.keys())
        exists_contact_codes = set(ContactOwners.objects.filter(code__in=contact_codes, user=user)\
                                   .values_list('code', flat=True))
        contacts_diff = contact_codes - exists_contact_codes
        last_pct = 0
        logging.info(' - got %d contacts %d new of them for user "%s" to process' %
                     (num_contacts, len(contacts_diff), user.username))
        num_contacts = len(contacts_diff)
        for progress, contact_code in enumerate(contacts_diff):
            Contact.create(user, providers.LINKEDIN, already_checked=True, **contacts[contact_code])
            progress_pct = round((float(progress) / num_contacts) * 100)
            if progress_pct != last_pct and progress_pct % 20 == 0:
                logging.info('  -- processed %s%% of "%s" contacts' % (progress_pct, user.username))
                last_pct = progress_pct
        #clear old dependencies for e.g. if some contact changed his headline, for removing duplicates
        # Contact.objects.filter(codes__code__in=contact_codes, codes__user=user)
        ContactOwners.objects.filter(user=user).exclude(code__in=contact_codes).delete()


@shared_task
@celery_log
def clear_unused_contacts():
    Contact.objects.filter(codes__id__isnull=True, invites__id__isnull=True).delete()