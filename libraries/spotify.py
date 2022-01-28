import logging
import requests
from typing import Any, Dict
from base64 import b64encode

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


def get_access_token() -> Dict[str, Any]:
    """
    Get an access token from Spotify
    Send a POST request with user credentials to Spotify's OAuth endpoint
    """
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
        return response.json()
    except requests.RequestException as e:
        logging.error(f'Error while getting access token: {e}')
        return {}
