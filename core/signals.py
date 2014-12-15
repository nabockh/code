from django.dispatch import Signal, receiver
from app.settings import MESSAGE_COLLEAGUE_INVITED
from django.contrib import messages

colleague_invited = Signal(providing_args=['user', ])


@receiver(colleague_invited)
def send_colleague_invited(sender, request, user, **kwargs):
    messages.add_message(request, MESSAGE_COLLEAGUE_INVITED, 'colleague was invited')