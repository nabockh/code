from core.forms import ContactForm
from django.contrib.sites.models import get_current_site
from django.conf import settings


def contact_form(request):
    return {'contact_form': ContactForm(request=request),
            'absolute_url': request.build_absolute_uri()}


def google_analytics(request):
    """
    Use the variables returned in this function to
    render your Google Analytics tracking code template.
    """
    ga_prop_id = getattr(settings, 'GOOGLE_ANALYTICS_PROPERTY_ID', False)
    ga_domain = getattr(settings, 'GOOGLE_ANALYTICS_DOMAIN', False)
    if not settings.DEBUG and ga_prop_id and ga_domain:
        return {
            'GOOGLE_ANALYTICS_PROPERTY_ID': ga_prop_id,
            'GOOGLE_ANALYTICS_DOMAIN': ga_domain,
        }
    return {}