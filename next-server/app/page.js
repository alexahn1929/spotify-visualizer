"use client"

import Image from 'next/image'
import styles from './page.module.css'
import "./globals.css"
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useState, useRef, useEffect } from "react";
//const data = null;//require("../../out.json")


export default function App() {
  const [hasPlaylist, setHasPlaylist] = useState(false);
  const [playlistJSON, setPlaylistJSON] = useState(null);

  function updateData(newJSON) {
    setHasPlaylist(true);
    setPlaylistJSON(newJSON);
  }

  let content = hasPlaylist ? <Plotify data={playlistJSON} /> : <Home onValidPlaylist={updateData} />;
  return (
    <main>
      <div onClick={() => setHasPlaylist(false)}>Plotify for Spotify</div>
      {content}
    </main>
  )
}

function Home({onValidPlaylist}) {
  const [errorMsg, setErrorMsg] = useState(""); // either playlist ID could not be parsed or could not get playlist from Spotify API

  function getPlaylist(link) {
    const HOSTNAME = "open.spotify.com";
    const PATH_PREFIX = "/playlist/";
    let playlistURL;
    try {
      playlistURL = new URL(link);
      if (playlistURL.hostname != HOSTNAME || !playlistURL.pathname.includes(PATH_PREFIX)) {
        throw new Error();
      }
    } catch {
      setErrorMsg("Could not parse a valid Spotify playlist ID.")
      return;
    }

    const playlistID = playlistURL.pathname.substring(playlistURL.pathname.lastIndexOf("/")+1);
    fetch(`http://localhost:5000/api/playlist/${playlistID}`).then((res) => {
      if (res.status !== 200) {
        return Promise.reject("Could not retrieve playlist from Spotify API.");
      }
      return res.json()
    })
      .catch((e) => setErrorMsg(e))
      .then((resJSON) => onValidPlaylist(resJSON));
  }
  function handleSubmit(event){
    event.preventDefault();
    getPlaylist(event.target.elements.playlistLink.value)
  }
  return (
    <main>
      <div>Paste your Spotify playlist link here!</div>
      <form onSubmit={handleSubmit}>
        <input name="playlistLink" type="text" placeholder="https://open.spotify.com/playlist/..." />
        <input type="submit" />
      </form>
      <div>{errorMsg}</div>
    </main>
  )
}

function Plotify({data}) { // data == json from backend
  const [selectedSong, setSelectedSong] = useState(0);
  const audioRef = useRef();
  const scale = 10;
  let points = []
  if (data !== null) {
    for (let i in data) {
      points.push((<mesh key={i} position={[data[i]["x"]*scale, data[i]["y"]*scale, data[i]["z"]*scale]} onClick={(e) => {
        e.stopPropagation();
        setSelectedSong(i);
      }}>
        <sphereGeometry args={[0.5]}/>
        {selectedSong == i ? (<meshStandardMaterial color="black"/>) : (<meshStandardMaterial color="lightblue"/>)}
      </mesh>));
    }
  }

  useEffect(() => {
    audioRef.current.volume = 0.02;
    audioRef.current.pause(); //is pause necessary to load next song?
    audioRef.current.load();
    audioRef.current.play();
  }, [selectedSong]);

  return (
    <div className={styles.main}>
      <Canvas className={styles.graph} camera={{ fov: 75, position: [-80, 0, 0]}}>
        <color attach="background" args={["lightgray"]} />
        <ambientLight intensity={1} />
        {points}
        <OrbitControls />
      </Canvas>
      <div className={styles.metadata}>
        <img src={data[selectedSong]["album_image"]} height={100} width={100} />
        <div className="title">
          {data[selectedSong]["name"]}
        </div>
        <div className="artist">
          {data[selectedSong]["artists"]}
        </div>
        <div className="album">
          {data[selectedSong]["album"]}
        </div>
        <audio controls src={data[selectedSong]["preview_url"]} ref={audioRef} />
      </div>
    </div>
  );
  //for orbitcontrols, play around with property target={points[selectedSong].position} (want to center cam around selection)
}