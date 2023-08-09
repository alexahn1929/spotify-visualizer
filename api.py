import requests
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
import pandas as pd
import numpy as np
import json
import pickle

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

def makeAPIRequest(apiURL):
    global savedToken
    response = requests.get(apiURL, headers={"Authorization": f"Bearer {savedToken}"})
    if response.status_code == 401: #expired token
        savedToken = getToken()
        return makeAPIRequest(apiURL)
    elif response.status_code == 403:
        raise Exception("Bad OAuth request")
    elif response.status_code == 429:
        raise Exception("Spotify API rate limit exceeded")
    # data = response.json()
    # with open('data.json', 'w') as f:
    #     json.dump(data, f)
    return response.json()

def getAudioFeatures(songs): #can take 100 songs max, returns array of song audio features in order
    songIdsCommaSeparated = ",".join([song["id"] for song in songs])
    return makeAPIRequest(f"https://api.spotify.com/v1/audio-features?ids={songIdsCommaSeparated}")["audio_features"]


def getPlaylistRaw(rawURL):
    playlistJSON = makeAPIRequest(getPlaylistAPIUrl(rawURL))
    songs = [song["track"] for song in playlistJSON["items"]]
    for i, features in enumerate(getAudioFeatures(songs)):
        songs[i]["audio_features"] = features
    while playlistJSON["next"]:
        playlistJSON = makeAPIRequest(playlistJSON["next"])
        songsToAppend = [song["track"] for song in playlistJSON["items"]]
        for i, features in enumerate(getAudioFeatures(songsToAppend)):
            playlistJSON["items"][i]["audio_features"] = features
        songs += playlistJSON["items"]
    return songs
# sampleSongs = getPlaylistRaw("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=0767d59f3bb9499c")
# with open('data.obj', 'wb') as fileObj:
#     pickle.dump(sampleSongs, fileObj)
# print("Sample song structure:", sampleSongs[0], len(sampleSongs))
# print()
# print(sampleSongs[-1])



'''
Generates a pd.DataFrame representing the tracks in the playlist and their IDs, href, names,
album (objects), artists, and duration.

:returns: a pandas DataFrame containing relevant track information in a given playlist
'''
def generate_playlist_df(rawURL):
    #script for manipulating track data into a usable format, stored in a provisional dataframe
    track_list = getPlaylistRaw(rawURL)
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
# sample_df = generate_playlist_df("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=0767d59f3bb9499c")
# print(sample_df)


def getDf(songs):
    df = pd.DataFrame(songs)
    metadata = df[["album", "artists", "id", "name", "preview_url"]]

    features = df["audio_features"].apply(pd.Series)[["acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "speechiness", "valence"]] #drop any NaNs, and drop rows when concatting at end
    #features = features.dropna() #some songs, ie. new ones, will not have this data in the API yet
    keepRows = features.notna().all(axis=1)
    features = features[keepRows]
    metadata = metadata[keepRows]

    features = features.apply(lambda col: (col - col.mean()) / col.std())
    data = np.array(features)
    covariance = np.matmul(np.transpose(data), data)
    eigenvalues, eigenvectors = np.linalg.eig(covariance)
    print(features)
    print()
    print(data)
    print()
    print(covariance)
    print()
    print(eigenvalues)
    print()
    print(eigenvectors)
    return data

fileObj = open('data.obj', 'rb')
songsSaved = pickle.load(fileObj)
fileObj.close()
getDf(songsSaved)