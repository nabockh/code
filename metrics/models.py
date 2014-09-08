from app.settings import METRICS
from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.cache import cache

TYPE_HTTP_REQUEST = 'HttpRequest'


class EventType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def register(cls, name, parent_id=None):
        obj, created = cls.objects.get_or_create(name=name, parent_id=parent_id)
        return obj

    @classmethod
    def get(cls, name):
        data = cache.get(cls.__name__)
        if not data:
            data = dict(cls.objects.values_list('name', 'id'))
            cache.set(cls.__name__, data)
        return data.get(name, 1)


class Event(models.Model):
    type = models.ForeignKey(EventType, related_name='events')
    user = models.ForeignKey(User, related_name='events', null=True, on_delete=models.SET_NULL)
    object = GenericForeignKey()
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{0} {1} at {2}'.format(self.user, self.type, self.date)

    @classmethod
    def log(cls, event_type, user, object=None, **kwargs):
        if METRICS:
            obj = cls()
            obj.type_id = event_type if isinstance(event_type, int) else EventType.get(event_type)
            obj.user = user
            if object:
                obj.object = object
            obj.save()
            return obj