from cms.api import get_page_draft
from cms.cms_toolbar import HISTORY_MENU_IDENTIFIER
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from cms.toolbar_pool import toolbar_pool
from cms.toolbar_base import CMSToolbar


@toolbar_pool.register
class PopupsToolbar(CMSToolbar):

    def populate(self):
        self.page = get_page_draft(self.request.current_page)
        menu = self.toolbar.get_or_create_menu('core-app', _('Popups'))
        url = reverse('cms_popup')
        menu.add_link_item(_('Edit'), url=url)
        history_menu = self.toolbar.get_or_create_menu(HISTORY_MENU_IDENTIFIER, _('History'), position=2)
        if self.page and self.toolbar.edit_mode:
            delete_action = reverse('cms_delete_widgets', kwargs=(dict(page=self.page.pk)))
            delete_question = _('Are you sure you want to delete all widgets on current page?')
            history_menu.add_ajax_item(_('Delete All widgets on page'), action=delete_action, question=delete_question,
                                       on_success=self.toolbar.REFRESH_PAGE)
        delete_action = reverse('cms_delete_static_widgets')
        delete_question = _('Are you sure you want to delete all widgets from all static placeholders?')
        history_menu.add_ajax_item(_('Delete All static widgets'), action=delete_action, question=delete_question,
                                   on_success=self.toolbar.REFRESH_PAGE)