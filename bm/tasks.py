from __future__ import absolute_import
import itertools
from bm.models import Benchmark, BenchmarkInvitation, BmInviteEmail, QuestionResponse, Question
from datetime import datetime, timedelta
from bm.utils import StringAgg
from celery import shared_task
from core.utils import celery_log, logger, get_context_variables_by_id, mail_logger
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
    benchmark = Benchmark.objects.filter(id=benchmark_id).select_related('owner').first()
    if benchmark:
        invites = benchmark.invites.filter(status='0', recipient__codes__user=benchmark.owner)\
            .annotate(recipient_code=StringAgg('recipient__codes__code'))\
            .select_related('recipient', 'recipient__user', 'sender')
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
        sent = []
        for invite in invites:
            if invite.recipient.email:
                Contact.send_mail(invite.sender, subject, body, (invite.recipient,), benchmark)
                sent.append(invite.id)
            else:
                invites_without_email.append(invite)

        invites_to_send_via_linked = invites_without_email[:99]
        invites_groups = grouper(10, invites_to_send_via_linked)
        for invites_group in invites_groups:
            sender = invites_group[0].sender
            contacts = []
            for invite in invites_group:
                if invite:
                    contact = invite.recipient
                    contact.code = invite.recipient_code
                    contacts.append(contact)
            sent = sent + [invite.id for invite in invites_group if invite]
            Contact.send_mail(sender, subject, body, contacts, benchmark)
        benchmark.invites.filter(id__in=sent).update(status=1, sent_date=datetime.date(datetime.now()))
        if len(invites_without_email) > 100:
            send_invites.apply_async((benchmark_id,), countdown=86400)
        else:
            BmInviteEmail.objects.filter(benchmark_id=benchmark.id).delete()

@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def send_reminders():
    current_time = datetime.now()
    days_count = timedelta(days=2)
    approved_benchmarks = Benchmark.objects.filter(approved=True,
                                                   end_date__gt=current_time,
                                                   end_date__lte=current_time+days_count)\
                                            .select_related('owner', 'link')
    query = '''
    SELECT
      "social_contact"."id",
      "social_contact"."provider",
      "social_contact"."first_name",
      "social_contact"."last_name",
      "social_contact"."email",
      "social_contact"."headline",
      "social_contact"."location_id",
      "social_contact"."company_id",
      "social_contact"."user_id",
      "social_contact_owners".code
    FROM "social_contact"
      INNER JOIN  "social_contact_owners" ON social_contact.id = social_contact_owners.contact_id
      INNER JOIN  "bm_benchmarkinvitation" ON ( "social_contact"."id" = "bm_benchmarkinvitation"."recipient_id" )
      INNER JOIN  "bm_benchmark" ON ( "bm_benchmarkinvitation"."benchmark_id" = "bm_benchmark"."id" )
      INNER JOIN  "bm_question" ON ( "bm_benchmark"."id" = "bm_question"."benchmark_id" )
      LEFT JOIN   "auth_user" ON ( "social_contact"."user_id" = "auth_user"."id" )
      LEFT JOIN   "bm_questionresponse" ON ( "auth_user"."id" = "bm_questionresponse"."user_id" AND bm_questionresponse.question_id = bm_question.id )
    WHERE
      "bm_benchmark"."id" = %s
      AND "bm_benchmark".owner_id = "social_contact_owners".user_id
      AND "bm_benchmarkinvitation"."status" = '1'
      AND bm_questionresponse.id IS NULL
        '''
    for benchmark in approved_benchmarks:
        subject = "Bedade benchmark response reminder"
        contacts = list(Contact.objects.raw(query, [benchmark.id]))
        sent = []
        contacts_without_email = []
        count_contacts_without_email = 0
        total_contacts = len(contacts)
        raw_context = get_context_variables(benchmark)
        raw_context['remaining_before_closure'] = benchmark.days_left
        for i, contact in enumerate(contacts, start=1):
            raw_context['reminder_contact'] = contact.first_name
            context = Context(raw_context)
            body = get_template('alerts/reminder_not_responded.html').render(context)
            if benchmark.owner:
                if contact.email:
                    Contact.send_mail(benchmark.owner, subject, body, [contact], benchmark)
                    sent.append(contact.id)
                else:
                    contacts_without_email.append(contact)
                    if len(contacts_without_email) == 10 or i == total_contacts:
                        count_contacts_without_email += len(contacts_without_email)
                        if count_contacts_without_email <= 100:
                            try:
                                Contact.send_mail(benchmark.owner, subject, body, contacts_without_email, benchmark)
                                sent = sent + [c.id for c in contacts_without_email]
                                contacts_without_email = []
                            except:
                                logger.exception('')
            else:
                logger.warning("Cannot send reminder. Benchmark owner or Contact email does not exist")
        BenchmarkInvitation.objects.filter(benchmark_id=benchmark.id, recipient__id__in=sent)\
            .update(status=2, sent_date=datetime.date(datetime.now()))



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
    benchmarks = Benchmark.objects.annotate(responses_count=Count('question__responses', distinct=True),
                                            invites_count=Count('invites', distinct=True))\
        .filter(end_date__lte=today,
                responses_count__lt=F('min_numbers_of_responses'),
                invites_count__gt=0,
                approved=True).exclude(invites__status=4)
    if benchmarks.exists():
        benchmark_names = ', '.join([benchmark.name for benchmark in benchmarks])
        recipient_list = [email for email in User.objects.filter(is_superuser=True).values_list('email', flat=True) if email]
        benchmark_ids = [benchmark.id for benchmark in benchmarks]
        if recipient_list:
            send_mail('Uncomplete Benchmark', 'Hi! Current benchmarks has not reached min_number_of_responses: %s' %
                      benchmark_names, None, recipient_list)
        BenchmarkInvitation.objects.filter(benchmark__id__in=benchmark_ids)\
            .update(status=4, sent_date=datetime.date(datetime.now()))


