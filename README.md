# Welcome to xmSync!

xmSync is an open-source project that bridges the gap between SiriusXM’s distinctive music curation and modern streaming platforms like Spotify. Inspired by the unique variety found on stations such as John Mayer Radio, xmSync empowers users to bring that same diversity to their Spotify queue—even if they can’t access SiriusXM directly.
What is xmSync?

## xmSync is a web and script-based application that:

* Automatically adds currently playing and newly discovered tracks from a SiriusXM station to your Spotify queue.
* Can be run via a Python script in a separate repository, from a web interface, or hosted locally.
* Is fully open source, allowing anyone to contribute or customize the project.

## Why xmSync?

The project was inspired by the realization that SiriusXM’s John Mayer Radio station offered a richer, more interesting mix than Spotify’s built-in radio. xmSync was created to provide everyone with access to that level of music variety, regardless of their SiriusXM subscription status.
Key Features

* Automatic Queueing: Seamlessly syncs SiriusXM tracks to your Spotify queue in real time.
* Flexible Deployment: Use xmSync as a web app, run it locally, or execute the Python script—whatever fits your workflow.
* Open Source: Freely available for customization, contribution, and self-hosting.
* Future-Ready: Plans to support other platforms like Apple Music and YouTube Music.

## Technical Highlights

* Python for backend logic and scripting
* Flask for the web application framework
* JavaScript, HTML, and CSS for a user-friendly interface

## Requirements
* Spotify Premium
* Users of [xmsync.com](https://xmsync.com) have to be whitelisted, if you would like to be added please send me your email address at [matt@xmsync.com](mailto:matt@xmsync.com), otherwise, continue reading for the instructions to host your own version locally.

## The Road Ahead

xmSync aims to become a universal bridge between the best of curated radio and the convenience of streaming. Future updates will expand support to additional platforms, ensuring that more listeners can enjoy a richer, more varied music experience—no matter where or how they listen.

---

# Want to Host Locally? Way Cool!

Due to [Spotify's April 15th, 2025 API limitations](https://developer.spotify.com/blog/2025-04-15-updating-the-criteria-for-web-api-extended-access), currently it is not possible to increase your Spotify Application User quota without being a registered organization, and without having >250k active users. My original vision was to host the website for it to be accessible to everyone, but that is not possible unless Spotify goes back on their API changes. I highly encourage anyone to host their own instance, instructions below.

## 1.) Clone the Repository in your IDE or Terminal
* Navigate to a convienent folder
* Clone the project, `git clone https://github.com/matt-ernst/xmSync-web.git`

## 2.) Create a Spotify Developer Application, Obtain Spotify API Keys
* Visit the [Spotify Developer Dashboard](https://developer.spotify.com)
* Log in with your Spotify account
* Create a new application
* Note down your Client ID and Client Secret
* `http://127.0.0.1:8888/callback/spotify` can be your Redirect URI
* Users of your application can be added here (max of 25), the owner is automatically given permission. 

## 3.) Supply Credentials in Environment File
* Create a .env file in the script directory
  
  ```
  FLASK_SECRET=your_flask_secret_key
  SPOTIFY_CLIENT_ID=your_spotify_client_id
  SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
  REDIRECT_URI_SPOTIFY = http://127.0.0.1:8888/callback/spotify  
  ```

## 4.) Install Project Dependencies
* Navigate to the *xmSync-web* directory `cd xmSync-web`
* Install the requirements, `pip install -r requirements.txt`
* Run the app.py file, `python app.py`

## 5.) Get Started
* Navigate to `http://127.0.0.1:8888/`
* Login! You're set!

