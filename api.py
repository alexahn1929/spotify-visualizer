import requests
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
import pandas as pd
import numpy as np

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
savedToken = "PLACEHOLDER"

def getToken():
    response = requests.post(f"https://accounts.spotify.com/api/token?grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}", headers={"Content-Type": "application/x-www-form-urlencoded"})
    if response.status_code != 200:
        raise Exception("Could not obtain new access token")
    output = response.json()
    return output["access_token"]
print("Sample token:", getToken())

def getPlaylistAPIUrl(rawURL):
    HOSTNAME = "open.spotify.com"
    PATH_PREFIX = "/playlist/"

    playlistURL = urlparse(rawURL)

    if playlistURL.hostname != HOSTNAME or PATH_PREFIX not in playlistURL.path:
        raise Exception("Could not parse playlist ID from URL")
    
    playlistID = playlistURL.path[playlistURL.path.rindex("/")+1:]
    return f"https://api.spotify.com/v1/playlists/{playlistID}/tracks"
print("Sample playlist API URL:", getPlaylistAPIUrl("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=de0c34a3ac7549bf"))

def getPlaylist(apiURL):
    global savedToken
    response = requests.get(apiURL, headers={"Authorization": f"Bearer {savedToken}"})
    if response.status_code == 401: #expired token
        savedToken = getToken()
        return getPlaylist(apiURL)
    elif response.status_code == 403:
        raise Exception("Bad OAuth request")
    elif response.status_code == 429:
        raise Exception("Spotify API rate limit exceeded")
    return response.json()

def getPlaylistRaw(rawURL):
    apiURL = getPlaylistAPIUrl(rawURL)
    playlistJSON = getPlaylist(apiURL)
    songs = playlistJSON["items"]
    print(playlistJSON["next"])
    while playlistJSON["next"]:
        playlistJSON = getPlaylist(playlistJSON["next"])
        songs += playlistJSON["items"]
    return songs
sampleSongs = getPlaylistRaw("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=0767d59f3bb9499c")
print("Sample song array:", sampleSongs[0], len(sampleSongs))

'''
Generates a pd.DataFrame representing the tracks in the playlist and their IDs, href, names,
album (objects), artists, and duration.

:returns: a pandas DataFrame containing relevant track information in a given playlist
'''
def generate_playlist_df(rawURL):
    api_url = getPlaylistAPIUrl(rawURL)
    playlist_json = getPlaylist(api_url)
    #script for manipulating track data into a usable format, stored in a provisional dataframe
    track_list = playlist_json['items']
    if not track_list:
        #raise error, empty playlist
        pass
    playlist_df = pd.DataFrame()
    for t in track_list:
        track_info = t['track']
        album = track_info['album']
        href = track_info['href']
        t_id = track_info['id']
        name = track_info['name']
        artists = track_info['artists']
        duration = track_info['duration_ms']
        temp_arr = [t_id, href, name, album, artists, duration]

        temp_df = pd.DataFrame(data = temp_arr)
        playlist_df = pd.concat([playlist_df, temp_df], axis = 1)
    playlist_df = playlist_df.T
    playlist_df = playlist_df.rename(columns = {0: 'ID', 1:'href', 2:'Name', 3:'Album', 4:'Artists', 5:'Duration'}).reset_index()
    playlist_df = playlist_df.drop(columns = ['index'])
    return playlist_df
sample_df = generate_playlist_df("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=0767d59f3bb9499c")
print(sample_df)

def extract_audio_features(track_id):
    endpoint = f"https://api.spotify.com/v1/audio-features/{track_id}"
    global savedToken
    response = requests.get(endpoint, headers={"Authorization": f"Bearer {savedToken}"})
    if response.status_code == 401: #expired token
        savedToken = getToken()
        return extract_audio_features(track_id)
    elif response.status_code == 403:
        raise Exception("Bad OAuth request")
    elif response.status_code == 429:
        raise Exception("Spotify API rate limit exceeded")
    return response.json()

def append_audio_features(playlist_df):
    playlist_df['helper'] = playlist_df.apply(lambda row: extract_audio_features(row['ID']), axis=1)
    playlist_df['acousticness'] = playlist_df['helper']['acousticness']
    return playlist_df
print(append_audio_features(sample_df))