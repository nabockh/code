from django.conf.urls import patterns, url
from bm import views

urlpatterns = patterns('',
    url(r'^save_preview$', views.PreviewPopupView.as_view(), name='bm_preview'),
    url(r'^create$', views.BenchmarkCreateWizardView.as_view(), name='bm_create'),
    url(r'^history$', views.BenchmarkHistoryView.as_view(), name='bm_history'),
    url(r'^welcome$', views.WelcomeView.as_view(), name='bm_welcome'),
    url(r'^answer/(?P<slug>[-a-zA-Z0-9_]+)$', views.BaseBenchmarkAnswerView.as_view(), name='bm_answer'),
    url(r'^(?P<bm_id>\d+)$', views.BenchmarkDetailView.as_view(), name='bm_details'),
    url(r'^(?P<bm_id>\d+)/aggregate$', views.BenchmarkAggregateView.as_view(), name='bm_aggregate'),
    url(r'^(?P<bm_id>\d+)/excel$', views.ExcelDownloadView.as_view(), name='bm_excel'),
    url(r'^(?P<bm_id>\d+)/add-recipients$', views.BenchmarkAddRecipientsView.as_view(), name='bm_add_recipients'),
    url(r'^search/$', views.BenchmarkSearchView.as_view(), name='bm_search'),
)
