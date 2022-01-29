# Setting up Spotify

## Credentials set up

1.  Create `spotify.json` file in the base directory
2.  Go to this page https://developer.spotify.com/dashboard
3.  Create a new application in spotify
4.  Add `http://127.0.0.1:8001/spotify/redirect` as `Redirect URI`
5.  Store `Client ID`, `Client Secret` and `Redirect URI` in config_local.py 
as `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` and `SPOTIFY_REDIRECT_URI` respectively

Since we will be using the authorization code flow of `OAuth 2.0`, 
user needs to login to the app that we just created.

## Authorizing the app

To login your spotify account to the app, run the following script through shell:

```sh
python libraries/app.py
```

Then, open the following site in the browser, and click the link to connect your
spotify account.

> http://127.0.0.1:8001/


More on this:

> https://developer.spotify.com/documentation/general/guides/authorization/code-flow/
