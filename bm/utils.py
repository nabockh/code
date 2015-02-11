from django.db.models import Aggregate as AggregateWrapper, DecimalField
from django.db.models.query import QuerySet
from django.db.models.sql.aggregates import Aggregate


class BmQuerySet(QuerySet):

    def iterator(self):
        for obj in super(BmQuerySet, self).iterator():
            obj.select_class()
            yield obj


class ArrayAggSql(Aggregate):
    sql_function = 'array_agg'


class ArrayAgg(AggregateWrapper):
    name = 'Array_Agg'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = ArrayAggSql(col, source=source, is_summary=is_summary, **self.extra)
        aggregate.field = DecimalField()
        query.aggregates[alias] = aggregate


class StringAggSql(Aggregate):
    sql_function = 'string_agg'
    sql_template = "%(function)s(%(field)s, '')"


class StringAgg(AggregateWrapper):
    name = 'String_Agg'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = StringAggSql(col, source=source, is_summary=is_summary, **self.extra)
        aggregate.field = DecimalField()
        query.aggregates[alias] = aggregate