import os
import uuid
import base64
import urllib.parse

from dotenv import load_dotenv
from stations import stations
import requests
from flask import Flask, redirect, render_template, request, session, jsonify
import spotipy

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")

def format_display_name(key):
    return key.replace('_', ' ').title()

station_options = [
    {"display": key, "value": value}
    for key, value in stations.items()
]

@app.route("/")
def index():
    display_name = session.get('display_name')

    return render_template("index.html", display_name=display_name)

@app.route("/dashboard")
def dashboard():
    display_name = session.get('display_name')
    return render_template("dashboard.html", display_name=display_name, station_options=station_options)

@app.route("/login")
def login():
    authentication_request_params = {
        'response_type': 'code',
        'client_id': SPOTIFY_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'user-modify-playback-state',
        'state': str(uuid.uuid4()),
        'show_dialog': 'true'
    }
    
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(authentication_request_params)

    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if not code:
        return "No code provided", 400

    # Exchange code for access token
    token_url = "https://accounts.spotify.com/api/token"
    client_creds = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded_creds = base64.b64encode(client_creds.encode()).decode()
    
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }

    headers = {
        'Authorization': f'Basic {encoded_creds}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        return f"Failed to get access token: {response.text}", 400
    token_info = response.json()
    access_token = token_info.get('access_token')

    # Store access token in session for later API calls
    session['access_token'] = access_token

    # Fetch user profile
    user_profile_url = "https://api.spotify.com/v1/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get(user_profile_url, headers=headers)

    if user_response.status_code != 200:
        return "Failed to get user info", 400
    
    user_info = user_response.json()
    display_name = user_info.get('display_name', 'Spotify User')
    spotify_session = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=REDIRECT_URI))
    print(spotify_session)

    # Store display name in session
    session['display_name'] = display_name

    return redirect("/")

@app.route("/logout")
def logout():
    session.pop('display_name', None)
    return redirect("/")

@app.route("/about")
def about():
    display_name = session.get('display_name')
    return render_template("about.html", display_name=display_name)

@app.route("/contact")
def contact():
    display_name = session.get('display_name')
    return render_template("contact.html", display_name=display_name)

@app.route("/index")
def home():
    display_name = session.get('display_name')
    return render_template("index.html", display_name=display_name)

@app.route('/poll_station', methods=['POST'])
def poll_station():
    print("Polling station for new song...")
    data = request.get_json()
    station_id = data.get('station_id')
    if not station_id:
        return jsonify({'error': 'No station_id provided'}), 400

    access_token = session.get('access_token')
    if not access_token:
        return jsonify({'error': 'User not authenticated'}), 401

    sp = spotipy.Spotify(auth=access_token)
    song_info = getSongLink(station_id)
    if not song_info:
        return jsonify({'error': 'No song found'}), 404

    last_uri = session.get('last_uri')
    new_song_added = False

    if song_info['URI'] != last_uri:
        try:
            sp.add_to_queue(song_info['URI'])
            print(f"Added song to queue: {song_info['Title']} by {song_info['Artist']}")
            session['last_uri'] = song_info['URI']
            print(session['last_uri'])
            new_song_added = True
        except Exception as e:
            print(f'Error adding to queue: {e}')

    return jsonify({'song': song_info, 'new_song_added': new_song_added})

def get_spotify_client():
    access_token = session.get('access_token')
    if not access_token:
        return None
    return spotipy.Spotify(auth=access_token)

def getSongLink(station_id):
    try:
        url = "https://xmplaylist.com/api/station/" + station_id
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    
        #Validates That There is a Playable Song
        if (data and 'results' in data and data['results'] and 'spotify' in data['results'][0] and 'track' in data['results'][0]):
            spotify_uri = {
                'URI': "spotify:track:" + data['results'][0]['spotify']['id'],
                'Title': data['results'][0]['track']['title'],
                'Artist': data['results'][0]['track']['artists'][0],
                'Image': data['results'][0]['spotify']['albumImageLarge']
            }

            icon = {
                'src': spotify_uri['Image'],
                'placement': 'appLogoOverride'
            }

            print(f"Found song: {spotify_uri['Title']} by {spotify_uri['Artist']}")            

            return spotify_uri
    
        else:
            return None
    
    except:
        print("An error occurred while fetching the song.")
        return None

    return spotify_uri


if __name__ == "__main__":
    app.run(port=8888, debug=True)