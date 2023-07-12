import requests
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

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