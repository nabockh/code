from django.dispatch import receiver, Signal
from social import tasks
from social.models import Invite
from django.db.models.signals import post_save, pre_save
from django.core.mail import send_mail

first_time_user_login = Signal(providing_args=['user', ])
invitee_approved = Signal(providing_args=['queryset', ])

@receiver(first_time_user_login)
def linked_in_autoimport(sender, **kwargs):
    tasks.import_linkedin_contacts.delay(kwargs['user'])


@receiver(pre_save, sender=Invite)
def notify_invitee(instance, **kwargs):
    if instance.allowed:
        send_mail('Your invite was approved', 'message', None, [instance.email])


@receiver(invitee_approved)
def notify_multiple_invitee(**kwargs):
    invitees = kwargs['queryset']
    recipient_list = [invitee.email for invitee in invitees]
    send_mail('Your invite was approved', 'message', None, recipient_list)