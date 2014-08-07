from django.db import models
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