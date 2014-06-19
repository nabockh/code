from django.views.generic import RedirectView
from social import tasks


class ContactsImport(RedirectView):
    pattern_name = 'home'

    def get(self, request, *args, **kwargs):
        tasks.import_linkedin_contacts.delay(request.user)
        return super(ContactsImport, self).get(request, *args, **kwargs)
