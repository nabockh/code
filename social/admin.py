from django.contrib import admin

# Register your models here.
from social.models import Invite
from social.signals import invitee_approved


def allow_email(modeladmin, request, queryset):
    for invite in queryset:
        if not invite.allowed:
            invite.allowed = True
            invite.save()
allow_email.short_description = "Allow selected emails"


class InviteAdmin(admin.ModelAdmin):
    list_filter = ('allowed',)
    actions = [allow_email]

admin.site.register(Invite, InviteAdmin)