from bm.forms import DeclineBenchmarkForm
from django.conf.urls import patterns
from django.contrib import admin

# Register your models here.
from bm.models import Benchmark
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import loader, Context
from django.template.defaulttags import url
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
            return HttpResponseRedirect('/admin/send_mail/%s' % obj.id)
        else:
            return super(CustomUserAdmin, self).response_change(request, obj)

# Need view to handle form submittion

    def get_urls(self):
        urls = super(CustomUserAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^send_mail/(\d+)$', DeclineView.as_view())
        )
        return my_urls + urls

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


class BenchmarkPendingAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    class Meta:
        verbose_name = 'Pending Benchmark'

    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('approved', )]
    fields = ('approved', 'name', 'owner', 'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses')
    actions = [decline_benchmark, approve_benchmark]

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


class BenchmarkApproved(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Approved Benchmark'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class BenchmarkPending(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Pending Benchmark'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(BenchmarkApproved)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class BenchmarkApprovedAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('popular')]
    fields = ('approved', 'popular', 'name', 'owner', 'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses')

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

    list_filter = ('start_date', 'owner')

admin.site.register(BenchmarkPending, BenchmarkPendingAdmin)
admin.site.register(BenchmarkApproved, BenchmarkApprovedAdmin)
