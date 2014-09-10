from functools import wraps
import os
from app import settings
from app.settings import BASE_DIR
from django.http import HttpResponse
import logging
from django.conf import settings
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils._os import safe_join
from datetime import datetime, timedelta
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site


logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('bedade.background')


def get_context_variables(benchmark, request=None):
    context_vars = {}
    context_vars['benchmark'] = benchmark
    context_vars['number_of_invites'] = benchmark.invites.count()
    context_vars['benchmark_name'] = benchmark.name
    context_vars['query_details'] = benchmark.question.first().description
    context_vars['link_to_answer'] = benchmark.link
    context_vars['benchmark_creator'] = benchmark.owner
    context_vars['link_to_bm_results'] = str(Site.objects.get_current()) + reverse('bm_details', args=[benchmark.id])
    return context_vars


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
    @wraps(func)
    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logger.exception('')
    return _decorator

"""

Loading templates with ReserveLoader if templates are not found in DB and with Default Loaders.

"""
app_template_dirs = (
    os.path.join(BASE_DIR,  'templates/dbtemplates'),
)


class ReserveLoader(BaseLoader):
    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Returns the absolute paths to "template_name", when appended to each
        directory in "template_dirs". Any paths that don't lie inside one of the
        template dirs are excluded from the result set, for security reasons.
        """
        if not template_dirs:
            template_dirs = app_template_dirs
        for template_dir in template_dirs:
            try:
                yield safe_join(template_dir, template_name)
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of template_dir.
                pass

    def load_template_source(self, template_name, template_dirs=None):
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return (fp.read().decode(settings.FILE_CHARSET), filepath)
            except IOError:
                pass
        raise TemplateDoesNotExist(template_name)
