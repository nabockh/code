from app.settings import MESSAGE_FIRST_ANSWER
from bm.admin import BenchmarkPending
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal
from django.dispatch import receiver
from django.template import loader, Context
from bm.models import QuestionResponse, Benchmark
from bm.tasks import send_invites

benchmark_answered = Signal(providing_args=['user',])


@receiver(benchmark_answered)
def send_welcome_alert(sender, request, user, **kwargs):
    if not QuestionResponse.objects.filter(user=user).count() > 1:
        messages.add_message(request, MESSAGE_FIRST_ANSWER, 'Hello')
        user_email = user.email
        recipient_list = [user_email]
        template = loader.get_template('alerts/welcome_alert_email.txt')
        context = Context({
            'user_name': user.username,
        })
        send_mail('Welcome', template.render(context), None, recipient_list)


@receiver(pre_save, sender=BenchmarkPending)
def calculate_deadline(instance, **kwargs):
    if hasattr(instance, 'already_approved'):
        if not instance.already_approved and instance.approved:
            instance.calculate_deadline()


@receiver(post_save, sender=BenchmarkPending)
def check_for_approve(instance, **kwargs):
    if not instance.already_approved and bool(instance.approved):
        instance.already_approved = True
        send_invites.delay(instance.id)


@receiver(pre_save, sender=Benchmark, dispatch_uid='nope')
def check_new_bm_created(instance, **kwargs):
    """
    send alert to all Superusers users
    """
    if instance.pk is None:
        owner = instance.owner
        recipient_list = User.objects.filter(is_superuser=True).values_list('email', flat=True)
        template = loader.get_template('alerts/new_benchmark.html')
        context = Context({
            'owner_name': owner.first_name + ' ' + owner.last_name,
            'benchmark': instance.name,
        })
        send_mail('New Benchmark has been created', template.render(context), None, recipient_list)