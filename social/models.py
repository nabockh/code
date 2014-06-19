from django.core.cache import cache
from django.db import models, transaction
from social_auth.db.django_models import USER_MODEL
from bm.models import Region


class LinkedInIndustry(models.Model):
    code = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __init__(self, code, name):
        super(LinkedInIndustry, self).__init__()
        self.code = code
        self.name = name

    @classmethod
    def get(cls, name):
        if isinstance(name, cls):
            return name
        data = cache.get(cls.__name__)
        if not data:
            data = dict(LinkedInIndustry.objects.all().values_list('name', 'code'))
            cache.set(cls.__name__, data)
        return LinkedInIndustry(data.get(name), name)


class Company(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    _industry = models.ForeignKey(LinkedInIndustry, db_column="industry_id", blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    code = models.PositiveIntegerField(null=True, blank=True)

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, value):
        self._industry = LinkedInIndustry.get(value)


class Profile(models.Model):
    user = models.ForeignKey(USER_MODEL, related_name='social_profile', on_delete=models.CASCADE)
    headline = models.CharField(max_length=200, blank=True, null=True)
    company = models.ForeignKey(Company, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    location = models.ForeignKey(Region, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)


class Contact(models.Model):
    class Meta:
        unique_together = (('code', 'provider'),)

    code = models.CharField(max_length=255)
    owners = models.ManyToManyField(USER_MODEL, related_name='contacts')
    provider = models.PositiveSmallIntegerField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, null=True)
    location = models.ForeignKey(Region, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)

    @classmethod
    def create(cls, owner, provider, **kwargs):
        #check if contact already exists
        contact = cls.objects.filter(code=kwargs['id'], provider=provider).first() or cls()
        with transaction.atomic():
            try:
                if kwargs.get('positions').get('values'):
                    for position in kwargs.get('positions').get('values'):
                        if position.get('isCurrent'):
                            company = Company.objects.filter(code=position.get('company', {}).get('id')).first()
                            if company:
                                contact.company = company
                            else:
                                company = Company()
                                company.code = position.get('company', {}).get('id')
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
            contact.email = kwargs.get('email')
            contact.headline = kwargs.get('headline')
            contact.save()
            contact.owners.add(owner)
        return contact