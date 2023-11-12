# BACKEND API: Run with "flask --app api run"

import requests
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, Response, abort
from flask_cors import CORS
from markupsafe import escape
import pickle
import tabloo
# from urllib.parse import urlparse

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
# print("Sample token:", getToken())

# def getPlaylistAPIUrl(rawURL):
#     HOSTNAME = "open.spotify.com"
#     PATH_PREFIX = "/playlist/"

#     playlistURL = urlparse(rawURL)

#     if playlistURL.hostname != HOSTNAME or PATH_PREFIX not in playlistURL.path:
#         raise Exception("Could not parse playlist ID from URL")
    
#     playlistID = playlistURL.path[playlistURL.path.rindex("/")+1:]
#     return f"https://api.spotify.com/v1/playlists/{playlistID}/tracks"

# print("Sample playlist API URL:", getPlaylistAPIUrl("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=de0c34a3ac7549bf"))

def makeAPIRequest(apiURL):
    global savedToken
    response = requests.get(apiURL, headers={"Authorization": f"Bearer {savedToken}"})
    if response.status_code == 401: #expired token
        savedToken = getToken()
        return makeAPIRequest(apiURL)
    elif response.status_code == 403:
        raise Exception("Bad OAuth request")
    elif response.status_code == 404:
        raise Exception("Invalid playlist ID")
    elif response.status_code == 429:
        raise Exception("Spotify API rate limit exceeded")
    return response.json()

def getAudioFeatures(songs): #can take 100 songs max, returns array of song audio features in order
    songIdsCommaSeparated = ",".join([song["id"] for song in songs])
    return makeAPIRequest(f"https://api.spotify.com/v1/audio-features?ids={songIdsCommaSeparated}")["audio_features"]

def getPlaylist(playlistID):
    playlistJSON = makeAPIRequest(f"https://api.spotify.com/v1/playlists/{playlistID}/tracks")
    songs = [song["track"] for song in playlistJSON["items"] if song["track"]["id"]] # local files will not have a song id and must be removed
    for i, features in enumerate(getAudioFeatures(songs)):
        songs[i]["audio_features"] = features
    while playlistJSON["next"]:
        playlistJSON = makeAPIRequest(playlistJSON["next"])
        songsToAppend = [song["track"] for song in playlistJSON["items"] if song["track"]["id"]]
        for i, features in enumerate(getAudioFeatures(songsToAppend)):
            songsToAppend[i]["audio_features"] = features
        songs += songsToAppend
    return songs
# sampleSongs = getPlaylist("https://open.spotify.com/playlist/1ID56tk92tPTeIJ5jH8aUb?si=571fdb006e8244a2")
# with open('summer22.obj', 'wb') as fileObj:
#     pickle.dump(sampleSongs, fileObj)
# print("Sample song structure:", sampleSongs[0], len(sampleSongs))
# print()
# print(sampleSongs[-1])

app = Flask(__name__)
CORS(app)

@app.route("/api/playlist/<playlistID>")
def getDf(playlistID):
    try:
        songs = getPlaylist(escape(playlistID))
    except Exception as e:
        abort(404, e)
    
    df = pd.DataFrame(songs)
    df = df[df["name"].ne("")] # old songs that have been deleted from spotify still have some data associated with them - this is a makeshift fix
    df["album_image"] = df["album"].apply(lambda x: x["images"][0]["url"]) # could use [-1] to save bandwidth
    df["album"] = df["album"].apply(lambda x: x["name"])
    df["artists"] = df["artists"].apply(lambda x: ", ".join([artist["name"] for artist in x]))
    # tabloo.show(df) # df viewable in browser at localhost:5000
    metadata = df[["album", "album_image", "artists", "id", "name", "preview_url"]]
    features = df["audio_features"].apply(pd.Series)[["acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "speechiness", "valence"]] # double check -- could add popularity, maybe remove some?
    keepRows = features.notna().all(axis=1) # drop any song for which features were not acquired
    features = features[keepRows].reset_index(drop=True)
    metadata = metadata[keepRows].reset_index(drop=True)

    features = features.apply(lambda col: (col - col.mean()) / col.std())
    data = np.array(features)
    covariance = np.cov(data, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eig(covariance)
    order_of_importance = np.argsort(eigenvalues)[::-1] # high to low
    sorted_eigenvectors = eigenvectors[:,order_of_importance] # sort the columns

    k = 3 # select the number of principal components
    reduced_data = pd.DataFrame(np.matmul(data, sorted_eigenvectors[:,:k]), columns=["x", "y", "z"]) # transform the original data
    processed_data = pd.concat([metadata, reduced_data], axis=1)
    # tabloo.show(processed_data)
    
    # explained_variance = sorted_eigenvalues / np.sum(sorted_eigenvalues)
    # cumulative_variance = np.cumsum(explained_variance)

    # # Plot scree plot from PCA
    # x_labels = ['PC{}'.format(i+1) for i in range(len(explained_variance))]

    # plt.plot(x_labels, explained_variance, marker='o', markersize=6, color='skyblue', linewidth=2, label='Proportion of variance')
    # plt.plot(x_labels, cumulative_variance, marker='o', color='orange', linewidth=2, label="Cumulative variance")
    # plt.legend()
    # plt.title('Scree plot')
    # plt.xlabel('Principal components')
    # plt.ylabel('Proportion of variance')
    # plt.show()
    
    return Response(processed_data.to_json(orient="index"), mimetype="application/json")

# fileObj = open('summer22.obj', 'rb')
# songsSaved = pickle.load(fileObj)
# fileObj.close()
# getDf(songsSaved)

# getDf("1ID56tk92tPTeIJ5jH8aUb") # output