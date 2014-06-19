from django.conf.urls import patterns, url
from social import views

urlpatterns = patterns('',
    url(r'^contacts/import$', views.ContactsImport.as_view(), name='in_contacts_import'),
)
