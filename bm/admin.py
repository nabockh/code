from bm.forms import DeclineBenchmarkForm, SendMailForm
from cms.models import StaticPlaceholder
from django.conf.urls import patterns
from django.contrib import admin
from django.contrib import messages
# Register your models here.
from bm.models import Benchmark, BenchmarkPending, BenchmarkApproved, BenchmarkAuditLog
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader, Context
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.views.generic import FormView
from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from core.utils import get_context_variables
from social_auth.db.django_models import Association, Nonce, UserSocialAuth
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(Association)
admin.site.unregister(Nonce)
admin.site.unregister(UserSocialAuth)


class CustomUserAdmin(UserAdmin):
    filter_horizontal = ('user_permissions', 'groups')
    save_on_top = True
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')

    class Media:
        js = ['js/admin-custom-ui.js']

    def response_change(self, request, obj):
        if '_send_mail' in request.POST:
            return HttpResponseRedirect('/admin/auth/user/%s/send_mail' % obj.id)
        else:
            return super(CustomUserAdmin, self).response_change(request, obj)

    def get_urls(self):
        urls = super(CustomUserAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^^(?P<user_id>\d+)/send_mail$', SendMail.as_view())
        )
        return my_urls + urls


class SendMail(FormView):
    template_name = 'admin/send_mail_form.html'
    form_class = SendMailForm

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(SendMail, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(SendMail, self).get_form_kwargs()
        user = User.objects.get(id=self.kwargs['user_id'])
        kwargs['user'] = user
        return kwargs

    def post(self, *args, **kwargs):
        template_name = 'admin/send_mail_form.html'
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
                template = loader.get_template('alerts/email_to_user.html')
                user = form.cleaned_data['User']
                email = form.cleaned_data['To']
                email_body = form.cleaned_data['Email_text']
                subject = form.cleaned_data['Subject']
                recipient_list = [email]
                context = Context({
                    'user': user,
                    'email_body': email_body
                })
                send_mail(subject, template.render(context), None, recipient_list)
                return HttpResponseRedirect('/admin/auth/user')
        else:
            form = self.get_form(form_class)
        return render(self.request, template_name, {'form': form})

admin.site.register(User, CustomUserAdmin)


class ReadOnlyAdminMixin:

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Commented out while no need for multiple decline
# def decline_benchmark(modeladmin, request, queryset):
#     queryset.update(approved=False)
# decline_benchmark.short_description = "Decline selected benchmarks"


def approve_benchmark(modeladmin, request, queryset):
    """
    Action in Benchmark Admin that mark selected Benchmarks
    as Approved
    """
    for benchmark in queryset:
         LogEntry.objects.log_action(
              user_id=request.user.pk,
              content_type_id=ContentType.objects.get_for_model(benchmark).pk,
              object_id=benchmark.pk,
              object_repr=force_unicode(benchmark),
              action_flag=CHANGE,
              change_message='Changed approved.'
         )
         benchmark.approved = True
         post_save.send(sender=BenchmarkPending, instance=benchmark)
    queryset.update(approved=True)
approve_benchmark.short_description = "Approve selected benchmarks"


def make_popular(modeladmin, request, queryset):
    """
    Action in Benchmark Admin that mark selected Benchmarks
    as Popular
    """
    queryset.update(popular=True)
make_popular.short_description = "Mark selected benchmarks as popular"


def deaprove_benchmark(modeladmin, request, queryset):
    """
    Action in Benchmark Admin that mark selected Benchmarks
    as Not Approved. They will disappear from Approved and
    Pending benchmarks
    """
    queryset.update(approved=False)
deaprove_benchmark.short_description = "Mark selected benchmarks as NOT approved"



class InvitedContactsForm(forms.ModelForm):
    invites_list = forms.ChoiceField()

    class Meta:
        model = Benchmark

    def __init__(self, *args, **kwargs):
        super(InvitedContactsForm, self).__init__(*args, **kwargs)
        benchmark = kwargs['instance']
        choices = [(invite.recipient, invite.recipient) for invite in benchmark.invites.all().select_related('recipient')]
        self.fields['invites_list'] = forms.MultipleChoiceField(choices=choices, required=False)
        self.fields['invites_list'].widget.attrs['size'] = '10'


class BenchmarkPendingAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    class Meta:
        verbose_name = 'Pending Benchmark'

    form = InvitedContactsForm

    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('approved', )]
    readonly_fields.append('question_description')
    readonly_fields.append('question_label')
    fields = ('approved', 'name', 'question_label', 'question_description', 'owner',
              'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses', 'invites_list')
    actions = [approve_benchmark]

    def question_description(self, obj):
        return obj.question.first().description

    def question_label(self, obj):
        return obj.question.first().label

    question_description.short_description = 'Description'
    question_label.short_description = 'Label'

    list_filter = ('start_date', 'owner')

    def get_queryset(self, request):
        qs = super(BenchmarkPendingAdmin, self).get_queryset(Benchmark)
        return qs.filter(approved=None)

    def response_add(self, request, obj, post_url_continue="../%s/"):
        if '_continue' in request.POST:
            return HttpResponseRedirect('/admin/bm/')
        else:
            return super(BenchmarkPendingAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' in request.POST:
            app_label = obj._meta.app_label
            model = obj._meta.module_name
            reverse('admin:%s_%s_change' % (app_label, model), args=(obj.id,))
            return HttpResponseRedirect(obj.get_admin_url())
        elif '_decline' in request.POST:
            obj.approved = False
            obj.save()
            return HttpResponseRedirect('/admin/bm/benchmarkpending/decline{0}'.format(obj.id))
        elif '_approve' in request.POST:
            obj.approved = True
            obj.save()
            return HttpResponseRedirect('/admin/bm/benchmarkpending')
        else:
            return super(BenchmarkPendingAdmin, self).response_change(request, obj)

    def get_urls(self):
        urls = super(BenchmarkPendingAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^decline(\d+)$', DeclineView.as_view())
        )
        return my_urls + urls


class DeclineView(FormView):
    template_name = 'admin/decline_form.html'
    form_class = DeclineBenchmarkForm

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(DeclineView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        id = (self.request.path).split('/benchmarkpending/decline')[1]
        kwargs = super(DeclineView, self).get_form_kwargs()
        benchmark = Benchmark.objects.filter(id=id).first()
        owner = benchmark.owner
        benchmark = benchmark.name
        kwargs['benchmark'] = benchmark
        kwargs['owner'] = owner
        kwargs['email'] = owner.email
        return kwargs

    def post(self, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
                template = loader.get_template('alerts/declined_benchmark.html')
                email = form.cleaned_data['Owner email']
                benchmark = Benchmark.objects.get(pk=args[1])
                raw_context = get_context_variables(benchmark)
                raw_context['reason'] = form.cleaned_data['reason']
                raw_context['remaining_before_closure'] = benchmark.days_left
                context = Context(raw_context)
                send_mail('Declined Benchmark', template.render(context), None, [email])
                return HttpResponseRedirect('/admin/bm/benchmarkpending/')
        return render(self.request, 'admin/decline_form.html', {'form': form})


class BenchmarkApprovedAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    form = InvitedContactsForm
    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('popular', 'end_date', 'approved')]
    readonly_fields.append('question_description')
    readonly_fields.append('question_label')
    fields = ('approved', 'popular', 'name', 'question_label', 'question_description', 'owner',
              'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses', 'invites_list')
    actions = [make_popular, deaprove_benchmark]

    def get_actions(self, request):
        actions = super(BenchmarkApprovedAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_selected_approved(self, request, queryset):
        for obj in queryset:
            obj.delete()

        if queryset.count() == 1:
            message_bit = "1 benchmark approved entry was"
        else:
            message_bit = "%s benchmark approved entries were" % queryset.count()
        self.message_user(request, "%s successfully deleted." % message_bit)
    delete_selected_approved.short_description = "Delete selected Benchmark Approved entries"

    actions.append(delete_selected_approved)

    def question_description(self, obj):
        return obj.question.first().description

    def question_label(self, obj):
        return obj.question.first().label

    question_description.short_description = 'Description'
    question_label.short_description = 'Label'

    def get_queryset(self, request):
        qs = super(BenchmarkApprovedAdmin, self).get_queryset(Benchmark)
        return qs.filter(approved=True)

    def response_add(self, request, obj, post_url_continue="../%s/"):
        if '_continue' in request.POST:
            return HttpResponseRedirect('/admin/bm/')
        else:
            return super(BenchmarkApprovedAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' in request.POST:
            return HttpResponseRedirect(obj.get_admin_url())
        elif '_aggregate' in request.POST:
            obj.aggregate()
            self.message_user(request, "{0} was Aggregated!".format(obj.name), level=messages.INFO)
            return HttpResponseRedirect('/admin/bm/benchmarkapproved/{0}'.format(obj.id))
        else:
            return super(BenchmarkApprovedAdmin, self).response_change(request, obj)

    list_filter = ('popular', 'start_date', 'owner')


class BenchmarkAuditLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):

    list_display = ('action_time', 'object_repr', 'user', 'change_message')
    fields = ('object_repr', 'user', 'change_message')
    readonly_fields = ('object_repr', 'user', 'change_message')
    list_filter = ('user', 'object_repr')

    def get_queryset(self, request):
        return LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(Benchmark).pk,)\
            .order_by('-id', 'object_id')

admin.site.register(BenchmarkPending, BenchmarkPendingAdmin)
admin.site.register(BenchmarkApproved, BenchmarkApprovedAdmin)
admin.site.register(BenchmarkAuditLog, BenchmarkAuditLogAdmin)
