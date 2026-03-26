# providers/apple_provider.py
#
# Apple Music integration using MusicKit.
#
# Required environment variables:
#   APPLE_TEAM_ID       — Your 10-character Apple Developer Team ID
#   APPLE_KEY_ID        — The Key ID from your MusicKit identifier
#   APPLE_PRIVATE_KEY   — Contents of the .p8 private key file (newlines as \n)
#   REDIRECT_URI_APPLE  — Unused for MusicKit JS flow, kept for consistency
#
# Auth flow:
#   1. Server generates a short-lived developer JWT with _generate_developer_token().
#   2. The JWT is injected into apple_auth.html, which loads MusicKit JS.
#   3. MusicKit JS prompts the user and returns a Music User Token.
#   4. The frontend POSTs that token to /callback/apple (handled in app.py).
#   5. The server stores the Music User Token in the Flask session.
#
# Queue / search:
#   Apple Music has no REST "add to queue" endpoint — queuing is client-side
#   via MusicKit JS.  add_to_queue() here adds the track to the user's Library
#   (the closest server-side equivalent).  For real-time queuing the frontend
#   should call MusicKit.getInstance().playLater() with the Apple Music ID
#   returned by find_track().

import time
import requests
import jwt as pyjwt
from typing import Optional

from .base import MusicProvider


class AppleProvider(MusicProvider):
    API_BASE = "https://api.music.apple.com/v1"

    def __init__(self, team_id: str, key_id: str, private_key: str,
                 redirect_uri: str, session):
        self.team_id = team_id
        self.key_id = key_id
        # Accept both raw PEM text and escaped \n-delimited strings from .env
        self.private_key = private_key.replace("\\n", "\n")
        self.redirect_uri = redirect_uri
        self.session = session

    # ------------------------------------------------------------------
    # Developer token (server-side JWT, valid up to 6 months)
    # ------------------------------------------------------------------

    def _generate_developer_token(self) -> str:
        now = int(time.time())
        payload = {
            "iss": self.team_id,
            "iat": now,
            "exp": now + 15_777_000,   # ~6 months, Apple's maximum
        }
        return pyjwt.encode(
            payload,
            self.private_key,
            algorithm="ES256",
            headers={"kid": self.key_id},
        )

    # ------------------------------------------------------------------
    # MusicProvider interface
    # ------------------------------------------------------------------

    def authenticate(self, music_user_token: Optional[str] = None):
        """
        Without a token: returns the developer JWT so apple_auth.html can
        initialise MusicKit JS.

        With a token (POSTed from the frontend after MusicKit JS auth):
        stores it in the session and returns True.
        """
        if music_user_token is None:
            return self._generate_developer_token()

        self.session["apple_music_user_token"] = music_user_token
        self.session["access_token"] = music_user_token
        return True

    def get_name(self) -> str:
        return self.session.get("apple_display_name") or "Apple Music User"

    def add_to_queue(self, apple_music_id: str) -> dict:
        """
        Adds a track to the user's Apple Music library.
        (Apple does not expose a REST queue endpoint; use MusicKit JS for
        real-time queuing on the client side.)

        Returns the full track object on success, raises on failure.
        """
        music_user_token = self.session.get("apple_music_user_token")
        if not music_user_token:
            raise Exception("Apple Music user not authenticated")

        url = f"{self.API_BASE}/me/library"
        headers = self._auth_headers(music_user_token)
        params = {"ids[songs]": apple_music_id}

        response = requests.post(url, headers=headers, params=params)
        if response.status_code not in (200, 201, 202, 204):
            raise Exception(
                f"Apple Music add_to_library failed "
                f"({response.status_code}): {response.text}"
            )
        return {"apple_music_id": apple_music_id, "added": True}

    # ------------------------------------------------------------------
    # Catalog search helpers
    # ------------------------------------------------------------------

    def find_track(self, title: str, artist: str,
                   storefront: str = "us") -> Optional[str]:
        """
        Search the Apple Music catalog for a song and return its catalog ID,
        or None if not found.
        """
        url = f"{self.API_BASE}/catalog/{storefront}/search"
        headers = self._auth_headers()
        params = {
            "term": f"{title} {artist}",
            "types": "songs",
            "limit": 1,
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(
                f"Apple Music search failed "
                f"({response.status_code}): {response.text}"
            )
            return None

        songs = (
            response.json()
            .get("results", {})
            .get("songs", {})
            .get("data", [])
        )
        return songs[0]["id"] if songs else None

    def get_track(self, apple_music_id: str,
                  storefront: str = "us") -> Optional[dict]:
        """Fetch full track details by catalog ID."""
        url = f"{self.API_BASE}/catalog/{storefront}/songs/{apple_music_id}"
        response = requests.get(url, headers=self._auth_headers())
        if response.status_code == 200:
            data = response.json().get("data", [])
            return data[0] if data else None
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_headers(self, music_user_token: Optional[str] = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self._generate_developer_token()}",
            "Content-Type": "application/json",
        }
        if music_user_token:
            headers["Music-User-Token"] = music_user_token
        return headers
