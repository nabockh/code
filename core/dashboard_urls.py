from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^$', views.DashboardView.as_view(), name='bm_dashboard'),
)
