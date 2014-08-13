from datetime import datetime
from bm.models import Benchmark
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from core.models import DashboardPanel, DashboardHistory, DashboardPending, DashboardRecent, DashboardPopular, \
    ButtonInviteColleague, HomeExample, HomeHowItWorks
from django.utils.translation import ugettext_lazy as _


class DashboardPanelGroupPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Panel Group"
    render_template = "cms/dashboard/panel_group.html"
    allow_children = True


class DashboardPanelPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Panel"
    model = DashboardPanel
    render_template = "cms/dashboard/panel.html"
    allow_children = True


class DashboardHistoryPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "History"
    model = DashboardHistory
    render_template = "cms/dashboard/history.html"

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
    render_template = "cms/dashboard/pending.html"

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
    render_template = "cms/dashboard/recent.html"

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
    render_template = "cms/dashboard/popular.html"

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
    render_template = "cms/buttons/invite_colleague.html"


class ButtonCreateBenchmarkPlugin(CMSPluginBase):
    module = _("Buttons")
    name = "Create Benchmark"
    model = ButtonInviteColleague
    render_template = "cms/buttons/create_benchmark.html"


class HomeExamplePlugin(CMSPluginBase):
    module = _("Home")
    name = "Example"
    model = HomeExample
    render_template = "cms/home/example.html"
    allow_children = True


class HomeHowItWorksPlugin(CMSPluginBase):
    module = _("Home")
    name = "How It Works"
    model = HomeHowItWorks
    render_template = "cms/home/how_it_works.html"

plugin_pool.register_plugin(DashboardPanelGroupPlugin)
plugin_pool.register_plugin(DashboardPanelPlugin)
plugin_pool.register_plugin(DashboardHistoryPlugin)
plugin_pool.register_plugin(DashboardPendingPlugin)
plugin_pool.register_plugin(DashboardRecentPlugin)
plugin_pool.register_plugin(DashboardPopularPlugin)

plugin_pool.register_plugin(ButtonInviteColleaguePlugin)
plugin_pool.register_plugin(ButtonCreateBenchmarkPlugin)

plugin_pool.register_plugin(HomeExamplePlugin)
plugin_pool.register_plugin(HomeHowItWorksPlugin)
