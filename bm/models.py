from django.db import models
from social.models import LinkedInIndustry
from social_auth.db.django_models import USER_MODEL


class Benchmark(models.Model):
    name = models.CharField(max_length=45)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(USER_MODEL, related_name='benchmarks', null=True, on_delete=models.SET_NULL)
    min_numbers_of_responses = models.PositiveIntegerField(default=5)
    geographic_coverage = models.ManyToManyField('Region', related_name='benchmarks')
    _industry = models.ForeignKey(LinkedInIndustry, db_column="industry_id", blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    approved = models.BooleanField(default=False)

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, value):
        self._industry = LinkedInIndustry.get(code=value) if str(value).isdigit() else LinkedInIndustry.get(value)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Pending Benchmark'
        # app_label = 'asx'


class BenchmarkInvitation(models.Model):
    benchmark = models.ForeignKey(Benchmark)
    recipient = models.ForeignKey("social.Contact", on_delete=models.CASCADE)
    sent_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=45)
    is_allowed_to_forward_invite = models.BinaryField(default=False)


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
        (SLIDING_SCALE, 'Sliding scale'),
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

    def __init__(self, label=None, order=None, *args, **kwargs):
        super(QuestionChoice, self).__init__(*args, **kwargs)
        if label and order:
            self.label = label
            self.order = order


class QuestionRanking(models.Model):
    question = models.ForeignKey(Question, related_name='ranks')
    label = models.CharField(max_length=45)
    order = models.PositiveSmallIntegerField(null=True, blank=True)


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