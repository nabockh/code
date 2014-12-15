from datetime import datetime
from bm.models import Benchmark
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from core.models import DashboardPanel, DashboardHistory, DashboardPending, DashboardRecent, DashboardPopular, \
    ButtonInviteColleague, HomeExample, HomeHowItWorks
from django.utils.translation import ugettext_lazy as _
import django.db.models as models

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
    cache = False

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['max_items'] = instance.max_items
        context['history'] = Benchmark.valid.filter(models.Q(owner=context['request'].user) |
                                      models.Q(question__responses__user=context['request'].user),
                                      end_date__lte=datetime.now()).order_by('-id', '-end_date', )[:instance.max_items]
        # context['history'] = Benchmark.valid.filter(owner=context['request'].user, end_date__lte=datetime.now())\
        #     .order_by('-end_date', '-id')[:instance.max_items]
        return context


class DashboardPendingPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Pending"
    model = DashboardPending
    render_template = "cms/dashboard/pending.html"
    cache = False

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['benchmarks'] = {
                'pending': Benchmark.pending.filter(models.Q(question__responses__user=context['request'].user) |
                                                    models.Q(owner=context['request'].user)).order_by('-end_date', '-id'),
        }
        return context


class DashboardRecentPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Recent"
    model = DashboardRecent
    render_template = "cms/dashboard/recent.html"
    cache = False

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        context['benchmarks'] = {
            'recent':Benchmark.objects \
                .annotate(responses_count=models.Count('question__responses')) \
                .filter(models.Q(approved=True,
                                 responses_count__gte=models.F('min_numbers_of_responses'),
                                 end_date__lte=datetime.now()) &
                        (models.Q(question__responses__user=context['request'].user) |
                         models.Q(owner=context['request'].user)) ) \
                .order_by('-end_date', '-id')[:5]
        }
        return context


class DashboardPopularPlugin(CMSPluginBase):
    module = _("Dashboard")
    name = "Popular"
    model = DashboardPopular
    render_template = "cms/dashboard/popular.html"
    cache = False

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        if context['request'].user.social_profile.first():
            context['benchmarks'] = {
                'popular': Benchmark.valid.filter(
                                popular=True,
                                end_date__lte=datetime.now(),
                                _industry=context['request'].user.social_profile.first().company.industry) \
                            .order_by('-end_date', '-id')
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
    allow_children = True

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
