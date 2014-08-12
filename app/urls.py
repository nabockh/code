from app import settings
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': "successfully_logget_out.html"}),
    url(r'^', include('social_auth.urls')),
    url(r'^social/', include('social.urls')),
    url(r'^', include('core.urls')),
    url(r'^benchmark/', include('bm.urls')),
    url(r'^', include('cms.urls')),
    url(r'^', include('core.cms_urls')),
)

if settings.DEBUG:
    urlpatterns = patterns('',
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'', include('django.contrib.staticfiles.urls')),
) + urlpatterns