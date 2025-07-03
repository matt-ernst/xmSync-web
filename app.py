import requests
import json
import webbrowser
import spotipy
import sys, os, time
import msvcrt

from flask import Flask, render_template, request
from stations import stations
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from datetime import datetime
from stations import stations

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        station = request.form["station"]
        # Call your getSongLink() logic here, passing the selected station
        # result = ...
    return render_template("index.html", stations=stations, result=result)

if __name__ == "__main__":
    app.run(debug=True)
