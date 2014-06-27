from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from core.forms import ContactForm
from django.contrib.auth.models import User


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        data['form'] = ContactForm()
        return data

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first name']
            last_name = form.cleaned_data['last name']
            comments = form.cleaned_data['comments']
            recipient_list = User.objects.filter(is_superuser=True).values_list('email', flat=True)
            send_mail('Customer feedback', comments, last_name + '' + first_name, recipient_list)
            return HttpResponseRedirect('/thanks/')