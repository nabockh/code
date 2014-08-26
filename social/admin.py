from django.contrib import admin

# Register your models here.
from social.models import Invite
from social.signals import invitee_approved


def allow_email(modeladmin, request, queryset):
    queryset.update(allowed=True)
    invitee_approved.send(sender=None, request=request, user=request.user, queryset=queryset)
allow_email.short_description = "Allow selected emails"


class InviteAdmin(admin.ModelAdmin):
    list_filter = ('allowed',)
    actions = [allow_email]

admin.site.register(Invite, InviteAdmin)