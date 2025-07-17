import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

# code that clones spotify playlists to a new playlist called 'Saved Weekly'
# ONLY WORKS WITH USER-CREATED PLAYLISTS

# https://open.spotify.com/playlist/60a6sFmz8YWf1IOHdguePR?si=aQSpa8TfTwqj_thZr1ylMA
# "Chill" playlist used for testing
# Only parts between 'playlist/' and '?' needed for discover_playlist_id

#TO DO: Change variable names to better reflect their role as the copy/paste playlists respectfully.

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = '1234567890'
TOKEN_INFO = 'token_info'

#default app route.
#tries to authenticate user using Spotify's OAuth.
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

#redirects here and attempts to re-authenticate the user
@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_discover_weekly', _external=True))

#main app route
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():

    try:
        token_info = get_token() #authentication attempt
    except:
        print('User not logged in')
        return redirect('http://127.0.0.1:5000/redirect')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    #Variable instantiation
    current_playlists = sp.current_user_playlists()['items']
    saved_weekly_playlist_id = None
    discover_weekly_playlist_id = None
    discover_weekly_playlist = None

    #Loop to iterate through the playlist to be copied as well as
    #The playlist to be copied into.
    for playlist in current_playlists:
        print(playlist['name'])
        if (playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
        # insert playlist name to be saved to new playlist
        if (playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']

    #In the case that the playlist you're attempting to copy from doesn't exist.
    if not discover_weekly_playlist_id:
        return ('Discover Weekly not found')

    #in the case that there is no Saved Weekly playlist yet
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']

    #Copying the tracks over
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    sp.user_playlist_add_tracks(
        user_id, saved_weekly_playlist_id, song_uris, None)

    return ('Discover Weekly songs added successfully') #Success!

#Obligatory token expiration block (Can't stay logged in forever, bucko)
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())

    #Refreshes your token for you
    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(
            token_info['refresh_token'])

    return token_info

#User Info
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="####",
        client_secret="####",
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private'
    )


app.run(debug=True)


