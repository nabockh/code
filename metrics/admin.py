from django.conf.urls import patterns
from django.contrib import admin
from django.core.urlresolvers import RegexURLPattern
from metrics.models import Event
from metrics.utils import queryset_to_excel


def export_to_excel(modeladmin, request, queryset):
    return queryset_to_excel(queryset)
export_to_excel.short_description = "Export to Excel"


def export_to_excel_all(request, *args, **kwargs):
    queryset = Event.objects.all()
    return queryset_to_excel(queryset)
# export_to_excel_all.short_description = "Export All to Excel"


class EventAdmin(admin.ModelAdmin):
    change_list_template = 'metrics/admin/change_list.html'
    list_display = ('user', 'type', 'object', 'date')
    list_filter = ('type', 'user', 'date')
    fields = ('type', 'user')

    actions = [export_to_excel]

    def get_urls(self):
        urls = super(EventAdmin, self).get_urls()
        my_urls = patterns('',
            # (r'^excel$', export_to_excel_all),
            RegexURLPattern(r'^excel$', export_to_excel_all, name='metrics_event_excel'),
        )
        return my_urls + urls

admin.site.register(Event, EventAdmin)
