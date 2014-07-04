from copy import copy
import uuid
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from social.models import LinkedInIndustry
from social_auth.db.django_models import USER_MODEL


class RegionsManager(models.Manager):
    def get_queryset(self):
        return super(RegionsManager, self).get_queryset().filter(type__name='region')


class RegionType(models.Model):
    name = models.CharField(max_length=45)


class Region(models.Model):
    name = models.CharField(max_length=45)
    code = models.CharField(max_length=2, null=True, blank=True)
    type = models.ForeignKey(RegionType, related_name='regions')
    parent = models.ForeignKey('self', null=True, blank=True)

    objects = models.Manager()
    regions = RegionsManager()

    def __unicode__(self):
        return self.name


class Benchmark(models.Model):
    name = models.CharField(max_length=45)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(USER_MODEL, related_name='benchmarks', null=True, on_delete=models.SET_NULL)
    min_numbers_of_responses = models.PositiveIntegerField(default=5)
    geographic_coverage = models.ManyToManyField('Region', related_name='benchmarks')
    _industry = models.ForeignKey(LinkedInIndustry, db_column="industry_id", blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    approved = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(Benchmark, self).__init__(*args, **kwargs)
        self.already_approved = copy(self.approved)

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, value):
        self._industry = LinkedInIndustry.get(code=value) if str(value).isdigit() else LinkedInIndustry.get(value)

    def __unicode__(self):
        return self.name

    def create_link(self):
        link = BenchmarkLink()
        self.links.add(link)
        return link

    @property
    def link(self):
        return self.links.first()

    class Meta:
        verbose_name = 'Pending Benchmark'
        # app_label = 'asx'


class BenchmarkInvitation(models.Model):
    benchmark = models.ForeignKey(Benchmark, related_name='invites')
    sender = models.ForeignKey(USER_MODEL, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    recipient = models.ForeignKey("social.Contact", on_delete=models.CASCADE, related_name='invites')
    sent_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=45)
    is_allowed_to_forward_invite = models.BooleanField(default=False)

    #TODO: this can produce extra db request
    def __unicode__(self):
        return str(self.recipient)


class BenchmarkLink(models.Model):
    benchmark = models.ForeignKey(Benchmark, related_name='links')
    slug = models.SlugField(max_length=36, unique=True)

    def __init__(self, *args, **kwargs):
        super(BenchmarkLink, self).__init__(*args, **kwargs)
        if not self.slug:
            self.slug = str(uuid.uuid4())

    def save(self, *args, **kwargs):
        while True:
            try:
                super(BenchmarkLink, self).save(*args, **kwargs)
            except IntegrityError:
                self.slug = str(uuid.uuid4())
            else:
                break

    def __unicode__(self):
        return 'http://{0}{1}'.format(Site.objects.get_current().domain, reverse('bm_answer', kwargs=dict(slug=self.slug)))


class Question(models.Model):
    MULTIPLE = 1
    RANKING = 2
    NUMERIC = 3
    SLIDING_SCALE = 4
    RANGE = 5

    TYPES = (
        (MULTIPLE, 'Multiple'),
        (RANKING, 'Ranking'),
        (NUMERIC, 'Numeric'),
        # (SLIDING_SCALE, 'Sliding scale'),
        (RANGE, 'Range'),
    )

    benchmark = models.ForeignKey(Benchmark, rel_class=models.OneToOneRel, on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    description = models.TextField()
    type = models.PositiveSmallIntegerField(choices=TYPES)


class QuestionResponse(models.Model):
    question = models.ForeignKey(Question, related_name='responses')
    user = models.ForeignKey(USER_MODEL, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)

    @property
    def data(self):
        if self.question.type == Question.MULTIPLE:
            return self.data_choices
        elif self.question.type == Question.RANKING:
            return self.data_ranks
        elif self.question.type == Question.NUMERIC or self.question.type == Question.SLIDING_SCALE:
            return self.data_numeric
        elif self.question.type == Question.RANGE:
            return self.data_range


class QuestionChoice(models.Model):
    question = models.ForeignKey(Question, related_name='choices')
    label = models.CharField(max_length=45)
    order = models.PositiveSmallIntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(QuestionChoice, self).__init__(*args, **kwargs)
        label = kwargs.get('label')
        order = kwargs.get('order')
        if label and order:
            self.label = label
            self.order = order


class QuestionRanking(models.Model):
    question = models.ForeignKey(Question, related_name='ranks')
    label = models.CharField(max_length=45)
    order = models.PositiveSmallIntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(QuestionRanking, self).__init__(*args, **kwargs)
        label = kwargs.get('label')
        order = kwargs.get('order')
        if label and order:
            self.label = label
            self.order = order


class QuestionOptions(models.Model):
    question = models.ForeignKey(Question, rel_class=models.OneToOneRel, related_name='options')
    units = models.CharField(max_length=50)
    number_of_decimal = models.PositiveSmallIntegerField(default=2)

    def __init__(self, units, number_of_decimal, *args, **kwargs):
        super(QuestionOptions, self).__init__(*args, **kwargs)
        self.units = units
        self.number_of_decimal = number_of_decimal


class ResponseChoice(models.Model):
    response = models.ForeignKey(QuestionResponse, related_name='data_choices')
    choice = models.ForeignKey(QuestionChoice)


class ResponseRanking(models.Model):
    response = models.ForeignKey(QuestionResponse, related_name='data_ranks')
    rank = models.ForeignKey(QuestionRanking)
    value = models.IntegerField()


class ResponseNumeric(models.Model):
    response = models.ForeignKey(QuestionResponse, rel_class=models.OneToOneRel, related_name='data_numeric')
    value = models.IntegerField()


class ResponseRange(models.Model):
    response = models.ForeignKey(QuestionResponse, rel_class=models.OneToOneRel, related_name='data_range')
    min = models.IntegerField()
    max = models.IntegerField()

