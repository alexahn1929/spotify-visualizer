const url = require("node:url");

let savedToken = "PLACEHOLDER";
let CLIENT_ID = "";
let CLIENT_SECRET = "";

const getToken = async () => {
    const options = {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        }
    };

    let res = await fetch(`https://accounts.spotify.com/api/token?grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}`, options);
    if (res.status != 200) {
        throw new Error("Could not obtain new access token");
    }
    let output = await res.json();
    return output.access_token;
};

const getPlaylistAPIUrl = (link) => { //NOTE: move to renderer? to know if url should be sent prior to message passing
    const HOSTNAME = "open.spotify.com";
    const PATH_PREFIX = "/playlist/";
    
    const playlistURL = url.parse(link);

    if (playlistURL.hostname != HOSTNAME || !playlistURL.pathname.includes(PATH_PREFIX)) {
        throw new Error("Could not parse playlist ID from URL");
    }

    const playlistID = playlistURL.pathname.substring(playlistURL.pathname.lastIndexOf("/")+1);
    return `https://api.spotify.com/v1/playlists/${playlistID}/tracks`;
};

const getPlaylist = async (apiURL) => {
    const options = {
        headers: {"Authorization": `Bearer ${savedToken}`}
    };
    let res = await fetch(apiURL, options);
    if (res.status == 401) { //expired token
        savedToken = await getToken();
        return getPlaylist(apiURL);
    } else if (res.status == 403) {
        throw new Error("Bad OAuth request");
    } else if (res.status == 429) {
        throw new Error("API rate limit exceeded");
    }
    return res.json();
};

module.exports = {
    getPlaylistRaw: async (rawURL) => {
        let apiURL = getPlaylistAPIUrl(rawURL);
        let playlistJSON = await getPlaylist(apiURL);
        let songs = playlistJSON.items;
        while (playlistJSON.next !== null) {
            playlistJSON = await getPlaylist(playlistJSON.next);
            songs = songs.concat(playlistJSON.items);
        }
        return songs;
    },
    updateKey: (settings) => {
        CLIENT_ID = settings.client_id;
        CLIENT_SECRET = settings.client_secret;
    }
}

/*getPlaylistRaw("https://open.spotify.com/playlist/3AFvuS9t4qLhaaLBHRcSqk?si=0b8e8e8e9d1447ad").then(c => {
    console.log(c)
    console.log(c.length)
})*/