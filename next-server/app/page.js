"use client"

import Image from 'next/image'
import styles from './page.module.css'
import "./globals.css"
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useState, useRef, useEffect } from "react";
const data = require("../../out.json")

export default function App() {
  const [selectedSong, setSelectedSong] = useState(0);
  const audioRef = useRef();
  const scale = 10;
  let points = []
  for (let i in data) {
    points.push((<mesh key={i} position={[data[i]["x"]*scale, data[i]["y"]*scale, data[i]["z"]*scale]} onClick={(e) => {
      e.stopPropagation();
      setSelectedSong(i);
    }}>
      <sphereGeometry args={[0.5]}/>
      {selectedSong == i ? (<meshStandardMaterial color="black"/>) : (<meshStandardMaterial color="lightblue"/>)}
    </mesh>));
  }

  useEffect(() => {
    audioRef.current.volume = 0.02;
    audioRef.current.pause();
    audioRef.current.load();
    audioRef.current.play();
  }, [selectedSong]);

  return (
    <main className={styles.main}>
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
    </main>
  );
  //for orbitcontrols, play around with property target={points[selectedSong].position} (want to center cam around selection)
}
