# providers/amazon_provider.py
#
# Amazon Music integration using Login with Amazon (LWA) OAuth 2.0.
#
# Required environment variables:
#   AMAZON_CLIENT_ID      — LWA application Client ID
#   AMAZON_CLIENT_SECRET  — LWA application Client Secret
#   REDIRECT_URI_AMAZON   — e.g. http://127.0.0.1:8888/callback/amazon
#
# Setup:
#   1. Sign in to https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html
#   2. Create a Security Profile.
#   3. Note Client ID and Client Secret.
#   4. Add your redirect URI under "Allowed Return URLs".
#
# Note on queue support:
#   Amazon Music does not publish a public REST API for queue management.
#   This provider fully implements authentication and user profile retrieval.
#   add_to_queue() raises NotImplementedError to reflect this limitation;
#   future Amazon Music API access (if/when available) can be added here.

import uuid
import urllib.parse
import requests
from typing import Optional

from .base import MusicProvider


class AmazonProvider(MusicProvider):
    AUTHORIZE_URL = "https://www.amazon.com/ap/oa"
    TOKEN_URL = "https://api.amazon.com/auth/o2/token"
    PROFILE_URL = "https://api.amazon.com/user/profile"

    # Scopes available via LWA:
    #   profile          — name, user_id, email
    #   postal_code      — zip/postal code
    SCOPES = "profile"

    def __init__(self, client_id: str, client_secret: str,
                 redirect_uri: str, session):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.session = session

    # ------------------------------------------------------------------
    # MusicProvider interface
    # ------------------------------------------------------------------

    def authenticate(self, code: Optional[str] = None):
        """
        Without a code: builds and returns the LWA authorization URL to
        redirect the user to.

        With a code (from the OAuth callback): exchanges it for an access
        token, stores it in the session, and returns True on success.
        """
        if code is None:
            state = str(uuid.uuid4())
            self.session["amazon_oauth_state"] = state

            params = {
                "client_id": self.client_id,
                "scope": self.SCOPES,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "state": state,
            }
            return f"{self.AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

        # Exchange authorization code for tokens
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(
            self.TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            self.session["access_token"] = access_token
            self.session["amazon_refresh_token"] = refresh_token
            return True

        print(f"Amazon authentication failed: {response.status_code} {response.text}")
        return False

    def get_name(self) -> str:
        """Fetch the user's display name from the Amazon profile API."""
        access_token = self.session.get("access_token")
        if not access_token:
            return "Amazon Music User"

        response = requests.get(
            self.PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("name") or "Amazon Music User"

        print(f"Amazon get_name failed: {response.status_code} {response.text}")
        return "Amazon Music User"

    def add_to_queue(self, song_uri: str):
        """
        Amazon Music does not expose a public REST API for queue management.
        This method is provided as a stub for future implementation.
        """
        raise NotImplementedError(
            "Amazon Music does not provide a public queue API. "
            "Queue management is not supported for this provider."
        )

    # ------------------------------------------------------------------
    # Token refresh helper
    # ------------------------------------------------------------------

    def refresh_access_token(self) -> bool:
        """Exchange the stored refresh token for a new access token."""
        refresh_token = self.session.get("amazon_refresh_token")
        if not refresh_token:
            return False

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(
            self.TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if response.status_code == 200:
            self.session["access_token"] = response.json().get("access_token")
            return True

        print(f"Amazon token refresh failed: {response.status_code} {response.text}")
        return False

    def find_track(self, title: str, artist: str) -> Optional[str]:
        """
        Placeholder — Amazon Music catalog search is not publicly available.
        Returns None to indicate the track could not be resolved.
        """
        return None
