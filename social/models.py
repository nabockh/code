from app import settings
from django.core.cache import get_cache
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Count
from linkedin import linkedin
from social.backend.linkedin import extract_access_tokens, LinkedInApplication
from social_auth.db.django_models import USER_MODEL
import random
import logging
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('mail.messages')


class LinkedInIndustry(models.Model):
    code = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __init__(self, code, name):
        super(LinkedInIndustry, self).__init__()
        self.code = code
        self.name = name

    @classmethod
    def get(cls, name='', code=None):
        if isinstance(name, cls):
            return name
        cache = get_cache('default')
        data = cache.get(cls.__name__)
        if not data:
            data = dict(LinkedInIndustry.objects.all().values_list('name', 'code'))
            cache.set(cls.__name__, data)
        return LinkedInIndustry(data.get(name), name) if not code else LinkedInIndustry(code, name)

    @classmethod
    def get_proposal(cls, contacts):
        result = cls.objects\
            .annotate(users_count=Count('companies__employees'))\
            .filter(companies__employees__in=contacts.values_list('id', flat=True))\
            .values_list('code', 'name', 'users_count')\
            .distinct().order_by('-users_count')
        return [(a, b) for a, b, _ in result]

    def __unicode__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    _industry = models.ForeignKey(LinkedInIndustry, db_column="industry_id", blank=True, null=True, db_constraint=False,
                                  on_delete=models.SET_NULL, related_name='companies')
    code = models.PositiveIntegerField(null=True, blank=True)

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, value):
        self._industry = LinkedInIndustry.get(code=value) if str(value).isdigit() else LinkedInIndustry.get(value)

    def __unicode__(self):
        return self.name


