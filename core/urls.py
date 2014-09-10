from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^beta$', views.BetaView.as_view(), name='beta'),
    # url(r'^terms$', views.TermsAndConditionsView.as_view(), name='terms_conditions'),

)
