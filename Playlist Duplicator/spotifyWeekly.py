import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

# code that clones spotify playlists to a new playlist called 'Saved Weekly'
# ONLY WORKS WITH USER-CREATED PLAYLISTS

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = '1234567890'
TOKEN_INFO = 'token_info'


@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_discover_weekly', _external=True))


@app.route('/saveDiscoverWeekly')
def save_discover_weekly():

    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect('http://127.0.0.1:5000/redirect')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    current_playlists = sp.current_user_playlists()['items']
    saved_weekly_playlist_id = None
    discover_weekly_playlist_id = None
    discover_weekly_playlist = None

    for playlist in current_playlists:
        print(playlist['name'])
        if (playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
        # insert playlist name to be saved to new playlist
        if (playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        return ('Discover Weekly not found')

    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']

    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    sp.user_playlist_add_tracks(
        user_id, saved_weekly_playlist_id, song_uris, None)

    return ('Discover Weekly songs added successfully')


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(
            token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="8aebf28a90e043cda6e31fae7761ef53",
        client_secret="81621808c20c4f45b0aaa428664a518f",
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private'
    )


app.run(debug=True)

# https://open.spotify.com/playlist/60a6sFmz8YWf1IOHdguePR?si=aQSpa8TfTwqj_thZr1ylMA
# Chill playlist used for testing
# Only parts between 'playlist/' and '?' needed for discover_playlist_id
