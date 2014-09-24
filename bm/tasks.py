from __future__ import absolute_import
import itertools
from bm.models import Benchmark, BenchmarkInvitation, BmInviteEmail
from datetime import datetime, timedelta
from celery import shared_task
from core.utils import celery_log
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template.loader import get_template
from social.models import Contact
from django.template import loader, Context
from celery.schedules import crontab
from celery.task import periodic_task
from django.db.models import Count, Avg
from django.template import Template
from core.utils import get_context_variables

INVITE_SUBJECT = 'You have been invited to benchmark'


def grouper(n, iterable, fillvalue=None):
    """grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"""
    args = [iter(iterable)] * n
    return itertools.izip_longest(*args, fillvalue=fillvalue)


@shared_task
@celery_log
def send_invites(benchmark_id):
    benchmark = Benchmark.objects.get(pk=benchmark_id)
    if benchmark:
        invites = benchmark.invites.filter(status='0').select_related('recipient', 'recipient__user', 'sender')
        subject = INVITE_SUBJECT
        raw_context = get_context_variables(benchmark)
        context = Context(raw_context)
        if BmInviteEmail.objects.exists():
            email_invite = BmInviteEmail.objects.filter(benchmark_id=benchmark.id).first()
            raw_body = email_invite.body
            if '<LINK>' in raw_body:
                raw_body = raw_body.replace('<LINK>', '{{ benchmark.link }}')
            else:
                raw_body += ('\n'+'{{ benchmark.link }}')
            body = Template(raw_body).render(context)
        else:
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
        else:
            if BmInviteEmail.objects.filter(benchmark_id=benchmark.id).first():
                BmInviteEmail.objects.filter(benchmark_id=benchmark.id).first().delete()

@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
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
        contacts = Contact.objects.raw(query, [benchmark.id])
        for contact in contacts:
            raw_context = get_context_variables(benchmark)
            raw_context['reminder_contact'] = contact.first_name
            context = Context(raw_context)
            body = get_template('alerts/reminder_not_responded.html').render(context)
            Contact.send_mail(benchmark.owner, subject, body, [contact])


@periodic_task(bind=True, run_every=crontab(minute=1, hour=0), default_retry_delay=30*60)
@celery_log
def benchmark_aggregate(self):
    today = datetime.now()
    benchmarks = Benchmark.valid.annotate(series_cnt=Count('series_statistic')) \
                                .filter(Q(end_date=today, series_cnt=0) |
                                        Q(end_date__lt=today, series_cnt=0))
    for benchmark in benchmarks:
        try:
            benchmark.aggregate()
        except Exception as exc:
            self.retry(exc=exc, max_retries=10)


@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def check_benchmark_results():
    # get finished benchmarks with invites status 1 or 2
    finished_benchmarks = Benchmark.valid.filter(end_date__lte=datetime.now(), invites__status__range=[1, 2])
    if finished_benchmarks:
        for benchmark in finished_benchmarks:
            subject = "Benchmark results"
            contacts = Contact.objects.filter(invites__benchmark__id=benchmark.id)\
                .annotate(responses_count=Count('invites__benchmark__question__responses'))\
                .filter(responses_count__gte=1)
            contacts_ids = [contact.id for contact in contacts]
            recipients = [contact.email for contact in contacts]
            recipients.append(benchmark.owner.email)
            raw_context = get_context_variables(benchmark)
            if contacts_ids:
                for recipient in recipients:
                    raw_context['contact_first_name'] = Contact.objects.get(email=recipient).first_name
                    context = Context(raw_context)
                    body = get_template('alerts/benchmark_results.html').render(context)
                    send_mail(subject, body, None, [recipient])
                BenchmarkInvitation.objects.filter(recipient__id__in=contacts_ids).update(status=3)

@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def new_responses():
    """
    Task to check new responses to user Benchmarks on daily basis

    """
    pending = Benchmark.pending.all()
    template = loader.get_template('alerts/benchmark_answered.html')
    for benchmark in pending:
        today = datetime.date(datetime.now())
        yesterday = today - timedelta(days=1)
        contributors = benchmark.question.first().responses.\
            filter(date__range=(yesterday, today)).\
            values_list('user__first_name', 'user__last_name')
        contributors_names = ', '.join([(first_name + ' ' + last_name) for first_name, last_name in contributors])
        raw_context = get_context_variables(benchmark)
        raw_context['remaining_before_closure'] = benchmark.days_left
        raw_context['new_contributors'] = contributors_names
        context = Context(raw_context)
        if benchmark.owner and contributors_names:
            send_mail('Welcome', template.render(context), None, [benchmark.owner.email])