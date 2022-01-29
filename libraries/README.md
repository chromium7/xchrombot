# Setting up Spotify

1.  Go to this page https://developer.spotify.com/dashboard
2.  Create a new application in spotify
3.  Store Client ID and Client Secret in config_local.py
4.  Add `redirect uri`

Since we will be using the authorization code flow of `OAuth 2.0`,
which require user to login to the app we just created.

To login your spotify account to the app, open up `python` 
and put in the following code to get the login URL:

```py
from libraries.spotify import get_authorization_url
print(get_authorization_url())
```

More on this:

> https://developer.spotify.com/documentation/general/guides/authorization/code-flow/
