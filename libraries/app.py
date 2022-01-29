import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from flask import Flask, request

from libraries import spotify

app = Flask(__name__)


STYLE = (
    "display: block;"
    "text-align: center;"
    "margin-top: 20px;"
)

@app.route('/', methods=['GET'])
def index() -> str:
    url = spotify.get_authorization_url()
    return f'<a href={url} style="{STYLE}">Connect spotify account</href>'


@app.route('/spotify/redirect', methods=['GET'])
def spotify_redirect() -> str:
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return error

    spotify.get_authorization_access_token(code)
    app.logger.info('Successfully saved access token')
    return f'<div style="{STYLE}">Your spotify account has been successfully registered!</div>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001)
