import os
import uuid
import base64
import urllib.parse
import requests
import spotipy

from providers.spotify_provider import SpotifyProvider
#from providers.amazon_provider import AmazonProvider
#from providers.apple_provider import AppleProvider

from dotenv import load_dotenv
from stations import stations
from flask_cors import CORS
from flask import Flask, redirect, render_template, request, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET")
CORS(app)

def get_provider_instance(provider):
    if provider == "spotify":
        return SpotifyProvider(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=os.environ["REDIRECT_URI_SPOTIFY"],
            session=session
        )
    
    if provider == "amazon":
        return AmazonProvider(
            client_id=os.environ["AMAZON_CLIENT_ID"],
            client_secret=os.environ["AMAZON_CLIENT_SECRET"],
            redirect_uri=os.environ["REDIRECT_URI_AMAZON"],
            session=session
        )
    
    if provider == "apple":
        return AppleProvider(
            client_id=os.environ["APPLE_CLIENT_ID"],
            client_secret=os.environ["APPLE_CLIENT_SECRET"],
            redirect_uri=os.environ["REDIRECT_URI_APPLE"],
            session=session
        )
    
    raise Exception(f"Unknown provider: {provider}")

@app.route("/login/<provider>")
def login(provider):
    provider_instance = get_provider_instance(provider)
    login_url = provider_instance.authenticate()
    return redirect(login_url)

@app.route("/callback/<provider>")
def callback(provider):
    provider_instance = get_provider_instance(provider)
    code = request.args.get('code')

    if provider_instance.authenticate(code):
        session['provider'] = provider
        display_name = provider_instance.get_name()
        session['display_name'] = display_name
        return redirect("/")
    else:
        return "Authentication failed", 400

@app.route("/")
def index():
    display_name = session.get('display_name')
    return render_template("index.html", display_name=display_name)

@app.route("/dashboard")
def dashboard():
    display_name = session.get('display_name')
    station_options = [
        {"display": key, "value": value}
        for key, value in stations.items()
    ]
    return render_template("dashboard.html", display_name=display_name, station_options=station_options)

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
        return jsonify({'error': song_info}), 404

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


def getSongLink(station_id):
    try:
        url = "https://xmplaylist.com/api/station/" + station_id
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text[:300]}")
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
            print("No playable song found for this station.")
            return jsonify({'error': 'No playable song found for this station.'})
    
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching the song.'})

if __name__ == "__main__":
    app.run(port=8888, debug=True)