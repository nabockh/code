from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^dashboard$', views.DashboardView.as_view(), name='bm_dashboard'),
)
