from django.shortcuts import redirect
from social.models import Profile, Company, LinkedInIndustry, Contact, Invite
from bm.models import Region
from social_auth.exceptions import StopPipeline, AuthFailed
from django.db.models import Count
from social.backend.linkedin import get_contacts


def beta_login(backend, details, request, response, uid, user, social_user=None, *args, **kwargs):
    allowed = Invite.objects.filter(email=response['email-address'], allowed=True).exists()
    invited = Contact.objects.filter(first_name=details['first_name'],
                                     last_name=details['last_name'])\
        .annotate(user_invites=Count('invites')).filter(user_invites__gt=0)
    if invited:
        return
    if not allowed:
        raise StopPipeline


def contacts_validation(backend, details, request, response, uid, user, social_user=None, *args, **kwargs):
    connections = get_contacts(tokens=response['access_token'])
    if connections is None or connections < 10:
        raise StopPipeline


def load_extra_data(backend, details,request, response, uid, user, social_user=None,
                    *args, **kwargs):
    """Load extra data from provider and store it on current UserSocialAuth
    extra_data field.

    """
    social_profile = Profile.objects.filter(user=user).first()
    social_contact = Contact.objects.filter(code=uid).first()
    if social_contact:
        social_contact.user = user
        social_contact.save()

    if not social_profile:
        social_profile = Profile()
        social_profile.user = user
        social_profile.save()
    social_profile.headline = response.get('headline')
    social_profile.industry = response.get('industry')
    location = Region.objects.filter(code=response.get('location', {}).get('country', {}).get('code')).first()
    if not location:
        location = Region()
        location.code = response.get('location', {}).get('country', {}).get('code')
        location.save()
    for position in response.get('positions').get('position'):
        if position == 'is-current' or (isinstance(position, dict) and
                                        position.get('is-current', '')):
            if isinstance(position, str):
                company = Company.objects.filter(name=position).first()
                position_company = {'name': position}
            else:
                position_company = position.get('company', {})
                if position_company.has_key('id'):
                    company = Company.objects.filter(code=position_company['id']).first()
                elif position_company.has_key('name'):
                    company = Company.objects.filter(name=position_company.get('name', None)).first()
                else:
                    continue

            if not company:
                company = Company()
                company.code = position_company.get('id', None)
                company.name = position_company.get('name', None)
                company.industry = LinkedInIndustry.objects.filter(name=response.get('industry', {})).first()
                company.save()
            social_profile.company = company
            break

    social_profile.location = location
    social_profile.save()
    return {'social_profile': social_profile}