from uuid import uuid4
from django.shortcuts import redirect
from social.models import Profile, Company, LinkedInIndustry, Contact, Invite
from bm.models import Region, BenchmarkInvitation
from social_auth.exceptions import StopPipeline, AuthFailed
from django.db.models import Count
from social.backend.linkedin import get_contacts
from social_auth.backends.pipeline.user import create_user
from social_auth.utils import setting, module_member
from social_auth.models import UserSocialAuth
from django.contrib.auth.models import User
from core.utils import celery_log, logger

slugify = module_member(setting('SOCIAL_AUTH_SLUGIFY_FUNCTION',
                                'django.template.defaultfilters.slugify'))



def get_username(details, user=None,
                 user_exists=UserSocialAuth.simple_user_exists,
                 *args, **kwargs):
    """Return an username for new user. Return current user username
    if user was given.
    """
    if user:
        return {'username': UserSocialAuth.user_username(user)}

    email_as_username = setting('SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL', False)
    uuid_length = setting('SOCIAL_AUTH_UUID_LENGTH', 16)
    do_slugify = setting('SOCIAL_AUTH_SLUGIFY_USERNAMES', False)

    old_user = User.objects.filter(email=details.get('email')).first()
    if old_user:
        final_username = old_user.username
        return {'username': final_username,
                'user': old_user}
    if email_as_username and details.get('email'):
        username = details['email']
    elif details.get('username'):
        username = unicode(details['username'])
    else:
        username = uuid4().get_hex()

    max_length = UserSocialAuth.username_max_length()
    short_username = username[:max_length - uuid_length]
    final_username = UserSocialAuth.clean_username(username[:max_length])
    if do_slugify:
        final_username = slugify(final_username)

    # Generate a unique username for current user using username
    # as base but adding a unique hash at the end. Original
    # username is cut to avoid any field max_length.
    while user_exists(username=final_username):
        username = short_username + uuid4().get_hex()[:uuid_length]
        username = username[:max_length]
        final_username = UserSocialAuth.clean_username(username)
        if do_slugify:
            final_username = slugify(final_username)
    return {'username': final_username}


def beta_login(backend, details, request, response, uid, user, social_user=None, *args, **kwargs):
    allowed = Invite.objects.filter(email=response['email-address'], allowed=True).exists()
    invited = Contact.objects.filter(first_name=details['first_name'],
                                     last_name=details['last_name'])\
        .annotate(user_invites=Count('invites')).filter(user_invites__gt=0)

    if invited.exists():
        return

    forwarded_invites = BenchmarkInvitation.user_friendly_invites(details['first_name'],
                                                                  details['last_name'])
    if not allowed and len([x for x in forwarded_invites]) == 0:
        raise StopPipeline


def contacts_validation(backend, details, request, response, uid, user, social_user=None, *args, **kwargs):
    connections = get_contacts(tokens=response['access_token'])
    if connections is None or len(connections) < 10:
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
        social_contact.email = user.email
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
    if response.get('positions'):
        for position in response.get('positions', {}).get('position', []):
            if position == 'is-current' or (isinstance(position, dict) and
                                            position.get('is-current', '')):
                try:
                    if isinstance(response.get('positions', {}).get('position', {}), list):
                        position_company = response.get('positions', {}).get('position', {})[0].get('company', {})
                        if position_company.has_key('id'):
                            company = Company.objects.filter(code=position_company['id']).first()
                        elif position_company.has_key('name'):
                            company = Company.objects.filter(name=position_company.get('name', None)).first()
                    elif response.get('positions', {}).get('position', {}).has_key('company'):
                        position_company = response.get('positions', {}).get('position', {}).get('company', {})
                        if position_company.has_key('id'):
                            company = Company.objects.filter(code=position_company['id']).first()
                        elif position_company.has_key('name'):
                            company = Company.objects.filter(name=position_company.get('name', None)).first()
                        else:
                            continue
                    elif isinstance(position, str):
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
                except:
                    logger.exception('Reponse error: %s' % response)
                    raise
                social_profile.company = company
                break
    elif response.get('industry'):
        company = Company.objects.filter(code=None, name=response.get('industry')).first()
        if not company:
            company = Company()
            company.code = None
            company.name = response.get('industry')
            company.industry = LinkedInIndustry.objects.filter(name=response.get('industry', {})).first()
            company.save()
        social_profile.company = company
    social_profile.location = location
    social_profile.save()
    return {'social_profile': social_profile}