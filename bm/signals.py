from django.core.mail import send_mail
from django.dispatch import Signal
from django.dispatch import receiver
from django.template import loader, Context
from bm.models import QuestionResponse

benchmark_answered = Signal(providing_args=['user',])


@receiver(benchmark_answered)
def send_welcome_alert(sender, **kwargs):
    if not QuestionResponse.objects.filter(user=kwargs['user']).count() > 1:
        user = kwargs['user']
        user_email = user.email
        recipient_list = [user_email]
        template = loader.get_template('alerts/welcome_alert_email.txt')
        context = Context({
            'user_name': user.username,
        })
        send_mail('Welcome', template.render(context), None, recipient_list)



