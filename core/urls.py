from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^beta$', views.BetaView.as_view(), name='beta'),
    url(r'^cms-popups$', views.CMSPopupsView.as_view(), name='cms_popup'),
    url(r'^disabled_cookies$', views.CookiesDisabled.as_view(), name='disabled_cookies')
    # url(r'^terms$', views.TermsAndConditionsView.as_view(), name='terms_conditions'),
)
