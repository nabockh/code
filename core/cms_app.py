from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


class DashboardApphook(CMSApp):
    name = _("Dashboard Apphook")
    urls = ["core.dashboard_urls"]

apphook_pool.register(DashboardApphook)