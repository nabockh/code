from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from cms.toolbar_pool import toolbar_pool
from cms.toolbar_base import CMSToolbar


@toolbar_pool.register
class PopupsToolbar(CMSToolbar):

    def populate(self):
        menu = self.toolbar.get_or_create_menu('core-app', _('Popups'))
        url = reverse('cms_popup')
        menu.add_link_item(_('Edit'), url=url)