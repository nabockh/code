from datetime import datetime
from bm.models import Benchmark
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from core.forms import ContactForm
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from social.forms import EmailInvitationRequest
from social.models import Invite
import django.db.models as models


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        data['form'] = ContactForm()
        data['invitation_form'] = EmailInvitationRequest(prefix='invite')
        return data

    def post(self, request, *args, **kwargs):
        form = ContactForm()
        if request.POST.has_key('invite-email'):
            invitation_form = EmailInvitationRequest(request.POST, prefix='invite')
            if invitation_form.is_valid():
                try:
                    login_invite = Invite()
                    login_invite.email = invitation_form.cleaned_data['email']
                    login_invite.save()
                except IntegrityError:
                    return HttpResponseRedirect('/')
                return HttpResponseRedirect('/')
        else:
            form = ContactForm(request.POST)
            if form.is_valid():
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                comments = form.cleaned_data['comment']
                recipient_list = User.objects.filter(is_superuser=True).values_list('email', flat=True)
                recipient_list = [email for email in recipient_list if email]
                if recipient_list:
                    send_mail('Customer feedback', comments, last_name + '' + first_name, recipient_list)
                return HttpResponseRedirect('/')
        return render(request, 'core/home.html', {'form': form, 'invitation_form': invitation_form})


class DashboardView(TemplateView):
    template_name = 'bm/dashboard.html'
    context_object_name = 'benchmark'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)

    def get_context_data(self,*args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args, **kwargs)
        context['user'] = self.request.user
        context['history'] = Benchmark.valid.filter(owner=self.request.user,
                                                    end_date__lte=datetime.now()) \
                                      .order_by('-end_date', '-id')[:5]
        context['benchmarks'] = {
            'pending': Benchmark.pending.filter(owner=self.request.user).order_by('-end_date', '-id'),
            'recent': Benchmark.objects \
                .annotate(responses_count=models.Count('question__responses')) \
                .filter(models.Q(approved=True,
                                 responses_count__gte=models.F('min_numbers_of_responses'),
                                 end_date__lte=datetime.now()) &
                        (models.Q(question__responses__user=self.request.user) |
                         models.Q(owner=self.request.user)) ) \
                .order_by('-end_date', '-id')[:5],
            'popular': Benchmark.valid.filter(
                                popular=True,
                                end_date__lte=datetime.now(),
                                _industry=self.request.user.social_profile.first().company.industry) \
                            .order_by('-end_date', '-id')
        }
        context['contact_form'] = ContactForm()
        return context


class ThankYouView(TemplateView):
    template_name = "general/thanks.html"


class BetaView(TemplateView):
    template_name = "social/beta.html"