from app.settings import FIRST_TIME_USER_REDIRECT_URL, REGISTERED_USER_REDIRECT_URL, MESSAGE_BETA_INVITE
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView, TemplateView
from social import tasks
from social_auth.decorators import dsa_view
from social_auth.views import associate_complete, auth_complete, DEFAULT_REDIRECT
from django.contrib.auth import login, REDIRECT_FIELD_NAME
from social_auth.utils import setting, backend_setting
LOGIN_ERROR_URL = setting('LOGIN_ERROR_URL', setting('LOGIN_URL'))
from django.contrib import messages
from urllib2 import quote
from social.signals import first_time_user_login

@csrf_exempt
@dsa_view()
def complete(request, backend, *args, **kwargs):
    """Authentication complete view, override this view if transaction
    management doesn't suit your needs."""
    if request.user.is_authenticated():
        return associate_complete(request, backend, *args, **kwargs)
    else:
        return complete_process(request, backend, *args, **kwargs)


def complete_process(request, backend, *args, **kwargs):
    """Authentication complete process"""
    # pop redirect value before the session is trashed on login()
    redirect_value = request.session.get(REDIRECT_FIELD_NAME, '') or \
                     request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    user = auth_complete(request, backend, *args, **kwargs)

    if isinstance(user, HttpResponse):
        return user

    if not user and request.user.is_authenticated():
        return HttpResponseRedirect(redirect_value)

    msg = None
    if user:
        if getattr(user, 'is_active', True):
            # catch is_new flag before login() might reset the instance
            is_new = getattr(user, 'is_new', False)
            login(request, user)
            # user.social_user is the used UserSocialAuth instance defined
            # in authenticate process
            treshold = 10  # seconds
            if not redirect_value:
                if is_new:
                    first_time_user_login.send(sender=request.user, user=request.user)
                    redirect_value = FIRST_TIME_USER_REDIRECT_URL
                else:
                    redirect_value = REGISTERED_USER_REDIRECT_URL
            social_user = user.social_user
            if redirect_value:
                request.session[REDIRECT_FIELD_NAME] = redirect_value or \
                                                       DEFAULT_REDIRECT

            if setting('SOCIAL_AUTH_SESSION_EXPIRATION', True):
                # Set session expiration date if present and not disabled by
                # setting. Use last social-auth instance for current provider,
                # users can associate several accounts with a same provider.
                expiration = social_user.expiration_datetime()
                if expiration:
                    try:
                        request.session.set_expiry(expiration)
                    except OverflowError:
                        # Handle django time zone overflow, set default expiry.
                        request.session.set_expiry(None)

            # store last login backend name in session
            request.session['social_auth_last_login_backend'] = \
                    social_user.provider

            # Remove possible redirect URL from session, if this is a new
            # account, send him to the new-users-page if defined.
            new_user_redirect = backend_setting(backend,
                                           'SOCIAL_AUTH_NEW_USER_REDIRECT_URL')
            if new_user_redirect and is_new:
                url = new_user_redirect
            else:
                url = redirect_value or \
                      backend_setting(backend,
                                      'SOCIAL_AUTH_LOGIN_REDIRECT_URL') or \
                      DEFAULT_REDIRECT
        else:
            msg = setting('SOCIAL_AUTH_INACTIVE_USER_MESSAGE', None)
            url = backend_setting(backend, 'SOCIAL_AUTH_INACTIVE_USER_URL',
                                  LOGIN_ERROR_URL)
    else:
        msg = setting('LOGIN_ERROR_MESSAGE', None)
        url = backend_setting(backend, 'LOGIN_ERROR_URL', LOGIN_ERROR_URL)
    if msg:
        messages.error(request, msg)

    if redirect_value and redirect_value != url:
        redirect_value = quote(redirect_value)
        if '?' in url:
            url += '&%s=%s' % (REDIRECT_FIELD_NAME, redirect_value)
        else:
            url += '?%s=%s' % (REDIRECT_FIELD_NAME, redirect_value)
    return HttpResponseRedirect(url)