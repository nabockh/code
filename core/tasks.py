from app import settings
from core.models import SystemKey
from djcelery_email.backends import CeleryEmailBackend
from django.conf import settings
from django.core.mail import get_connection

from celery.task import task

CONFIG = getattr(settings, 'CELERY_EMAIL_TASK_CONFIG', {})
BACKEND = getattr(settings, 'CELERY_EMAIL_BACKEND',
                  'django.core.mail.backends.smtp.EmailBackend')
TASK_CONFIG = {
    'name': 'bedade_email_send',
    'ignore_result': True,
}
TASK_CONFIG.update(CONFIG)


@task(**TASK_CONFIG)
def send_email(message, **kwargs):
    logger = send_email.get_logger()
    smtp_keys = SystemKey.get_keys('SendGrid SMTP')
    settings.EMAIL_HOST_USER = str(smtp_keys['EMAIL_HOST_USER'])
    settings.EMAIL_HOST_PASSWORD = str(smtp_keys['EMAIL_HOST_PASSWORD'])

    conn = get_connection(backend=BACKEND,
                          **kwargs.pop('_backend_init_kwargs', {}))
    try:
        result = conn.send_messages([message])
        logger.debug("Successfully sent email message to %r.", message.to)
        return result
    except Exception as e:
        # catching all exceptions b/c it could be any number of things
        # depending on the backend
        logger.warning("Failed to send email message to %r, retrying.",
                       message.to)
        send_email.retry(exc=e)


class BedadeCeleryEmailBackend(CeleryEmailBackend):
    def send_messages(self, email_messages, **kwargs):
        results = []
        kwargs['_backend_init_kwargs'] = self.init_kwargs
        for msg in email_messages:
            results.append(send_email.delay(msg, **kwargs))
        return results
