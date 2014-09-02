from dbtemplates.models import Template
from dbtemplates.admin import TemplateAdmin, TemplateAdminForm
from django.contrib import admin


class SimplifiedTemplateAdmin(TemplateAdmin):
    form = TemplateAdminForm
    fieldsets = (
        (None, {
            'fields': ('name', 'content'),
            'classes': ('monospace',),
        }),
        # Hide Advanced fields in Dbtemplates app admin
        # (('Advanced'), {
        #     'fields': (('sites'),),
        # }),
        (('Date/time'), {
            'fields': (('creation_date', 'last_changed'),),
            'classes': ('collapse',),
        }),
    )
    list_display = ('name', 'creation_date', 'last_changed')
    list_filter = ('creation_date',)
    save_as = True
    search_fields = ('name', 'content')
    actions = ['invalidate_cache', 'repopulate_cache', 'check_syntax']

admin.site.unregister(Template)
admin.site.register(Template, SimplifiedTemplateAdmin)


