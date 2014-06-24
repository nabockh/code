from __future__ import absolute_import

from celery import shared_task

from social import providers
from social.backend import linkedin
from social.models import Contact


@shared_task
def import_linkedin_contacts(user):
    print 'linkedin import started'
    contacts = linkedin.get_contacts(user)
    for contact_data in contacts:
        Contact.create(user, providers.LINKEDIN, **contact_data)
