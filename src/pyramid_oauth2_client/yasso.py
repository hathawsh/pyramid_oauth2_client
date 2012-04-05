
from pyramid_oauth2_client.abstract import AbstractOAuth2Client
import json
import requests


class YassoClient(AbstractOAuth2Client):
    """OAuth2 client for a Yasso server."""

    def get_userid(self):
        access_token = self.get_access_token()
        userinfo_url = self.request.registry.settings['yasso.userinfo_url']
        verify = userinfo_url.startswith('https')
        r = requests.post(userinfo_url, data={'access_token': access_token},
            verify=verify)
        r.raise_for_status()
        userinfo_response = json.loads(r.content)
        userid = userinfo_response['userid']
        return userid
