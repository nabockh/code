from datetime import datetime, timedelta
import uuid
import math
from app.settings import BENCHMARK_DURATIONS_DAYS
from bm.utils import BmQuerySet, ArrayAgg
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError, connection
from django.db.models import Count, F
from django.db.models.aggregates import Min
from django.utils.functional import cached_property
from social.models import LinkedInIndustry
from social_auth.db.django_models import USER_MODEL
import numpy
import collections, operator
from decimal import Decimal, getcontext
import json


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
            .annotate(responses_count=Count('question__responses', distinct=True))\
            .filter(approved=True, responses_count__gte=F('min_numbers_of_responses'))


class BenchmarkPendingManager(models.Manager):
    def get_queryset(self):
        return super(BenchmarkPendingManager, self).get_queryset() \
            .annotate(responses_count=Count('question__responses', distinct=True))\
            .exclude(approved=False) \
            .filter(end_date__gt=datetime.now())\
            .distinct()


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
            elif self.question_type == Question.YES_NO:
                self.__class__ = BenchmarkYesNo

    @property
    def industry(self):
        return self._industry

    @industry.setter
    def industry(self, value):
        self._industry = LinkedInIndustry.get(code=value) if str(value).isdigit() else LinkedInIndustry.get(value)

    @property
    def is_new(self):
        delta = datetime.date(datetime.now()) - self.start_date
        return delta.days <= 1

    @property
    def days_left(self):
        if self.end_date:
            delta = self.end_date - datetime.now().date()
            return delta.days
        else:
            return 4

    @property
    def progress(self):
        if hasattr(self, 'responses_count'):
            return min(int(round(float(self.responses_count)/self.min_numbers_of_responses*100)), 100)

    @property
    def geography(self):
        region = self.geographic_coverage.first()
        return region.name if region else 'Global'

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

    @cached_property
    def charts(self):
        return {}

    def calc_average_rating(self):
        if not hasattr(self, 'rate_avg'):
            all_ratings = BenchmarkRating.objects.filter(benchmark=self).values_list('rating', flat=True)
            if all_ratings:
                self.rate_avg = float(sum(all_ratings))/len(all_ratings)
            else:
                self.rate_avg = 0
        return self.rate_avg or 0

    @property
    def contributors(self):
        if not hasattr(self, '_contributors'):
            return self.question.first().responses.count()
        return self._contributors

    @property
    def charts_allowed(self):
        return [name for name, title in self.available_charts]

    @property
    def calc_progress(self):
        return min(int(round(float(self.contributors)/self.min_numbers_of_responses*100)), 100)


