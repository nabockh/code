from core.forms import ContactForm
from django.contrib.sites.models import get_current_site


def contact_form(request):
    return {'contact_form': ContactForm(request=request),
            'absolute_url': request.build_absolute_uri()}