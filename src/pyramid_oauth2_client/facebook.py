
from pyramid_oauth2_client.abstract import AbstractOAuth2Client
import json
import requests


class FacebookClient(AbstractOAuth2Client):
    """OAuth2 client for Facebook."""

    def get_userid(self):
        access_token = self.get_access_token()
        me_url = 'https://graph.facebook.com/me'
        r = requests.get(me_url, params={'access_token': access_token},
            verify=True)
        r.raise_for_status()
        userinfo_response = json.loads(r.content)
        userid = userinfo_response['id']
        return userid
