from django.db import models
from cms.models.pluginmodel import CMSPlugin


class DashboardPanel(CMSPlugin):
    class Meta:
        db_table = 'widget_dashboard_panel'
    title = models.CharField(max_length=45)
    collapsed = models.BooleanField(default=False)

    def get_short_description(self):
        return self.title