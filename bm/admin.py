from django.contrib import admin

# Register your models here.
from bm.models import Benchmark
from django.http import HttpResponseRedirect
from django.shortcuts import redirect


class ReadOnlyAdminMixin:

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BenchmarkPendingAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('approved', )]
    fields = ('approved', 'name', 'owner', 'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses')

    def get_queryset(self, request):
        qs = super(BenchmarkPendingAdmin, self).get_queryset(Benchmark)
        return qs.filter(approved=False)

    list_filter = ('start_date', 'owner')

    def response_add(self, request, obj, post_url_continue="../%s/"):
        if '_continue' in request.POST:
            return HttpResponseRedirect('/admin/bm/')
        else:
            return super(BenchmarkPendingAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' in request.POST:
            return HttpResponseRedirect('/admin/bm/')
        else:
            return super(BenchmarkPendingAdmin, self).response_change(request, obj)


class BenchmarkApproved(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Approved Benchmark'


class BenchmarkApprovedAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    readonly_fields = [field for field in Benchmark._meta.get_all_field_names() if field not in ('approved',)]
    fields = ('approved', 'name', 'owner', 'geographic_coverage', 'start_date', 'end_date', 'min_numbers_of_responses')

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
            return HttpResponseRedirect('/admin/bm/')
        else:
            return super(BenchmarkApprovedAdmin, self).response_change(request, obj)

    list_filter = ('start_date', 'owner')

admin.site.register(Benchmark, BenchmarkPendingAdmin)
admin.site.register(BenchmarkApproved, BenchmarkApprovedAdmin)
