import os
import uuid
import base64
import urllib.parse

from dotenv import load_dotenv
import requests
from flask import Flask, redirect, render_template, request, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")
SPOTIFY_CLIENT_ID = "5313474a55be44d4acfdae1423805b70"
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET") 
REDIRECT_URI = "http://127.0.0.1:8888/callback"

@app.route("/")
def index():
    display_name = session.get('display_name')

    return render_template("index.html", display_name=display_name)

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

    # Fetch user profile
    user_profile_url = "https://api.spotify.com/v1/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get(user_profile_url, headers=headers)
    if user_response.status_code != 200:
        return "Failed to get user info", 400
    user_info = user_response.json()
    display_name = user_info.get('display_name', 'Spotify User')

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

if __name__ == "__main__":
    app.run(port=8888, debug=True)