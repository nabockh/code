from django.dispatch import receiver, Signal
from social import tasks


first_time_user_login = Signal(providing_args=['user', ])


@receiver(first_time_user_login)
def linked_in_autoimport(sender, **kwargs):
    tasks.import_linkedin_contacts.delay(kwargs['user'])
