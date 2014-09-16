from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^beta$', views.BetaView.as_view(), name='beta'),
    url(r'^cms-popups$', views.CMSPopupsView.as_view(), name='cms_popup'),
    url(r'^cms-delete-widgets/(?P<page>\d+)$', views.CMSDeleteWidgets.as_view(), name='cms_delete_widgets'),
    url(r'^cms-delete-static-widgets$', views.CMSDeleteStaticWidgets.as_view(), name='cms_delete_static_widgets'),
    url(r'^disabled_cookies$', views.CookiesDisabled.as_view(), name='disabled_cookies'),
    url(r'^disabled_javascript$', views.JavascriptDisabled.as_view(), name='disabled_javascript$')
    # url(r'^terms$', views.TermsAndConditionsView.as_view(), name='terms_conditions'),
)
