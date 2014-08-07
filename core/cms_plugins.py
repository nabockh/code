from datetime import datetime
from bm.models import Benchmark
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from core.models import DashboardPanel, DashboardHistory, DashboardPending, DashboardRecent, DashboardPopular, \
    ButtonInviteColleague
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


class DashboardHistoryPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "History"
    model = DashboardHistory
    render_template = "dashboard/history.html"

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['history'] = Benchmark.valid.filter(owner=context['request'].user, end_date__lte=datetime.now())\
            .order_by('-end_date')[:instance.max_items]
        return context


class DashboardPendingPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Pending"
    model = DashboardPending
    render_template = "dashboard/pending.html"

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['benchmarks'] = {
            'pending': Benchmark.pending.filter(owner=context['request'].user),
        }
        return context


class DashboardRecentPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Recent"
    model = DashboardRecent
    render_template = "dashboard/recent.html"

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['benchmarks'] = {
            'recent': Benchmark.valid.filter(owner=context['request'].user, end_date__lte=datetime.now()).order_by('-end_date')[:5],
        }
        return context


class DashboardPopularPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Popular"
    model = DashboardPopular
    render_template = "dashboard/popular.html"

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['benchmarks'] = {
            'popular': Benchmark.valid.filter(popular=True)
        }
        return context


class ButtonInviteColleaguePlugin(CMSPluginBase):
    module = _("Buttons")
    name = "Invite Colleague"
    model = ButtonInviteColleague
    render_template = "buttons/invite_colleague.html"


class ButtonCreateBenchmarkPlugin(CMSPluginBase):
    module = _("Buttons")
    name = "Create Benchmark"
    model = ButtonInviteColleague
    render_template = "buttons/create_benchmark.html"

plugin_pool.register_plugin(DashboardPanelGroupPlugin)
plugin_pool.register_plugin(DashboardPanelPlugin)
plugin_pool.register_plugin(DashboardHistoryPlugin)
plugin_pool.register_plugin(DashboardPendingPlugin)
plugin_pool.register_plugin(DashboardRecentPlugin)
plugin_pool.register_plugin(DashboardPopularPlugin)

plugin_pool.register_plugin(ButtonInviteColleaguePlugin)
plugin_pool.register_plugin(ButtonCreateBenchmarkPlugin)
