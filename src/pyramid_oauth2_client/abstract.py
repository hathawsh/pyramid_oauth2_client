
from base64 import urlsafe_b64encode
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from urllib import urlencode
from urlparse import parse_qs
from urlparse import urljoin
import json
import os
import requests
import time


class AbstractOAuth2Client(object):
    """Base for an OAuth2 client library."""

    def __init__(self, request,
            settings_prefix='oauth2.',
            session_prefix='oauth2.',
            callback_path='@@oauth2callback'):
        self.request = request
        self.settings_prefix = settings_prefix
        self.session_prefix = session_prefix
        self.callback_path = callback_path

    def get_userid(self, access_token):
        """Abstract method: get the user ID represented by the access token."""
        raise NotImplementedError("Override this method")

    def get_access_token(self):
        return self.request.session[self.session_prefix + 'access_token']

    def login(self, came_from=None):
        """Redirect to the OAuth2 server for login."""
        request = self.request
        if came_from is None:
            came_from = request.params.get('came_from')
        request.session[self.session_prefix + 'came_from'] = came_from

        settings = request.registry.settings
        authorize_url = settings[self.settings_prefix + 'authorize_url']
        client_id = settings[self.settings_prefix + 'client_id']
        redirect_uri = urljoin(request.application_url, self.callback_path)
        state = urlsafe_b64encode(os.urandom(16))
        request.session[self.session_prefix + 'state'] = state

        q = urlencode([
            ('client_id', client_id),
            ('redirect_uri', redirect_uri),
            ('state', state),
            ('response_type', 'code'),
        ])
        location = '{0}?{1}'.format(authorize_url, q)
        headers = [('Cache-Control', 'no-cache')]
        return HTTPFound(location=location, headers=headers)

    def callback(self):
        """Receive an authorization code and log in the user.
        """
        request = self.request
        code = request.params.get('code')
        state = request.params.get('state')
        if not code or not state:
            return HTTPBadRequest("Missing code or state parameters")

        session = request.session
        session_state = session.get(self.session_prefix + 'state')
        if session_state != state:
            # CSRF protection
            return HTTPBadRequest(body="Incorrect state value")

        self.prepare_access_token(code)

        userid = self.get_userid()
        if userid:
            remember(request, userid)

        location = session.get(self.session_prefix + 'came_from')
        if not location:
            location = request.application_url
        headers = [('Cache-Control', 'no-cache')]
        return HTTPFound(location=location, headers=headers)

    def prepare_access_token(self, code):
        """Use an authorization code to get an access token.

        Puts access_token and possibly refresh_at in the session.
        """
        request = self.request
        settings = request.registry.settings
        session = request.session

        token_url = settings[self.settings_prefix + 'token_url']
        client_id = settings[self.settings_prefix + 'client_id']
        client_secret = settings[self.settings_prefix + 'client_secret']

        redirect_uri = urljoin(request.application_url, '@@oauth2callback')
        verify = token_url.startswith('https')
        r = requests.post(token_url, auth=(client_id, client_secret), data={
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code,
            # Facebook requires POST parameters and ignores basic auth.
            'client_id': client_id,
            'client_secret': client_secret,
        }, verify=verify)
        r.raise_for_status()
        if r.headers.get('content-type').startswith('application/json'):
            token_response = json.loads(r.content)
        else:
            # Facebook's variation
            token_response = parse_qs(r.content)
        access_token = token_response['access_token']
        session[self.session_prefix + 'access_token'] = access_token

        # Possibly put a refresh_at value in the session.
        refresh_interval = int(request.registry.settings.get(
            self.settings_prefix + 'refresh_interval', 0))
        if not refresh_interval:
            expires_in = float(token_response.get('expires_in', 0))
            if not expires_in:
                # Facebook's variation
                expires_in = float(token_response.get('expires', 0))
            if expires_in:
                refresh_interval = expires_in / 2

        refresh_at_key = self.session_prefix + 'refresh_at'
        if refresh_interval:
            refresh_at = int(time.time() + refresh_interval)
            session[refresh_at_key] = refresh_at
        elif refresh_at_key in session:
            del session[refresh_at_key]

    def refresh(self):
        """If it is time to do so, refresh the access token."""
        request = self.request
        if request.method != 'GET':
            # Don't redirect on POST and other special HTTP request methods.
            return None

        refresh_at = request.session.get(self.session_prefix + 'refresh_at')
        if refresh_at and time.time() >= refresh_at:
            return self.login(came_from=request.url)
        else:
            return None