@periodic_task(run_every=crontab(minute=0, hour=0))
@celery_log
def check_benchmark_results():
    # get all invites needed to be notify
    sql = '''
    WITH finished_benchmarks AS (
        SELECT bm_benchmark.id FROM bm_benchmark
          JOIN bm_question ON bm_benchmark.id = bm_question.benchmark_id
          JOIN bm_questionresponse ON bm_question.id = bm_questionresponse.question_id
        WHERE
          bm_benchmark.end_date <= %s AND bm_benchmark.approved = TRUE
        GROUP BY bm_benchmark.id
        HAVING COUNT(DISTINCT bm_questionresponse.id) >= bm_benchmark.min_numbers_of_responses
    )
    SELECT
      bm_benchmarkinvitation.*,
      social_contact.first_name as contact_first_name,
      social_contact.last_name as contact_last_name,
      social_contact.email as contact_email
    FROM bm_benchmarkinvitation
      JOIN social_contact ON social_contact.id = bm_benchmarkinvitation.recipient_id
      JOIN bm_benchmark ON bm_benchmark.id = bm_benchmarkinvitation.benchmark_id
      JOIN bm_question ON bm_benchmark.id = bm_question.benchmark_id
      JOIN bm_questionresponse ON bm_question.id = bm_questionresponse.question_id
                                  AND social_contact.user_id = bm_questionresponse.user_id
    WHERE
      bm_benchmarkinvitation.status::INT8 < 3
      AND bm_benchmark.id IN (SELECT id FROM finished_benchmarks);
    '''
    invites = BenchmarkInvitation.objects.raw(sql, (datetime.date(datetime.now()),))
    successfully_send = []
    for invite in invites:
        subject = "Bedade results published"
        raw_context = get_context_variables_by_id(invite.benchmark_id, Question)
        raw_context['contact_first_name'] = invite.contact_first_name
        context = Context(raw_context)
        body = get_template('alerts/benchmark_results.html').render(context)
        if send_mail(subject, body, None, [invite.contact_email,]):
            successfully_send.append(invite.id)
            recipient_name = '%s %s<%s>' % (invite.contact_first_name, invite.contact_last_name, invite.contact_email)
            mail_logger.info('[%s] To: %s; BM: %s' % (subject, recipient_name, invite.benchmark_id))
    BenchmarkInvitation.objects.filter(id__in=successfully_send)\
        .update(status=3, sent_date=datetime.date(datetime.now()))


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