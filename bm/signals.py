from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import Signal
from django.dispatch import receiver
from django.template import loader, Context
from bm.models import QuestionResponse, Benchmark
from bm.tasks import send_invites

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


@receiver(post_save, sender=Benchmark)
def check_for_approve(instance, **kwargs):
    if not instance.already_approved and instance.approved:
        instance.already_approved = True
        send_invites(instance.id)