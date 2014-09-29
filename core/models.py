from app import settings
from Crypto.Cipher import ARC4
import base64
from django.db import models
from django.http import HttpResponseForbidden
from cms.models.pluginmodel import CMSPlugin


class DashboardPanel(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_panel'
    title = models.CharField(max_length=45)
    collapsed = models.BooleanField(default=False)

    def get_short_description(self):
        return self.title


class DashboardPanel(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_panel'
    title = models.CharField(max_length=45)
    collapsed = models.BooleanField(default=False)

    def get_short_description(self):
        return self.title


class DashboardHistory(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_history'
    max_items = models.SmallIntegerField(default=5)

    def get_short_description(self):
        return 'Dashboard History (%d items)' % self.max_items


class DashboardPending(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_pending'

    def get_short_description(self):
        return 'Dashboard Pending Benchmarks'


class DashboardRecent(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_recent'

    def get_short_description(self):
        return 'Dashboard Recent Benchmarks'


class DashboardPopular(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_popular'

    def get_short_description(self):
        return 'Dashboard Popular Benchmarks'


class DashboardPopular(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_popular'

    def get_short_description(self):
        return 'Dashboard Popular Benchmarks'


class ButtonInviteColleague(CMSPlugin):
    class Meta:
        db_table = 'widget_button_invite_colleague'
    label = models.CharField(max_length=100, default='Invite a colleague')

    def get_short_description(self):
        return 'Button'


class ButtonCreateBenchmark(CMSPlugin):
    class Meta:
        db_table = 'widget_button_create_benchmark'
    label = models.CharField(max_length=100, default='Create new benchmark')

    def get_short_description(self):
        return 'Button'


class HomeExample(CMSPlugin):
    class Meta:
        db_table = 'widget_home_example'
    TYPES = (
        (1, 'benchmark'),
        (2, 'market-trending'),
        (3, 'market-share'),
        (4, 'market-size'),
        (5, 'historical-series'),
        (6, 'adoption-rate'),
    )

    label = models.CharField(max_length=50)
    description = models.TextField()
    type = models.SmallIntegerField(choices=TYPES)

    def get_short_description(self):
        return self.label

    @property
    def type_class(self):
        return dict(self.TYPES)[self.type]


class HomeHowItWorks(CMSPlugin):
    class Meta:
        db_table = 'widget_home_how_it_works'
    TYPES = (
        ('fa-cogs', 'Custom'),
        ('fa-comments', 'Comments'),
        ('fa-tasks', 'Tasks'),
    )

    label = models.CharField(max_length=50)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=TYPES)

    def get_short_description(self):
        return self.label

    @property
    def type_class(self):
        return dict(self.TYPES)[self.type]

class SystemKey(models.Model):
    class Meta:
        db_table = 'system_keys'

    key_name = models.CharField(max_length=50, unique=True)
    _payload = models.CharField(max_length=500)
    key_group = models.CharField(max_length=50)
    description = models.TextField(max_length=1000)

    @classmethod
    def get_keys(self, group):
        keys = {}
        for key in SystemKey.objects.filter(key_group=group).all():
            keys[key.key_name] = key.decrypted_payload
        return keys

    @property
    def payload(self):
        return self._payload

    @property
    def decrypted_payload(self):
        encobj = ARC4.new(settings.SECRET_KEY)
        enc_string = base64.decodestring(self._payload)
        return encobj.decrypt(enc_string)

    def set_payload(self, value):
        encobj = ARC4.new(settings.SECRET_KEY)
        self._payload = base64.encodestring(encobj.encrypt(value))


    def delete(self, using=None):
        raise HttpResponseForbidden()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_payload(self._payload)
        super(SystemKey, self).save(force_insert=force_insert, force_update=force_update,
                                    using=using, update_fields=update_fields)