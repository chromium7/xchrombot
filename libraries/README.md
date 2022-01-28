# Setting up Spotify

1.  Go to this page https://developer.spotify.com/dashboard
2.  Create a new application in spotify
3.  Store Client ID and Client Secret in config_local.py

Since we are not using a web server, we will go with the `client credentials` option of `OAuth 2.0` which means that only endpoints that do not access user information can be accessed.

More on this:

> https://developer.spotify.com/documentation/general/guides/authorization/client-credentials/
