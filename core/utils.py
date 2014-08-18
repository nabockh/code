from app import settings
from django.http import HttpResponse
import logging
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('bedade.background')



def login_required_ajax(function=None, redirect_field_name=None):
    """
    Just make sure the user is authenticated to access a certain ajax view

    Otherwise return a HttpResponse 401 - authentication required
    instead of the 302 redirect of the original Django decorator
    """
    def _decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=401)
        return _wrapped_view

    if function is None:
        return _decorator
    else:
        return _decorator(function)


def celery_log(func):
    def _decorator():
        try:
            return func()
        except:
            logger.exception('')
    _decorator.__name__ = func.__name__
    return _decorator