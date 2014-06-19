from __future__ import absolute_import
from linkedin import linkedin
import collections
from app import settings

UserAccess = collections.namedtuple('UserToken', ['token', 'token_secret'])


def extract_access_tokens(access_tokens):
    return UserAccess(access_tokens['oauth_token'], access_tokens['oauth_token_secret'])


def get_contacts(user):
    auth = user.social_auth.first()
    user_access = extract_access_tokens(auth.tokens)
    authentication = linkedin.LinkedInDeveloperAuthentication(
        settings.LINKEDIN_CONSUMER_KEY,
        settings.LINKEDIN_CONSUMER_SECRET,
        user_access.token,
        user_access.token_secret,
        ''
    )
    application = linkedin.LinkedInApplication(authentication)
    connections = application.get_connections(selectors=['id', 'first-name', 'last-name', 'industry', 'location', 'headline', 'positions'])
    return connections['values']
