from django.contrib import admin

# Register your models here.
from social.models import Invite


class InviteAdmin(admin.ModelAdmin):
    list_filter = ('allowed',)

admin.site.register(Invite, InviteAdmin)