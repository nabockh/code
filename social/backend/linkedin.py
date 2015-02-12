from __future__ import absolute_import
import json
import logging
from linkedin import linkedin
from linkedin.exceptions import LinkedInError
import collections
from app import settings
from linkedin.utils import raise_for_error

UserAccess = collections.namedtuple('UserToken', ['token', 'token_secret'])


class LinkedInApplication(linkedin.LinkedInApplication):

    def send_message(self, subject, body, recipients):
        data = {
            'recipients': {
                'values': []
            },
            'subject': subject,
            'body': body,
        }
        for recipient in recipients:
            data['recipients']['values'].append({'person': {'_path': '/people/' + recipient}})
        url = '%s/~/mailbox' % linkedin.ENDPOINTS.PEOPLE
        response = self.make_request('POST', url,
                                     data=json.dumps(data))
        raise_for_error(response)
        return True



def extract_access_tokens(access_tokens):
    return UserAccess(access_tokens['oauth_token'], access_tokens['oauth_token_secret'])


def get_contacts(user=None, tokens=None):
    if tokens:
        oauth_token_secret = tokens.split('&')[0].split('=')[1]
        oauth_token = tokens.split('&')[1].split('=')[1]
        access_tokens = {'oauth_token': oauth_token, 'oauth_token_secret': oauth_token_secret}
        user_access = extract_access_tokens(access_tokens)
        authentication = linkedin.LinkedInDeveloperAuthentication(
            settings.LINKEDIN_CONSUMER_KEY,
            settings.LINKEDIN_CONSUMER_SECRET,
            user_access.token,
            user_access.token_secret,
            ''
        )
        application = linkedin.LinkedInApplication(authentication)
        try:
            connections = application.get_connections(selectors=['id', 'first-name', 'last-name', 'industry', 'location', 'headline', 'positions'])
        except LinkedInError as e:
            logging.exception('LinkedIn auth error for user "%s": %s' % (user and user.username, e))
            connections = {}
        if connections.has_key('_total') and connections['_total'] != 0:
            return connections['values']
        else:
            return None
    auth = user.social_auth.first()
    if not auth:
        return []
    user_access = extract_access_tokens(auth.tokens)
    authentication = linkedin.LinkedInDeveloperAuthentication(
        settings.LINKEDIN_CONSUMER_KEY,
        settings.LINKEDIN_CONSUMER_SECRET,
        user_access.token,
        user_access.token_secret,
        ''
    )
    application = linkedin.LinkedInApplication(authentication)
    try:
        connections = application.get_connections(selectors=['id', 'first-name', 'last-name', 'industry', 'location', 'headline', 'positions'])
    except LinkedInError as e:
        logging.exception('LinkedIn auth error for user "%s": %s' % (user.username, e))
        connections = {}
    if connections.has_key('_total') and connections['_total'] != 0:
        return connections['values']
    else:
        return []
