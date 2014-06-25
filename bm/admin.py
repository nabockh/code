from django.contrib import admin

# Register your models here.
from bm.models import Benchmark


class BenchmarkPendingAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super(BenchmarkPendingAdmin, self).get_queryset(Benchmark)
        return qs.filter(approved=False)

    list_filter = ('start_date', 'owner')


class BenchmarkApproved(Benchmark):

    class Meta:
        proxy = True
        verbose_name = 'Approved Benchmark'


class BenchmarkApprovedAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super(BenchmarkApprovedAdmin, self).get_queryset(Benchmark)
        return qs.filter(approved=True)

    list_filter = ('start_date', 'owner')

admin.site.register(Benchmark, BenchmarkPendingAdmin)
admin.site.register(BenchmarkApproved, BenchmarkApprovedAdmin)
