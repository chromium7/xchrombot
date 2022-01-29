import json
import logging
import requests
from base64 import b64encode
from datetime import datetime, timedelta
from typing import Any, Dict
from urllib.parse import urlencode

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


BASE_URL = 'https://api.spotify.com/v1/'


def get_authorization_url() -> str:
    """
    Get URL for user to give access of their spotify account
    to our application.
    """
    # More on scope: https://developer.spotify.com/documentation/general/guides/authorization/scopes/
    scope = [
        'user-read-playback-state',
        'user-modify-playback-state',
        'user-read-currently-playing',
        'user-read-recently-played',
    ]
    url = 'https://accounts.spotify.com/authorize?'
    parameter = {
        'client_id': SPOTIFY_CLIENT_ID,
        'scope': ' '.join(scope),
        'response_type': 'code',
        # TODO: create this API endpoint
        'redirect_uri': 'http://127.0.0.1:8001/api/spotify/redirect',
    }
    return url + urlencode(parameter)


def get_headers() -> Dict[str, Any]:
    """
    Get the headers required to make a request to Spotify's API
    """
    token = get_access_token()
    headers = {
        'Authorization': f'{token["token_type"]} {token["access_token"]}',
        'Content-Type': 'application/json'
    }
    return headers


def get_access_token() -> Dict[str, Any]:
    """
    Get an access token from Spotify
    Send a POST request with user credentials to Spotify's OAuth endpoint
    """
    now = datetime.now()
    try:
        with open('spotify.json', 'r') as f:
            access_token: Dict = json.load(f)
            expires_at = datetime.fromtimestamp(access_token.get('expires_at', 0))
            # Check if access token is still valid
            if expires_at > now:
                return access_token
    except (json.JSONDecodeError, FileNotFoundError):
        pass

    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic {}'.format(
            b64encode(
                '{}:{}'.format(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET).encode('utf-8')
            ).decode('utf-8')
        ),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    try:
        # 10 seconds timeout
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        data = response.json()
        data['expires_at'] = (now + timedelta(seconds=data['expires_in'])).timestamp()
        # Write access token to file
        with open('spotify.json', 'w') as f:
            json.dump(data, f)
        return data
    except requests.RequestException as e:
        logging.error(f'Error while getting access token: {e}')
        return {}