class BenchmarkMultiple(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Multiple'

    available_charts = [('Pie', 'Pie Chart'), ('Column', 'Column Chart')]
    default_chart = 'Pie'

    @cached_property
    def charts(self):
        series = self.series_statistic.values('series', 'value')
        series = [[str(s['series']), s['value']] for s in series]
        value_sum = sum([vote[1] for vote in series])
        for vote in series:
            value = round((float(vote[1])/value_sum)*100)
            del vote[1]
            vote.append(value)
        series1 = list(series)
        series.insert(0, ['series', 'votes'])
        title = ['Series']
        for s, _ in series1:
            title.append(s)
        series_data = [title]
        sampled_data = [None,] * len(series1)
        for idx, (s, v) in enumerate(series1):
            data = sampled_data[:]
            data[idx] = v
            series_data.append([s, ]+data)
        return {
            'pie': series,
            'column': series_data,
        }


class BenchmarkRanking(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Ranking'

    available_charts = [('Bar', 'Bar Chart')]
    default_chart = 'Bar'

    @cached_property
    def charts(self):
        series1 = self.series_statistic.values('series', 'sub_series', 'value').order_by('series')
        ranks = []
        for item in series1:
            if item.get('series') not in ranks:
                ranks.append(item.get('series'))
        value = []
        for rank in ranks:
            rank_val = []
            for item in series1:
                if item.get('series') == rank:
                    rank_val.append((item.get('sub_series'), item.get('value')))
            rank_val.insert(0, rank)
            value.append(rank_val)
        avg_total = {}
        for item in value:
            avg = []
            for vote, count in item[1:]:
                avg.extend(vote * count)
            avg_total[item[0]] = round(numpy.average(map(int, avg)), 2)
        series1 = [[(s['series'] + ' as Rank ' + s['sub_series']), s['value']] for s in series1]
        series1.insert(0, ['series', 'count'])
        # series2 = self.series_statistic.values('series', 'sub_series', 'value').order_by('series')
        # series2 = [[int(s['sub_series']), s['series'], s['value']] for s in series2]
        # series2.insert(0, ['rank', 'series', 'votes'])
        series2 = self.series_statistic.values('series', 'sub_series', 'value').order_by('series')
        rank_data = {}
        for item in series2:
            rank_data.setdefault(item['series'], []).append((item['sub_series'], item['value']))
        series = sorted(rank_data)
        titles = ['Ranks']
        ranks = []
        for s in series:
            sub_ranks = [s]
            for rid, val in sorted(rank_data[s]):
                titles.append('Rank ' + rid)
                sub_ranks.append(val)
            ranks.append(sub_ranks)
        titles = [str(title) for title in titles]

        series2 = map(list, zip(titles, *ranks))
        for rank in series2[1:]:
            values = rank[1:]
            del rank[1:]
            for value in values:
                value = round((float(value) / sum(values)) * 100, 2)
                rank.append(value)
        if len(series2) == 11:
            series2.insert(10, series2.pop(2))
        bar_data = []
        bar_excel = []
        for rank in ranks:
            summa = sum(rank[1:])
            percent = []
            excel_percent = []
            for r in rank[1:]:
                obj = {'v': (round(Decimal(r/float(summa))*100, 1)),
                       'f': str((round(Decimal(r/float(summa))*100, 1)))+'%'}
                excel_percent.append(round(Decimal(r/float(summa))*100, 1))
                percent.append(obj)
            excel_percent.insert(0, rank[0])
            percent.insert(0, rank[0])
            bar_excel.append(excel_percent)
            bar_data.append(percent)
        ranks_titles = ['Rank']
        for idx, i in enumerate(series, start=1):
            ranks_titles.append('Rank ' + str(idx))
        [rank.append(avg_total.get(rank[0])) for rank in bar_data]
        for rank_excel in bar_excel:
            rank_excel.append(avg_total.get(rank_excel[0]))
        bar_data = sorted(bar_data, key=lambda k: k[-1])
        bar_excel = sorted(bar_excel, key=lambda k: k[-1])
        [rank.remove(rank[-1]) for rank in bar_data]
        [excel_rank.remove(excel_rank[-1]) for excel_rank in bar_excel]
        bar_data.insert(0, ranks_titles)
        graph_average = [v for k, v in avg_total.iteritems()]
        return json.dumps({
            'pie': series1,
            'column_ranking': series2,
            'bar': bar_data,
            'bar_excel': bar_excel,
            'avg': graph_average
        })


class BenchmarkNumeric(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Open Number'

    available_charts = [('Area', 'Area Chart'), ('Bell_Curve', 'Bell Curve Chart')]
    default_chart = 'Area'

    @cached_property
    def charts(self):
        responses = [i.data_numeric.all() for i in self.question.first().responses.all()]
        # remove extreme values from numeric responses values
        numeric_data = [response[0].value for response in responses]
        stddev = numpy.std(numeric_data)
        avg = numpy.mean(numeric_data)
        min_point = int(avg - (3 * stddev))
        max_point = int(avg + (3 * stddev))
        for i in xrange(len(numeric_data) - 1, -1, -1):
            element = numeric_data[i]
            if element < min_point or element > max_point:
                del numeric_data[i]
        counted_dict = collections.Counter(numeric_data)
        sorted_list = sorted(counted_dict.items(), key=operator.itemgetter(0))
        values = []
        percen = []
        for k, v in sorted_list:
            values.append(k)
            percen.append(v)
        values_percent = []
        for i in values:
            index = values.index(i)
            val_sum = sum(percen)
            if index == 0:
                values_percent.append(round(Decimal(percen[index] / float(val_sum) * 100), 1))
            else:
                values_percent.append(round(Decimal(percen[index]/float(val_sum)*100 + values_percent[index-1]), 1))
        if values_percent[-1] != 100:
            values_percent.remove(values_percent[-1])
            values_percent.append(100)
        area_raw_data = zip(values_percent, values)
        area_data = [[str(perc) + '%', val]for perc, val in area_raw_data]
        area_data.insert(0, ['Contributors', 'Contributor Value'])
        series = self.series_statistic.values('series', 'sub_series', 'value').order_by('id')
        series = [[str(s['series']), s['value']] for s in series]
        value_sum = sum([vote[1] for vote in series])
        for vote in series:
            value = round((float(vote[1])/value_sum)*100)
            del vote[1]
            vote.append(value)
        series1 = list(series)
        series.insert(0, ['series', 'votes'])
        title = ['Series']
        for s, _ in series1:
            title.append(s)
        series_data = [title]
        sampled_data = [None,] * len(series1)
        for idx, (s, v) in enumerate(series1):
            data = sampled_data[:]
            data[idx] = v
            series_data.append([s,]+data)
        bell_curve = self.numeric_statistic.values('min', 'max', 'avg', 'sd').first()
        return {
            'area': area_data,
            'pie': series,
            'column': series_data,
            'bell_curve': bell_curve,
            'units': self.question.first().options.first().units.encode('utf-8'),
        }


class BenchmarkRange(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Range'

    available_charts = [('Area', 'Area Chart'), ('Quartile', 'Quartile Chart')]
    default_chart = 'Area'

    @cached_property
    def charts(self):
        series = self.series_statistic.values('series', 'sub_series', 'value').order_by('id')
        series1 = [[str(s['series'] + '-' + s['sub_series']), s['value']] for s in series]
        excel_data = [[str(s['series'] + ',' + s['sub_series']), s['value']] for s in series]
        value_sum = sum([vote[1] for vote in series1])
        for vote in excel_data:
            value = round((float(vote[1])/value_sum)*100)
            del vote[1]
            vote.append(value)
        excel_data.insert(0, ['series', 'Contributors'])
        for vote in series1:
            value = round((float(vote[1])/value_sum)*100)
            del vote[1]
            vote.append(value)
        series3 = list(series1)
        series1.insert(0, ['series', 'Contributors'])
        title = ['Series']
        for s, _ in series3:
            title.append(s)
        series_data = [title]
        sampled_data = [None,] * len(series3)
        for idx, (s, v) in enumerate(series3):
            data = sampled_data[:]
            data[idx] = v
            series_data.append([s, ]+data)
        series2 = [['votes', 'min', 'max', 'min', 'max']]
        for s in series:
            series2.append([s['value'], int(s['series']), int(s['series']), int(s['sub_series']), int(s['sub_series'])])
        value_sum = sum([vote[0] for vote in series2[1:]])
        for vote in series2[1:]:
            value = round((float(vote[0])/value_sum)*100)
            del vote[0]
            vote.insert(0, value)

        # Data for area chart
        range_responses = [i.data_range.all() for i in self.question.first().responses.all()]
        numeric_data = sorted([numpy.mean([response[0].min, response[0].max]) for response in range_responses])
        avg = numpy.mean(numeric_data)
        stddev = numpy.std(numeric_data)
        min_point = int(avg - (3 * stddev))
        max_point = int(avg + (3 * stddev))
        for i in xrange(len(numeric_data) - 1, -1, -1):
            element = numeric_data[i]
            if element < min_point or element > max_point:
                del numeric_data[i]
        percen = []
        for i in numeric_data:
            index = numeric_data.index(i)
            val_sum = len(numeric_data)
            if index == 0:
                percen.append(round(Decimal(1/float(val_sum)*100), 1))
            else:
                percen.append(round(Decimal(1/float(val_sum)*100 + percen[index-1]), 1))
        if percen[-1] != 100:
            percen.remove(percen[-1])
            percen.append(100)
        area_raw_data = zip(percen, numeric_data)
        area_data = [[str(perc) + '%', val]for perc, val in area_raw_data]
        area_data.insert(0, ['Contributors', 'Contributor Average'])

        # Data for Quartile
        quartile_data = sorted([([response[0].min, response[0].max, numpy.mean([response[0].min, response[0].max])]) for response in range_responses])
        for i in xrange(len(quartile_data) - 1, -1, -1):
            element = quartile_data[i]
            if element[2] < min_point or element[2] > max_point:
                del quartile_data[i]
            else:
                del element[2]
        quartile_raw = sorted(quartile_data)
        quartile_raw.insert(0, ['min', 'max'])
        quartile_raw = [item for item in quartile_raw if item[0]!= item[1]]
        min_values = []
        max_values = []
        average = []
        for min, max in quartile_raw[1:]:
            average.append(numpy.average([min, max]))
            min_values.append(min)
            max_values.append(max)
        percentiles = [25, 50, 75, 100]
        quartiles = []
        for idx, i in enumerate(percentiles):
            quartiles.append([numpy.percentile(min_values, percentiles[idx]), numpy.percentile(max_values, percentiles[idx])])
        stock_data = [['quartile', 'min', 'avg', 'avg2', 'max']]
        excel_stock = []
        for idx, (q_min, q_max) in enumerate(quartiles, start=1):
            average = numpy.average([q_min, q_max])
            tooltip = {'v': idx, 'f': 'Quartile ' + (str(idx))}
            stock_data.append([tooltip, q_min, average, average, q_max])
            excel_stock.append(([str(idx) + ' Quartile', q_min, q_max, average]))

        return {
            'pie': series1,
            'column': series_data,
            'stock': stock_data,
            'area': area_data,
            'line': series2,
            'ecxel_stock': excel_stock,
            'ecxel': excel_data,
            'units': self.question.first().options.first().units.encode('utf-8'),
         }


class BenchmarkYesNo(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Yes/No'

    available_charts = [('Pie', 'Pie Chart'), ('Column', 'Column Chart')]
    default_chart = 'Pie'

    @cached_property
    def charts(self):
        series = self.series_statistic.values('series', 'value')
        series = [[str(s['series']), s['value']] for s in series]
        if len(series) >= 2:
            value_sum = series[0][1] + series[1][1]
            for vote in series:
                value = round((float(vote[1])/value_sum)*100)
                del vote[1]
                vote.append(value)
        else:
            value_sum = 1
            for vote in series:
                value = round((float(vote[1])/value_sum)*100)
                del vote[1]
                vote.append(value)
        series2 = list(series)
        series.insert(0, ['series', 'Votes'])
        title = ['Series']
        for s, _ in series2:
            title.append(s)
        series_data = [title]
        sampled_data = [None,] * len(series2)
        for idx, (s, v) in enumerate(series2):
            data = sampled_data[:]
            data[idx] = v
            series_data.append([s, ]+data)
        return {
            'pie': series,
            'column': series_data,
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

    @classmethod
    def user_friendly_invites_count(cls, first_name, last_name, bm_id=None):
        query = """
            SELECT i.id FROM bm_benchmarkinvitation i
              INNER JOIN social_contact sc ON sc.id = i.recipient_id
              INNER JOIN social_contact_owners o ON o.user_id = sc.user_id
              INNER JOIN social_contact c ON o.contact_id=c.id
            WHERE i."is_allowed_to_forward_invite" = TRUE AND
                  c."first_name" = %s AND
                  c."last_name" = %s
          """
        args = [first_name, last_name]
        if bm_id:
            query += ' AND i.benchmark_id=%s'
            args.append(bm_id)

        return len(list(cls.objects.raw(query, args)))


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
    YES_NO = 4
    RANGE = 5

    TYPES = (
        (MULTIPLE, 'Multiple choice'),
        (RANKING, 'Ranking'),
        (NUMERIC, 'Numerical value '),
        (RANGE, 'Range'),
        (YES_NO, 'Yes/No'),
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
        elif self.question.type == Question.YES_NO:
            return self.data_boolean


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
    UNITS = (
        ('$', '$'),
        ('\xe2\x82\xac', '\xe2\x82\xac'),
        ('\xc2\xa3', '\xc2\xa3'),
        ('%', '%'),
        ('year', 'year'),
        ('trades', 'trades'),
        ('clients', 'clients')
    )
    question = models.ForeignKey(Question, rel_class=models.OneToOneRel, related_name='options')
    units = models.CharField(max_length=50)

    def __init__(self, *args, **kwargs):
        super(QuestionOptions, self).__init__(*args, **kwargs)
        if 'units' in kwargs:
            self.units = kwargs.get('units')


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


class ResponseYesNo(models.Model):
    response = models.ForeignKey(QuestionResponse, rel_class=models.OneToOneRel, related_name='data_boolean')
    value = models.BooleanField()


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
        verbose_name = 'Benchmark Pending'
        verbose_name_plural = 'Benchmarks Pending'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(BenchmarkApproved)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class BenchmarkApproved(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Benchmark Approved'
        verbose_name_plural = 'Benchmark Approved'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class BenchmarkAuditLog(LogEntry):

    class Meta:
        proxy = True
        verbose_name = 'Audit Log'


class BmInviteEmail(models.Model):
    benchmark = models.ForeignKey(Benchmark, related_name='invitation_email')
    body = models.TextField()
