from app import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Count
from linkedin import linkedin
from social.backend.linkedin import extract_access_tokens, LinkedInApplication
from social_auth.db.django_models import USER_MODEL
import random


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
    class Meta:
        unique_together = (('code', 'provider'),)

    code = models.CharField(max_length=255)
    owners = models.ManyToManyField(USER_MODEL, related_name='contacts')
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
    def send_mail(cls, user_from, subject, body, contacts):
        if not list(contacts):
            return
        assert isinstance(contacts[0], cls), 'Contacts should be social.Contact instances'
        recipients_without_email = []
        for contact in contacts:
            if contact.email:
                send_mail(subject, body, user_from.email, recipient_list=[contact.email])
            else:
                recipients_without_email.append(contact.code)
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

    @classmethod
    def create(cls, owner, provider, **kwargs):
        from bm.models import Region
        if kwargs['id'] == 'private':
            print "Contacts have explicitly set their information to private"
            return

        #check if contact already exists
        contact = cls.objects.filter(code=kwargs['id'], provider=provider).first()
        if not contact:
            contact = cls.objects.filter(first_name=kwargs['firstName'], last_name=kwargs['lastName'], headline=kwargs.get('headline', None), provider=provider).first()
            if contact:
                contact.code = kwargs['id']
                contact.save()
        contact = contact or cls()
        with transaction.atomic():
            try:
                if kwargs.get('positions').get('values'):
                    for position in kwargs.get('positions').get('values'):
                        if position.get('isCurrent'):
                            company = None
                            company_id = position.get('company', {}).get('id')
                            if company_id:
                                company = Company.objects.filter(code=position.get('company', {}).get('id'), _industry__name=kwargs.get('industry', {})).first()
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
                print "Contacts have explicitly set their information to private"
                return
            location = Region.objects.filter(code=kwargs.get('location', {}).get('country', {}).get('code')).first()
            if not location:
                print "Don't have Contact location"
                return
                # location = Region()
                # location.code = kwargs.get('location', {}).get('country', {}).get('code')
                # location.save()
            contact.location = location
            contact.code = kwargs['id']
            contact.provider = provider
            contact.first_name = kwargs['firstName']
            contact.last_name = kwargs['lastName']
            contact.email = kwargs.get('email') or contact.email
            contact.headline = kwargs.get('headline')
            contact.save()
            contact.owners.add(owner)
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
                                    'headline')[:10]


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