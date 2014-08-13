from datetime import datetime, timedelta
import uuid
import math
from app.settings import BENCHMARK_DURATIONS_DAYS
from bm.utils import BmQuerySet, ArrayAgg
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError, connection
from django.db.models import Count, F
from django.db.models.aggregates import Min
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


class BenchmarkManager(models.Manager):
    def get_queryset(self):
        return BmQuerySet(self.model, using=self._db)\
            .annotate(question_type=Min('question__type'))


class BenchmarkValidManager(BenchmarkManager):
    def get_queryset(self):
        return super(BenchmarkValidManager, self).get_queryset()\
            .annotate(responses_count=Count('question__responses'))\
            .filter(approved=True, responses_count__gte=F('min_numbers_of_responses'))


class BenchmarkPendingManager(models.Manager):
    def get_queryset(self):
        return super(BenchmarkPendingManager, self).get_queryset()\
            .annotate(responses_count=Count('question__responses'))\
            .filter(approved=True, end_date__gt=datetime.now())


class Benchmark(models.Model):
    name = models.CharField(max_length=45)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(USER_MODEL, related_name='benchmarks', null=True, on_delete=models.SET_NULL)
    min_numbers_of_responses = models.PositiveIntegerField(default=5)
    geographic_coverage = models.ManyToManyField('Region', related_name='benchmarks')
    _industry = models.ForeignKey(LinkedInIndustry, db_column="industry_id", blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL)
    approved = models.NullBooleanField(blank=True)
    popular = models.BooleanField(default=False)
    overview = models.TextField(blank=True)

    objects = BenchmarkManager()
    valid = BenchmarkValidManager()
    pending = BenchmarkPendingManager()

    def __init__(self, *args, **kwargs):
        super(Benchmark, self).__init__(*args, **kwargs)
        self.already_approved = bool(self.approved)

    def __unicode__(self):
        return self.name

    def select_class(self):
        if not isinstance(self, BenchmarkPending):
            if self.question_type == Question.MULTIPLE:
                self.__class__ = BenchmarkMultiple
            elif self.question_type == Question.RANKING:
                self.__class__ = BenchmarkRanking
            elif self.question_type == Question.NUMERIC:
                self.__class__ = BenchmarkNumeric
            elif self.question_type == Question.RANGE:
                self.__class__ = BenchmarkRange

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, value):
        self._industry = LinkedInIndustry.get(code=value) if str(value).isdigit() else LinkedInIndustry.get(value)

    @property
    def days_left(self):
        delta = self.end_date - datetime.now().date()
        return delta.days

    @property
    def progress(self):
        if hasattr(self, 'responses_count'):
            return min(int(round(float(self.responses_count)/self.min_numbers_of_responses*100)), 100)

    def create_link(self):
        link = BenchmarkLink()
        self.links.add(link)
        return link

    @property
    def link(self):
        return self.links.first() if not hasattr(self, '_link') else self._link

    @link.setter
    def link(self, value):
        self._link = value

    def calculate_deadline(self):
        count_without_email = self.invites.filter(recipient___email__isnull=True, recipient__user_id__isnull=True).count()
        days_to_sent_via_linkedin = math.ceil(float(count_without_email)/100)
        self.end_date = datetime.now() + timedelta(days=days_to_sent_via_linkedin+BENCHMARK_DURATIONS_DAYS)

    def aggregate(self):
        cursor = connection.cursor()
        result = cursor.callproc('benchmark_aggregate', (self.id,))
        cursor.close()
        return result

    @property
    def charts(self):
        return {}

    def calc_average_rating(self):
        all_ratings = BenchmarkRating.objects.filter(benchmark=self)
        if all_ratings:
            rating_digits = [rating.rating for rating in all_ratings]
            average = float(sum(rating_digits))/len(rating_digits)
        else:
            average = 0
        return average

    @property
    def contributors(self):
        return self.question.first().responses.count()

    @property
    def charts_allowed(self):
        return [name for name, title in self.available_charts]


