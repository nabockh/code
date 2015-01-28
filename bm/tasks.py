from __future__ import absolute_import
import itertools
from bm.models import Benchmark, BenchmarkInvitation, BmInviteEmail, QuestionResponse
from datetime import datetime, timedelta
from celery import shared_task
from core.utils import celery_log, logger
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q, F
from django.template.loader import get_template
from social.models import Contact
from django.template import loader, Context
from celery.schedules import crontab
from celery.task import periodic_task
from django.db.models import Count, Avg
from django.template import Template
from core.utils import get_context_variables
from django.contrib.auth.models import User

INVITE_SUBJECT = 'You have been invited to a benchmark'


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
        raw_context['remaining_before_closure'] = benchmark.days_left
        if Site.objects.all().exists():
            raw_context['site_link'] = Site.objects.all().first()
        context = Context(raw_context)
        bm_email_query = BmInviteEmail.objects.filter(benchmark_id=benchmark_id)
        if bm_email_query.exists():
            email_invite = bm_email_query.first()
            raw_body = email_invite.body
            if 'Link to answer form will be here' in raw_body:
                raw_body = raw_body.replace('Link to answer form will be here', '{{ benchmark.link }}')
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
            send_invites.apply_async((benchmark_id,), countdown=86400)
        else:
            if BmInviteEmail.objects.filter(benchmark_id=benchmark.id).first():
                BmInviteEmail.objects.filter(benchmark_id=benchmark.id).first().delete()

@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def send_reminders():
    current_time = datetime.now()
    days_count = timedelta(days=2)
    approved_benchmarks = Benchmark.objects.filter(approved=True, end_date__gt=current_time, end_date__lte=current_time+days_count)
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
        subject = "Bedade benchmark response reminder"
        contacts = Contact.objects.raw(query, [benchmark.id])
        for contact in contacts:
            raw_context = get_context_variables(benchmark)
            raw_context['reminder_contact'] = contact.first_name
            raw_context['remaining_before_closure'] = benchmark.days_left
            context = Context(raw_context)
            body = get_template('alerts/reminder_not_responded.html').render(context)
            if benchmark.owner:
                Contact.send_mail(benchmark.owner, subject, body, [contact])
                BenchmarkInvitation.objects.filter(benchmark_id=benchmark.id, recipient__id=contact.id).update(status=2)
            elif contact.email:
                send_mail(subject, body, None, [contact.email])
                BenchmarkInvitation.objects.filter(benchmark_id=benchmark.id, recipient__id=contact.id).update(status=2)
            else:
                logger.warning("Cannot send reminder. Benchmark owner or Contact email does not exist")



@periodic_task(bind=True, run_every=crontab(minute=1, hour=0), default_retry_delay=30*60)
@celery_log
def benchmark_aggregate(self):
    today = datetime.now()
    benchmarks = Benchmark.valid.annotate(series_cnt=Count('series_statistic')) \
                                .filter(end_date__lte=today, series_cnt=0)
    for benchmark in benchmarks:
        try:
            benchmark.aggregate()
        except Exception as exc:
            self.retry(exc=exc, max_retries=10)


@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def check_response_count():
    today = datetime.now()
    benchmarks = Benchmark.objects.annotate(responses_count=Count('question__responses', distinct=True))\
        .filter(end_date__lte=today, responses_count__lt=F('min_numbers_of_responses'), approved=True).exclude(invites__status=4)
    if benchmarks.exists():
        benchmark_names = ', '.join([benchmark.name for benchmark in benchmarks])
        recipient_list = [email for email in User.objects.filter(is_superuser=True).values_list('email', flat=True) if email]
        benchmark_ids = [benchmark.id for benchmark in benchmarks]
        if recipient_list:
            send_mail('Uncomplete Benchmark', 'Hi! Current benchmarks has not reached min_number_of_responses: %s' %
                      benchmark_names, None, recipient_list)
        BenchmarkInvitation.objects.filter(benchmark__id__in=benchmark_ids).update(status=4)


@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def check_benchmark_results():
    # get finished benchmarks with invites status 1 or 2
    finished_benchmarks = Benchmark.valid.filter(end_date__lte=datetime.now(), invites__status__range=[0, 2])
    if finished_benchmarks:
        for benchmark in finished_benchmarks:
            subject = "Bedade results published"
            contacts = []
            filtered_contacts = Contact.objects.filter(invites__benchmark__id=benchmark.id)
            responded__users = [response.user_id for response in
                                QuestionResponse.objects.filter(question_id=benchmark.question.first().id)]
            for contact in filtered_contacts:
                if contact.user and contact.user_id in responded__users:
                    contacts.append(contact)
            contacts_ids = [contact.id for contact in contacts]
            recipients = [contact.email for contact in contacts]
            if benchmark.owner:
                recipients.append(benchmark.owner.email)
            raw_context = get_context_variables(benchmark)
            successfully_send = []
            if contacts_ids:
                for recipient in recipients:
                    contact = Contact.objects.filter(_email=recipient).first()
                    if not contact:
                        logger.warning("Cannot send notification. Contact with email '%s' does not exist" %
                                       recipient)
                        continue
                    raw_context['contact_first_name'] = contact.first_name
                    context = Context(raw_context)
                    body = get_template('alerts/benchmark_results.html').render(context)
                    if send_mail(subject, body, None, [recipient, ]):
                        successfully_send.append(contact.id)
                BenchmarkInvitation.objects.filter(recipient__id__in=successfully_send).update(status=3)


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
        if contributors.exists():
            contributors_names = str(', '.join([(first_name + ' ' + last_name) for first_name, last_name in contributors]))
            context = Context({
                'benchmark_name': benchmark.name,
                'query_details': benchmark.question.first().description,
                'link_to_answer': benchmark.link,
                'new_contributors': contributors_names,
                'benchmark_creator': benchmark.owner.get_full_name(),
                'remaining_before_closure': benchmark.days_left
            })
            if benchmark.owner.email:
                send_mail('New Contributors', template.render(context), None, [benchmark.owner.email])