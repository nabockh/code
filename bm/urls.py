from django.conf.urls import patterns, url
from bm import views

urlpatterns = patterns('',
    url(r'^create$', views.BenchmarkCreateWizardView.as_view(), name='bm_create'),
    url(r'^history', views.BenchmarkHistoryView.as_view())
)
