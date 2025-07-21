# spotify_provider.py

import requests
import urllib.parse
import uuid
import base64
import spotipy
import os 
from .base import MusicProvider

class SpotifyProvider(MusicProvider):
    AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    
    def __init__(self, client_id, client_secret, redirect_uri, session):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.session = session
        self.access_token = session.get('access_token')

    def add_to_queue(self, song_uri):
        if not self.access_token:
            raise Exception("User not authenticated")
        endpoint = "https://api.spotify.com/v1/me/player/queue"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'uri': song_uri}
        response = requests.post(endpoint, headers=headers, params=params)

        if response.status_code not in [201, 204]:
            raise Exception(f"Failed to add song to queue: " + response.text)
        
    def get_name(self):
        access_token = self.session.get('access_token')
        if not access_token:
            return None
        
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        if response.status_code == 200:
            return response.json().get('display_name', 'Unknown User')

        else:
            print(f"Failed to get user info: {response.status_code} - {response.text}")
            return None

    def authenticate(self, code=None):
        if code is None:
            params ={
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': 'user-modify-playback-state',
                'state': str(uuid.uuid4()),
                'show_dialog': 'true'
            }

            url = f"{self.AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
            return url
        
        else:
            client_creds = f"{self.client_id}:{self.client_secret}"
            encoded_creds = base64.b64encode(client_creds.encode()).decode()
            
            payload = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri
            }
            
            headers = {
                'Authorization': f'Basic {encoded_creds}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(self.TOKEN_URL, data=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.session['access_token'] = self.access_token
                return True
            else:
                print("Spotify authentication failed:", response.text)
                return False
