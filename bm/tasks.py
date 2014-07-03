from __future__ import absolute_import
import itertools
from bm.models import Benchmark

from celery import shared_task
from django.template import Context
from django.template.loader import get_template
from social.models import Contact


INVITE_SUBJECT = 'You has been invited to benchmark'


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

@shared_task
def send_invites(benchmark_id):
    benchmark = Benchmark.objects.get(pk=benchmark_id)
    if benchmark:
        invites = benchmark.invites.filter(status='0').select_related('recipient', 'recipient__user', 'sender')
        subject = INVITE_SUBJECT
        context = Context({'benchmark': benchmark})
        body = get_template('alerts/invite.html').render(context)

        invites_without_email = []
        for invite in invites:
            if invite.recipient.email:
                Contact.send_mail(invite.sender, subject, body, (invite.recipient,))
                invite.status = 1
                invite.save()
            else:
                invites_without_email.append(invite)

        invites_to_send_via_linked = invites_without_email[:99]
        invites_groups = grouper(10, invites_to_send_via_linked)
        for invites_group in invites_groups:
            sender = invites_group[0].sender
            contacts = [invite.recipient for invite in invites_group]
            Contact.send_mail(sender, subject, body, contacts)
        for invite in invites_to_send_via_linked:
            invite.status = 1
            invite.save()
        if len(invites_without_email) > 100:
            send_invites.apply_async(benchmark_id, countdown=86400)

    print benchmark_id