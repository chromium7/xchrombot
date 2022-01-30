import json
import logging
import requests
from base64 import b64encode
from datetime import datetime, timedelta
from typing import Any, Dict
from urllib.parse import urlencode, urljoin

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
from core.objects import Song


BASE_URL = 'https://api.spotify.com/v1/me/'
TOKEN_URL = 'https://accounts.spotify.com/api/token'


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
        'redirect_uri': SPOTIFY_REDIRECT_URI,
    }
    return url + urlencode(parameter)


def get_json_headers() -> Dict[str, Any]:
    """
    Get the headers required to make a request to Spotify's API
    """
    token = get_access_token()
    headers = {
        'Authorization': f'{token["token_type"]} {token["access_token"]}',
        'Content-Type': 'application/json'
    }
    return headers


def get_form_headers() -> Dict[str, Any]:
    """
    Get the headers required to request/refresh access token
    """
    return {
        'Authorization': 'Basic {}'.format(
            b64encode(
                '{}:{}'.format(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET).encode('utf-8')
            ).decode('utf-8')
        ),
        'Content-Type': 'application/x-www-form-urlencoded'
    }


def get_authorization_access_token(code: str) -> Dict[str, Any]:
    """
    Get access token from Spotify after authorization
    """
    now = datetime.now()
    headers = get_form_headers()
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
    }
    try:
        # 10 seconds timeout
        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)
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


def get_access_token() -> str:
    now = datetime.now()
    try:
        with open('spotify.json', 'r') as f:
            access_token: Dict = json.load(f)
            expires_at = datetime.fromtimestamp(access_token.get('expires_at', 0))
            # Check if access token is still valid
            if expires_at > now:
                return access_token
    except (json.JSONDecodeError, FileNotFoundError):
        raise Exception('Spotify access token has not been configured properly.')
    # Refresh token if expired
    return refresh_access_token(access_token['refresh_token'])


def refresh_access_token(refresh_token: str) -> str:
    now = datetime.now()
    headers = get_form_headers()
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=5)
        response.raise_for_status()
        data = response.json()
        data['expires_at'] = (now + timedelta(seconds=data['expires_in'])).timestamp()
        data['refresh_token'] = refresh_token
        # Update access token
        with open('spotify.json', 'w') as f:
            json.dump(data, f)
        return data
    except requests.RequestException as e:
        logging.error(f'Error while refreshing access token: {e}')
        return {}


def get_currently_playing() -> Song:
    url = urljoin(BASE_URL, 'player/currently-playing')
    headers = get_json_headers()
    try:
        response = requests.get(url, headers=headers, timeout=2)
        # No currently playing song
        if response.status_code != 200:
            return {}
    except requests.RequestException as e:
        logging.error(f'Error while getting currently playing song: {e}')
        return {}
    data = response.json()
    context = data['context']
    item = data['item']
    return Song(
        id=item['id'],
        name=item['name'],
        artists=", ".join([artist['name'] for artist in item['artists']]),
        duration=item['duration_ms'],
        track_url=item['external_urls']['spotify'],
        is_playing=data['is_playing'],
        context_type=context['type'],
        context_url=context['external_urls']['spotify'],
    )
