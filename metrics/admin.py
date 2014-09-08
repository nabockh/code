from django.contrib import admin
from metrics.models import Event
from metrics.utils import queryset_to_excel


def export_to_excel(modeladmin, request, queryset):
    return queryset_to_excel(queryset)
export_to_excel.short_description = "Export to Excel"


def export_to_excel_all(modeladmin, request, queryset):
    queryset = Event.objects.all()
    return queryset_to_excel(queryset)
export_to_excel_all.short_description = "Export All to Excel"


class EventAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'object', 'date')
    list_filter = ('type', 'user', 'date')
    fields = ('type', 'user')

    actions = [export_to_excel, export_to_excel_all]

admin.site.register(Event, EventAdmin)