class BenchmarkMultiple(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Multiple'

    available_charts = [('Pie', 'Pie Chart'), ('Column', 'Column Chart')]

    @property
    def charts(self):
        series = self.series_statistic.values('series', 'value')
        series = [[str(s['series']), s['value']] for s in series]
        series.insert(0, ['series', 'count'])
        return {
            'pie': series,
            'column': series,
        }


class BenchmarkRanking(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Ranking'

    available_charts = [('Pie', 'Pie Chart'), ('Column', 'Column Chart')]

    @property
    def charts(self):
        series1 = self.series_statistic.values('series', 'sub_series', 'value').order_by('series')
        series1 = [[str(s['series'] + '-' + s['sub_series']), s['value']] for s in series1]
        series1.insert(0, ['series', 'count'])
        series2 = self.series_statistic.values('series').annotate(count=ArrayAgg('value')).order_by('series')
        series2 = [[str(s['series'])] + s['count'][::-1] for s in series2]
        series2.insert(0, ['series'] + [str(i) for i in range(1, len(s['count']) + 1)])
        return {
            'pie': series1,
            'column': series2,
        }


class BenchmarkNumeric(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Open Number'

    available_charts = [('Pie', 'Pie Chart'), ('Column', 'Column Chart'), ('Bell_Curve', 'Bell Curve Chart')]

    @property
    def charts(self):
        series = self.series_statistic.values('series', 'sub_series', 'value').order_by('id')
        series = [[str(s['series']), s['value']] for s in series]
        series.insert(0, ['series', 'count'])
        bell_curve = self.numeric_statistic.values('min', 'max', 'avg', 'sd').first()
        return {
            'pie': series,
            'column': series,
            'bell_curve': bell_curve
        }


class BenchmarkRange(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Range'

    available_charts = [('Pie', 'Pie Chart'), ('Column', 'Column Chart'), ('Line', 'Line Chart')]

    @property
    def charts(self):
        series = self.series_statistic.values('series', 'sub_series', 'value').order_by('id')
        series1 = [[str(s['series'] + '-' + s['sub_series']), s['value']] for s in series]
        series1.insert(0, ['series', 'count'])
        series2 = [['series', 'count']]
        for s in series:
            series2.append([int(s['series']), s['value']])
            series2.append([int(s['sub_series']), s['value']])
        return {
            'pie': series1,
            'column': series1,
            'line': series2,
        }


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
        # TODO: http is hardcoded
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

    benchmark = models.ForeignKey(Benchmark, related_name='question', rel_class=models.OneToOneRel, on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    description = models.TextField()
    type = models.PositiveSmallIntegerField(choices=TYPES)


class QuestionResponse(models.Model):
    question = models.ForeignKey(Question, related_name='responses')
    user = models.ForeignKey(USER_MODEL, related_name='responses', null=True, on_delete=models.SET_NULL)
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


class BenchmarkRating(models.Model):
    benchmark = models.ForeignKey(Benchmark, related_name='ratings')
    user = models.ForeignKey(USER_MODEL, null=True)
    rating = models.PositiveSmallIntegerField()


class SeriesStatistic(models.Model):
    benchmark = models.ForeignKey(Benchmark, on_delete=models.CASCADE, related_name='series_statistic')
    series = models.CharField(max_length=255)
    sub_series = models.CharField(max_length=255, blank=True, null=True)
    value = models.PositiveIntegerField()

    def __unicode__(self):
        return '{0}-{1}: {2}'.format(self.series, self.sub_series, self.value) if self.sub_series else \
               '{0}: {1}'.format(self.series, self.value)


class NumericStatistic(models.Model):
    benchmark = models.ForeignKey(Benchmark, on_delete=models.CASCADE, related_name='numeric_statistic')
    min = models.FloatField()
    max = models.FloatField()
    avg = models.FloatField()
    sd = models.FloatField()


class BenchmarkPending(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Pending Benchmark'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(BenchmarkApproved)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class BenchmarkApproved(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Approved Benchmark'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))
