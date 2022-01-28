# Twitch credentials
# https://dev.twitch.tv/docs/irc
TWITCH_OAUTH_TOKEN = ""
TWITCH_USERNAME = ""

# Spotify credentials
# https://developer.spotify.com/documentation/web-api/quick-start/
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""


try:
    from config_local import *
except ImportError:
    pass
