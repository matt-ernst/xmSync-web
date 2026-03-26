import os
import cloudscraper

from providers.spotify_provider import SpotifyProvider
from providers.amazon_provider import AmazonProvider
from providers.apple_provider import AppleProvider

from dotenv import load_dotenv
from stations import stations
from flask_cors import CORS
from flask import Flask, redirect, render_template, request, session, jsonify

load_dotenv()

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
            team_id=os.environ["APPLE_TEAM_ID"],
            key_id=os.environ["APPLE_KEY_ID"],
            private_key=os.environ["APPLE_PRIVATE_KEY"],
            redirect_uri=os.environ.get("REDIRECT_URI_APPLE", ""),
            session=session
        )

    raise ValueError(f"Unknown provider: {provider}")

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/login/<provider>")
def login(provider):
    if provider not in ("spotify", "apple", "amazon"):
        return "Unknown provider", 400

    provider_instance = get_provider_instance(provider)

    # Apple Music uses MusicKit JS — render a page instead of redirecting
    if provider == "apple":
        developer_token = provider_instance.authenticate()
        return render_template("apple_auth.html", developer_token=developer_token)

    login_url = provider_instance.authenticate()
    return redirect(login_url)

@app.route("/callback/apple", methods=["POST"])
def apple_callback():
    """Receives the Music User Token POSTed by MusicKit JS after user auth."""
    data = request.get_json(silent=True) or {}
    music_user_token = data.get("music_user_token")
    display_name = data.get("display_name") or "Apple Music User"

    if not music_user_token:
        return jsonify({"error": "No music_user_token provided"}), 400

    provider_instance = get_provider_instance("apple")
    provider_instance.authenticate(music_user_token)
    session["provider"] = "apple"
    session["display_name"] = display_name
    session["apple_display_name"] = display_name
    return jsonify({"success": True})

@app.route("/callback/<provider>")
def callback(provider):
    if provider not in ("spotify", "amazon"):
        return "Unknown provider", 400

    provider_instance = get_provider_instance(provider)
    code = request.args.get("code")

    if provider_instance.authenticate(code):
        session["provider"] = provider
        display_name = provider_instance.get_name()
        session["display_name"] = display_name
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
    data = request.get_json(silent=True) or {}
    station_id = data.get('station_id')

    if not station_id:
        return jsonify({'error': 'No station_id provided'}), 400

    access_token = session.get('access_token')
    if not access_token:
        return jsonify({'error': 'User not authenticated'}), 401

    provider_name = session.get('provider', 'spotify')
    song_info = getSongInfo(station_id)

    if not song_info:
        return jsonify({'song': None, 'error': 'No playable song found for this station.'}), 200

    last_uri = session.get('last_uri')
    new_song_added = False

    if song_info['URI'] != last_uri:
        try:
            provider_instance = get_provider_instance(provider_name)

            if provider_name == 'spotify':
                provider_instance.add_to_queue(song_info['URI'])

            elif provider_name == 'apple':
                apple_id = provider_instance.find_track(
                    song_info['Title'], song_info['Artist']
                )
                if apple_id:
                    provider_instance.add_to_queue(apple_id)
                    song_info['AppleID'] = apple_id
                else:
                    return jsonify({
                        'song': song_info,
                        'new_song_added': False,
                        'error': 'Track not found on Apple Music.'
                    }), 200

            elif provider_name == 'amazon':
                # Amazon Music does not expose a public queue API.
                # Return song info so the frontend can display what's playing.
                return jsonify({'song': song_info, 'new_song_added': False,
                                'error': 'Queue management is not supported for Amazon Music.'}), 200

            print(f"Added song to queue: {song_info['Title']} by {song_info['Artist']}")
            session['last_uri'] = song_info['URI']
            new_song_added = True

        except Exception as e:
            print(f'Error adding to queue: {e}')
            return jsonify({'song': song_info, 'new_song_added': False,
                            'error': 'Failed to add song to queue.'}), 500

    return jsonify({'song': song_info, 'new_song_added': new_song_added})


def getSongInfo(station_id):
    """Fetch the current track from xmplaylist.com for a given station ID.
    Returns a dict with URI (Spotify), Title, Artist, and Image, or None."""
    try:
        url = "https://xmplaylist.com/api/station/" + station_id
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        response = scraper.get(url, timeout=15)
        print(f"xmplaylist status: {response.status_code}, content-type: {response.headers.get('content-type')}")
        print(f"xmplaylist body (first 300 chars): {response.text[:300]}")
        response.raise_for_status()
        data = response.json()

        if (data and 'results' in data and data['results']
                and 'spotify' in data['results'][0]
                and 'track' in data['results'][0]):
            result = data['results'][0]
            song_info = {
                'URI': "spotify:track:" + result['spotify']['id'],
                'Title': result['track']['title'],
                'Artist': result['track']['artists'][0],
                'Image': result['spotify']['albumImageLarge'],
            }
            print(f"Found song: {song_info['Title']} by {song_info['Artist']}")
            return song_info

        print("No playable song found for this station.")
        return None

    except Exception as e:
        print(f"Error fetching song for station {station_id}: {e}")
        return None


# Keep old name as an alias for backwards compatibility
def getSongLink(station_id):
    return getSongInfo(station_id)

if __name__ == "__main__":
    app.run(port=8888, debug=True)