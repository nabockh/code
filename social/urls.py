from django.conf.urls import patterns, url
from social import views
from social.views import complete

urlpatterns = patterns('',
    url(r'^complete/(?P<backend>[^/]+)/$', complete,
        name='social_complete'),
)
