"use client"

import Image from 'next/image'
import styles from './page.module.css'
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
const data = require("../../out.json")

export default function Home() {
  const scale = 10;
  let points = []
  for (let i in data) {
    points.push((<mesh position={[data[i]["x"]*scale, data[i]["y"]*scale, data[i]["z"]*scale]}>
      <sphereGeometry args={[0.5]}/>
      <meshStandardMaterial color="hotpink" />
    </mesh>));
  }
  return (
    <main className={styles.main}>
      <Canvas camera={{ fov: 75, position: [-80, 0, 0]}}>
        <pointLight position={[10, 10, 10]} />
        <ambientLight intensity={8} />
        {points}
        <OrbitControls />
      </Canvas>
    </main>
  )
}
