from django.dispatch import receiver, Signal
from social import tasks
from social.models import Invite
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.template import loader, Context
from django.contrib.sites.models import Site

first_time_user_login = Signal(providing_args=['user', ])
invitee_approved = Signal(providing_args=['approved_invites', ])

@receiver(first_time_user_login)
def linked_in_autoimport(sender, **kwargs):
    tasks.import_linkedin_contacts.delay(kwargs['user'])


@receiver(post_save, sender=Invite)
def notify_invitee(instance, **kwargs):
    if instance.allowed and kwargs['update_fields']:
        template = loader.get_template('alerts/beta_notification.html')
        context = Context({
            'email': instance.email,
            'site_link': Site.objects.get_current()
        })
        send_mail('Your invite was approved', template.render(context), None, [instance.email])
    elif kwargs.get('created', None):
        template = loader.get_template('alerts/beta_email_submitted.html')
        context = Context({
            'email': instance.email,
            'site_link': Site.objects.get_current()
        })
        send_mail('Your invite was submitted', template.render(context), None, [instance.email])
