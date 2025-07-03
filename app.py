import uuid
import urllib
from flask import Flask, redirect, render_template

app = Flask(__name__)

@app.route("/")
def index():
    print("Index route called")

    return render_template("index.html")

@app.route("/login")
def login():
    authentication_request_params = {
        'response_type': 'code',
        'client_id': "5313474a55be44d4acfdae1423805b70",
        'redirect_uri': "http://127.0.0.1:8888",
        'scope': 'openid email profile',
        'scope': 'user-modify-playback-state',
        'state': str(uuid.uuid4()),
        'show_dialog': 'true'
    }
    
    return True

if __name__ == "__main__":
    app.run(debug=True)