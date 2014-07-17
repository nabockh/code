from django.shortcuts import redirect
from social.models import Profile, Company, LinkedInIndustry, Contact
from bm.models import Region


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
    for item in response.get('positions').get('position'):
        if type(item) == dict:
            if item['is-current']:
                company = Company.objects.filter(code=response['positions'].get('position', {})[0].get('company').get('id')).first()
                if not company:
                    company = Company()
                    company.code = response['positions'].get('position', {})[0].get('company').get('id',{})
                    company.name = response['positions'].get('position', {})[0].get('company').get('name', {})
                    company.industry = LinkedInIndustry.objects.filter(name=response.get('industry', {})).first()
                    company.save()
                social_profile.company = company
                break
        elif type(item) == str:
            if item == "is-current":
                company = Company.objects.filter(code=response['positions'].get('position').get('company', {}).get('id')).first()
                if not company:
                    company = Company()
                    company.code = response['positions'].get('position', {}).get('company', {}).get('id', {})
                    company.name = response['positions'].get('position', {}).get('company', {}).get('name', {})
                    company.industry = LinkedInIndustry.objects.filter(name=response.get('industry', {})).first()
                    company.save()
                social_profile.company = company
                break
    social_profile.location = location
    social_profile.save()
    return {'social_profile': social_profile}