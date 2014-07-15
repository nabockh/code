from django.conf.urls import patterns, url
from bm import views

urlpatterns = patterns('',
    url(r'^create$', views.BenchmarkCreateWizardView.as_view(), name='bm_create'),
    url(r'^history$', views.BenchmarkHistoryView.as_view(), name='bm_history'),
    url(r'^welcome$', views.WelcomeView.as_view(), name='bm_welcome'),
    url(r'^answer/(?P<slug>[-a-zA-Z0-9_]+)$', views.BaseBenchmarkAnswerView.as_view(), name='bm_answer'),
    url(r'^benchmark(?P<bm_id>\d+)/details$', views.RateBenchmarkView.as_view(), name='bm_details'),
    url(r'^benchmark(?P<bm_id>\d+)/statistic$', views.BenchmarkStatisticView.as_view(), name='bm_statistic'),
)
