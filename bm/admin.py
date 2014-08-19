from bm.forms import DeclineBenchmarkForm, SendMailForm
from django.conf.urls import patterns
from django.contrib import admin

# Register your models here.
from bm.models import Benchmark, BenchmarkPending, BenchmarkApproved, BenchmarkAuditLog
from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader, Context
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

admin.site.unregister(User)


class CustomUserAdmin(UserAdmin):
    filter_horizontal = ('user_permissions', 'groups')
    save_on_top = True
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')

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


def decline_benchmark(modeladmin, request, queryset):
    queryset.update(approved=False)
decline_benchmark.short_description = "Decline selected benchmarks"


def approve_benchmark(modeladmin, request, queryset):
    queryset.update(approved=True)
approve_benchmark.short_description = "Approve selected benchmarks"


def make_popular(modeladmin, request, queryset):
    queryset.update(popular=True)
approve_benchmark.short_description = "Mark selected benchmarks as popular"


class BenchmarkPendingAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    class Meta:
        verbose_name = 'Pending Benchmark'

    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('approved', )]
    readonly_fields.append('question_description')
    readonly_fields.append('question_label')
    fields = ('approved', 'name', 'question_label', 'question_description', 'owner',
              'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses')
    actions = [decline_benchmark, approve_benchmark]

    def question_description(self, obj):
        return obj.question.first().description

    def question_label(self, obj):
        return obj.question.first().label

    question_description.short_description = 'Description'
    question_label.short_description = 'Label'


    def get_queryset(self, request):
        qs = super(BenchmarkPendingAdmin, self).get_queryset(Benchmark)
        return qs.filter(approved=None)

    list_filter = ('start_date', 'owner')

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
                owner = form.cleaned_data['Benchmark owner']
                email = form.cleaned_data['Owner email']
                benchmark = form.cleaned_data['Benchmark name']
                reason = form.cleaned_data['reason']
                recipient_list = [email]
                context = Context({
                    'owner': owner,
                    'benchmark': benchmark,
                    'reason': reason,
                })
                send_mail('Declined Benchmark', template.render(context), None, recipient_list)
                return HttpResponseRedirect('/admin/bm/benchmarkpending/')
        return render(self.request, 'admin/decline_form.html', {'form': form})


class BenchmarkApprovedAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('popular')]
    readonly_fields.append('question_description')
    readonly_fields.append('question_label')
    fields = ('approved', 'popular', 'name', 'question_label', 'question_description', 'owner',
              'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses')
    actions = [make_popular]
    # readonly_fields = ['related_objects']

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
