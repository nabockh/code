from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from core.models import DashboardPanel
from django.utils.translation import ugettext_lazy as _


class DashboardPanelGroupPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Panel Group"
    render_template = "dashboard/panel_group.html"
    allow_children = True


class DashboardPanelPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Panel"
    model = DashboardPanel
    render_template = "dashboard/panel.html"
    allow_children = True

plugin_pool.register_plugin(DashboardPanelGroupPlugin)
plugin_pool.register_plugin(DashboardPanelPlugin)
