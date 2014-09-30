from core.models import SystemKey
from core.forms import SystemKeysForm
from django.contrib import admin
from django.views.generic import FormView
from dbtemplates.models import Template
from dbtemplates.admin import TemplateAdmin, TemplateAdminForm


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

    #Remove delete_selected from actions for Dbtemplates app
    def get_actions(self, request):
        actions = super(SimplifiedTemplateAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

admin.site.unregister(Template)
admin.site.register(Template, SimplifiedTemplateAdmin)


class KeyGroupsListFilter(admin.SimpleListFilter):
    title = 'Key Groups'

    parameter_name = 'Third-Parties'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        groups = SystemKey.objects.distinct('key_group').all()
        return tuple((row.key_group, row.key_group)  for row in groups)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if not self.value():
            return queryset
        else:
            return queryset.filter(key_group=self.value())

class SystemKeysAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'System Key'

    form = SystemKeysForm
    list_display = ('key_name', )
    list_filter = (KeyGroupsListFilter,)

    field_groups = {}
    keys = SystemKey.objects.all()
    for key in keys:
        field_groups.setdefault(key.key_group, []).append(key.key_name)
    fields = ('key_name', '_payload', 'description')
#    fieldsets = tuple((grp, {'fields': ['key_name', '_payload', 'description']}) for grp in field_groups)

admin.site.register(SystemKey, SystemKeysAdmin)

