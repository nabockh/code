from __future__ import absolute_import
import itertools
from bm.models import Benchmark
from datetime import datetime, timedelta
from celery import shared_task
from django.template.loader import get_template
from social.models import Contact
from django.template import loader, Context
from celery.schedules import crontab
from celery.task import periodic_task


INVITE_SUBJECT = 'You has been invited to benchmark'


def grouper(n, iterable, fillvalue=None):
    """grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"""
    args = [iter(iterable)] * n
    return itertools.izip_longest(*args, fillvalue=fillvalue)

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
            contacts = [invite.recipient for invite in invites_group if invite]
            Contact.send_mail(sender, subject, body, contacts)
        for invite in invites_to_send_via_linked:
            invite.status = 1
            invite.save()
        if len(invites_without_email) > 100:
            send_invites.apply_async(benchmark_id, countdown=86400)



@periodic_task(run_every=crontab(minute=0, hour=0))
def send_reminders():
    current_time = datetime.now()
    days_count = timedelta(days=2)
    approved_benchmarks = Benchmark.objects.filter(approved=True, end_date__gt=current_time, end_date__lte=current_time+days_count)
    # contacts = Contact.objects.filter(invites__benchmark__end_date__gt=current_time,
    #                                   invites__benchmark__end_date__lte=current_time+days_count,
    #                                   invites__benchmark__approved=True,
    #                                   invites__status=1,
    #                                   user__responses__question__benchmark__id=F('invites__benchmark__id'),
    query = '''
            SELECT
      "social_contact"."id",
      "social_contact"."code",
      "social_contact"."provider",
      "social_contact"."first_name",
      "social_contact"."last_name",
      "social_contact"."email",
      "social_contact"."headline",
      "social_contact"."location_id",
      "social_contact"."company_id",
      "social_contact"."user_id"
    FROM "social_contact"
      INNER JOIN  "bm_benchmarkinvitation" ON ( "social_contact"."id" = "bm_benchmarkinvitation"."recipient_id" )
      INNER JOIN  "bm_benchmark" ON ( "bm_benchmarkinvitation"."benchmark_id" = "bm_benchmark"."id" )
      INNER JOIN  "bm_question" ON ( "bm_benchmark"."id" = "bm_question"."benchmark_id" )
      LEFT JOIN   "auth_user" ON ( "social_contact"."user_id" = "auth_user"."id" )
      LEFT JOIN   "bm_questionresponse" ON ( "auth_user"."id" = "bm_questionresponse"."user_id" AND bm_questionresponse.question_id = bm_question.id )
    WHERE
      "bm_benchmark"."id" = %s
      AND "bm_benchmarkinvitation"."status" = '1'
      AND bm_questionresponse.id IS NULL
        '''
    for benchmark in approved_benchmarks:
        subject = "Reminder for {0}".format(benchmark.name)
        context = Context({'benchmark_name': benchmark.name,
                           'benchmark_link': benchmark.link,
                           })
        body = get_template('alerts/reminder_not_responded.html').render(context)
        contacts = Contact.objects.raw(query, [benchmark.id])
        Contact.send_mail(benchmark.owner, subject, body, contacts)