class Profile(models.Model):
    user = models.ForeignKey(USER_MODEL, related_name='social_profile', on_delete=models.CASCADE)
    headline = models.CharField(max_length=200, blank=True, null=True)
    company = models.ForeignKey(Company, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    location = models.ForeignKey('bm.Region', blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)


class Contact(models.Model):
    owners = models.ManyToManyField(USER_MODEL, related_name='contacts', through='ContactOwners')
    provider = models.PositiveSmallIntegerField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    _email = models.EmailField(blank=True, null=True, db_column="email")
    headline = models.CharField(max_length=200, blank=True, null=True)
    location = models.ForeignKey('bm.Region', blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL,
                                 related_name='contacts')
    company = models.ForeignKey(Company, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL,
                                related_name='employees')
    user = models.ForeignKey(USER_MODEL, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    _code = None

    @property
    def code(self):
        if self._code is None:
            self._code = self.codes.filter(user_id=self.owner_id).first()\
                if hasattr(self, 'owner_id') else str(self.codes.first())
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    @property
    def email(self):
        return self._email if self._email else self.user and self.user.email

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __unicode__(self):
        return self.full_name

    @classmethod
    def send_mail(cls, user_from, subject, body, contacts, benchmark=None):
        if not list(contacts):
            return
        assert isinstance(contacts[0], cls), 'Contacts should be social.Contact instances'
        recipients_without_email = []
        recipients_names_without_email = []
        for contact in contacts:
            if contact.email:
                send_mail(subject, body, user_from.email, recipient_list=[contact.email])
                logger.info('[%s] To: %s; BM: %s' % (subject, '%s<%s>' % (contact.full_name, contact.email),
                                                     benchmark and benchmark.id))
            else:
                recipients_without_email.append(contact.code)
                recipients_names_without_email.append(contact.full_name)
        if len(recipients_without_email):
            auth = user_from.social_auth.first()
            user_access = extract_access_tokens(auth.tokens)
            authentication = linkedin.LinkedInDeveloperAuthentication(
                settings.LINKEDIN_CONSUMER_KEY,
                settings.LINKEDIN_CONSUMER_SECRET,
                user_access.token,
                user_access.token_secret,
                ''
            )
            application = LinkedInApplication(authentication)
            application.send_message(subject, body, recipients_without_email)
            recipients = ('%s<%s>' % i for i in zip(recipients_names_without_email, recipients_without_email))
            logger.info('[%s] To: %s; BM: %s' % (subject, ', '.join(recipients), benchmark and benchmark.id))

    @classmethod
    def create(cls, owner, provider, already_checked=False, **kwargs):
        from bm.models import Region
        if kwargs['id'] == 'private':
            print "Contacts have explicitly set their information to private"
            return

        #check if contact already exists
        contact_code = None if already_checked else \
            ContactOwners.objects.filter(user=owner, code=kwargs['id'], contact__provider=provider)\
                .select_related('contact').first()
        if contact_code is None:
            contact_code = ContactOwners.objects.filter(user=owner,
                                                        contact__first_name=kwargs['firstName'],
                                                        contact__last_name=kwargs['lastName'],
                                                        contact__headline=kwargs.get('headline'),
                                                        contact__provider=provider).select_related('contact').first()
            if contact_code:
                if (not already_checked and contact_code.code != kwargs['id']) or already_checked:
                    contact_code.code = kwargs['id']
                    contact_code.save()
                return contact_code.contact
            else:
                ###Try to find this contact for other owners
                other_contact_code = ContactOwners.objects.filter(code=kwargs['id'], contact__provider=provider)\
                    .select_related('contact').first()
                if other_contact_code is None:
                    other_contact_code = ContactOwners.objects.filter(
                                                        contact__first_name=kwargs['firstName'],
                                                        contact__last_name=kwargs['lastName'],
                                                        contact__headline=kwargs.get('headline'),
                                                        contact__provider=provider).select_related('contact').first()
                if other_contact_code:
                    contact_code = ContactOwners()
                    contact_code.code = kwargs['id']
                    contact_code.user = owner
                    contact_code.contact = other_contact_code.contact
                    contact_code.save()
                    return contact_code.contact
        else:
            return contact_code.contact
        contact = cls()
        with transaction.atomic():
            try:
                if kwargs.get('positions').get('values'):
                    for position in kwargs.get('positions').get('values'):
                        if position.get('isCurrent'):
                            company = None
                            company_id = position.get('company', {}).get('id')
                            if company_id:
                                company = Company.objects.filter(code=company_id, _industry__name=kwargs.get('industry', {})).first()
                            if not company:
                                company = Company.objects.filter(name=position.get('company', {}).get('name'), _industry__name=kwargs.get('industry', {})).first()
                                if company and company_id and company.code != company_id:
                                    company.code = company_id
                                    company.save()
                            if company:
                                if company.industry.name != kwargs.get('industry', {}):
                                    company.industry = LinkedInIndustry.objects.filter(name=kwargs.get('industry', {})).first();
                                    company.save()
                                contact.company = company
                            else:
                                company = Company()
                                if position.get('company', {}).get('id'):
                                    company.code = position.get('company', {}).get('id')
                                else:
                                    while True:
                                        rand_code = random.randint(100000, 2147483647)
                                        if not Company.objects.filter(code=rand_code).exists():
                                            break
                                    company.code = rand_code
                                company.name = position.get('company', {}).get('name')
                                company.industry = LinkedInIndustry.objects.filter(name=kwargs.get('industry', {})).first()
                                company.save()
                                contact.company = company
                            break
            except AttributeError:
                print "Contacts have explicitly set their information to private %s" % kwargs['id']
                return
            location = Region.objects.filter(code=kwargs.get('location', {}).get('country', {}).get('code')).first()
            if not location:
                print "Don't have Contact location"
                return
                # location = Region()
                # location.code = kwargs.get('location', {}).get('country', {}).get('code')
                # location.save()
            contact.location = location
            contact.provider = provider
            contact.first_name = kwargs['firstName']
            contact.last_name = kwargs['lastName']
            if kwargs.get('email'):
                contact.email = kwargs.get('email')
            contact.headline = kwargs.get('headline')
            contact.save()
            co = ContactOwners.objects.create(contact=contact, user=owner, code=kwargs['id'])
            co.save()
        return contact

    @classmethod
    def get_suggested(cls, geo=None, industry=None, user=None, exclude_ids=[]):
        contact_filter = {}
        if industry:
            contact_filter['company___industry__code__in'] = industry
        if geo:
            contact_filter['location__parent__id'] = geo

        return cls.objects.exclude(models.Q(id__in=exclude_ids)) \
                          .filter(owners=user, **contact_filter) \
                          .annotate(num_responses=models.Count('user__responses'),
                                    is_active_user=models.Count('user__id')) \
                          .order_by('-is_active_user',
                                    'num_responses',
                                    'company___industry',
                                    'headline')\
                          .select_related('user', 'company', 'company___industry', 'location')[:10]


class ContactOwners(models.Model):
    class Meta:
        db_table = 'social_contact_owners'
    contact = models.ForeignKey(Contact, related_name='codes')
    user = models.ForeignKey(USER_MODEL, related_name='contact_codes')
    code = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.code


class Invite(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    allowed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.email

    def save(self, *args, **kw):
        if self.pk is not None:
            orig = Invite.objects.get(pk=self.pk)
            if orig.allowed != self.allowed:
                kw['update_fields'] = ('allowed',)
        super(Invite, self).save(*args, **kw)