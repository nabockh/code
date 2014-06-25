from __future__ import absolute_import
import json
from linkedin import linkedin
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
