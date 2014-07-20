from django.db.models.query import QuerySet


class BmQuerySet(QuerySet):

    def iterator(self):
        obj = super(BmQuerySet, self).iterator().next()
        obj.select_class()
        yield obj