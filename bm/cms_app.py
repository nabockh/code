from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


class BmApphook(CMSApp):
    name = _("Benchmark Apphook")
    urls = ["bm.urls"]

apphook_pool.register(BmApphook)