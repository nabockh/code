from datetime import datetime
from app import settings
from app.settings import MESSAGE_LOGOUT, MESSAGE_BETA, MESSAGE_BETA_INVITE
from bm import metric_events
from bm.models import Benchmark
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import REDIRECT_FIELD_NAME, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, resolve_url, render_to_response
from django.template.response import TemplateResponse
from django.utils.encoding import force_str
from django.views.generic import TemplateView, RedirectView
from core.forms import ContactForm, TermsAndConditions
from bm.forms import InviteColleagueForm
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from metrics.models import Event
from metrics.utils import event_log
from social.forms import EmailInvitationRequest
from social.models import Invite
import django.db.models as models
from django.template import  Context
from django.template.loader import get_template


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def dispatch(self, request, *args, **kwargs):
        kwargs['login_next'] = request.GET.get('next')
        if kwargs['login_next'] and request.COOKIES.get('terms'):
            path = kwargs['login_next']
            resolved_login_url = force_str(resolve_url(settings.LOGIN_REAL_URL))
            return redirect_to_login(path, resolved_login_url, REDIRECT_FIELD_NAME)
        if request.user.is_authenticated():
            Event.log(metric_events.HOME_OPEN, request.user)
        return super(HomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, login_next, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        data['form'] = ContactForm(request=self.request)
        data['invitation_form'] = EmailInvitationRequest(prefix='invite')
        if login_next:
            data['terms_and_conditions_form'] = TermsAndConditions(initial={'next': login_next})
        return data

    # def get(self, request, *args, **kwargs):
    #     result = super(HomeView, self).get(request, *args, **kwargs)
    #     result.set_cookie('terms', 1)
    #     return result

    def post(self, request, *args, **kwargs):
        invitation_form = EmailInvitationRequest(prefix='invite')
        terms_form = TermsAndConditions()
        contact_form = ContactForm(request=request)
        if 'invite-email' in request.POST:
            invitation_form = EmailInvitationRequest(request.POST, prefix='invite')
            if invitation_form.is_valid():
                try:
                    login_invite = Invite()
                    login_invite.email = invitation_form.cleaned_data['email']
                    login_invite.save()
                    messages.add_message(request, MESSAGE_BETA_INVITE, 'Your request successfully have been accepted.')
                    return HttpResponseRedirect('/')
                except IntegrityError:
                    messages.add_message(request, MESSAGE_BETA_INVITE, 'Please wait for approval.')
                    return HttpResponseRedirect('/')
        elif 'next' in request.POST:
            terms_form = TermsAndConditions(data=request.POST)
            if terms_form.is_valid():
                path = terms_form.cleaned_data['next']
                resolved_login_url = force_str(resolve_url(settings.LOGIN_REAL_URL))
                result = redirect_to_login(path, resolved_login_url, REDIRECT_FIELD_NAME)
                result.set_cookie('terms', 1)
                return result
        else:
            contact_form = ContactForm(request=request, data=request.POST)
            if contact_form.is_valid():
                first_name = contact_form.cleaned_data['first_name']
                last_name = contact_form.cleaned_data['last_name']
                customer_email = contact_form.cleaned_data['email']
                comment = contact_form.cleaned_data['comment']
                recipient_list = User.objects.filter(is_superuser=True, email__isnull=False)\
                    .exclude(email__exact='')\
                    .values_list('email', flat=True)
                if recipient_list:
                    send_mail('Customer feedback', comment, '%s %s <%s>' % (first_name, last_name, customer_email),
                              recipient_list)
                return HttpResponseRedirect('/')
        return render(request, 'core/home.html', {'form': contact_form, 'invitation_form': invitation_form,
                                                  'terms_and_conditions_form': terms_form})


class DashboardView(TemplateView):
    template_name = 'bm/dashboard.html'
    context_object_name = 'benchmark'

    @method_decorator(login_required)
    @event_log(event_type=metric_events.DASHBOARD_OPEN)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)

    def get_context_data(self,*args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args, **kwargs)
        context['user'] = self.request.user
        context['history'] = Benchmark.valid.filter(owner=self.request.user,
                                                    end_date__lte=datetime.now()) \
                                      .order_by('-end_date', '-id')[:5]
        context['benchmarks'] = {
            'pending': Benchmark.pending.filter(models.Q(question__responses__user=self.request.user) |
                                                models.Q(owner=self.request.user))
                                                .annotate(responses_count=models.Count('question__responses'))
                                                .order_by('-end_date', '-id'),
            'recent': Benchmark.objects \
                .annotate(responses_count=models.Count('question__responses')) \
                .filter(models.Q(approved=True,
                                 responses_count__gte=models.F('min_numbers_of_responses'),
                                 end_date__lte=datetime.now()) &
                        (models.Q(question__responses__user=self.request.user) |
                         models.Q(owner=self.request.user)) ) \
                .order_by('-end_date', '-id')[:5],

        }
        # Check if user is associated with Social Profile
        if self.request.user.social_profile.exists():
            context['benchmarks']['popular'] = Benchmark.valid.filter(
                                popular=True,
                                end_date__lte=datetime.now(),
                                _industry=self.request.user.social_profile.first().company.industry) \
                            .order_by('-end_date', '-id')
        else:
            context['benchmarks']['popular'] = None
        context['contact_form'] = ContactForm()
        context['invite_colleague_form'] = InviteColleagueForm()
        return context

    def post(self, request, *args, **kwargs):
        invite_colleague = InviteColleagueForm(data=request.POST)
        if invite_colleague.is_valid():
            customer_email = invite_colleague.cleaned_data['colleague_email']
            recipient_list = [customer_email]
            user = request.user.get_full_name()
            if recipient_list:
                context = Context(
                    {
                        'user': user,
                        'site_link': request.build_absolute_uri(),
                    },)
                body = get_template('alerts/invite_colleague_email.html').render(context)
                send_mail('Invitation to Bedade from %s' % user, body, None, recipient_list)
            return HttpResponseRedirect('/dashboard')
        return render(request, 'bm/dashboard.html', {'invite_colegaue_form': invite_colleague})


class ThankYouView(TemplateView):
    template_name = "general/thanks.html"


class BetaView(RedirectView):
     url = '/'

     def get(self, request, *args, **kwargs):
        messages.add_message(request, MESSAGE_BETA, 'Beta')
        return super(BetaView, self).get(request, *args, **kwargs)


class LogoutView(RedirectView):
    url = '/'

    @event_log(event_type=metric_events.LOGOUT)
    def get(self, request, *args, **kwargs):
        """
        Logs out the user and displays 'You are logged out' message.
        """
        logout(request)
        messages.add_message(request, MESSAGE_LOGOUT, 'Logout')
        return super(LogoutView, self).get(request, *args, **kwargs)


class CMSPopupsView(TemplateView):
    template_name = 'cms/poppups.html'

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CMSPopupsView, self).dispatch(request, *args, **kwargs)


def csrf_failure(request, reason=""):
    """
    Default view used when request fails CSRF protection
    """

    return HttpResponseRedirect('/disabled_cookies')


class CookiesDisabled(TemplateView):
    template_name = 'core/cookies_disabled.html'


class JavascriptDisabled(TemplateView):
    template_name = 'core/javascript_disabled.html'