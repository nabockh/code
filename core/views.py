from bm.models import Benchmark
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from core.forms import ContactForm
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        data['form'] = ContactForm()
        return data

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            comments = form.cleaned_data['comment']
            recipient_list = User.objects.filter(is_superuser=True).values_list('email', flat=True)
            if recipient_list:
                send_mail('Customer feedback', comments, last_name + '' + first_name, recipient_list)
            return HttpResponseRedirect('/thanks/')
        else:
            form = ContactForm()
        return render(request, 'core/home.html', {'form': form})


class DashboardView(TemplateView):
    template_name = 'bm/dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)

    def get_context_data(self,*args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args, **kwargs)
        context['user'] = self.request.user
        context['benchmarks'] = {
            'pending': Benchmark.pending.filter(owner=self.request.user)
        }
        return context


class ThankYouView(TemplateView):
    template_name = "general/thanks.html"