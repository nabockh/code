from django.contrib import admin
from bm.admin import ReadOnlyAdminMixin

# Register your models here.
from social.models import Invite


class InviteAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    readonly_fields = ('email',)
    list_filter = ('allowed',)

admin.site.register(Invite, InviteAdmin)