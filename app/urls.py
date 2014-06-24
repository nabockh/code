from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^linkedin/', include('social.urls')),
    url(r'^benchmark/', include('bm.urls')),
    url(r'^', include('core.urls')),
    url(r'', include('social_auth.urls')),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': "successfully_logget_out.html"})
)
