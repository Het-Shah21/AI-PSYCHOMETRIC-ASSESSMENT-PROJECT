"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Stars, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

function FloatingOrb({ position, color, speed = 1 }: { position: [number, number, number]; color: string; speed?: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.x += delta * 0.2 * speed;
      ref.current.rotation.y += delta * 0.3 * speed;
    }
  });
  return (
    <Float speed={speed * 2} rotationIntensity={0.5} floatIntensity={1}>
      <mesh ref={ref} position={position}>
        <sphereGeometry args={[0.4, 32, 32]} />
        <MeshDistortMaterial color={color} distort={0.3} speed={2} roughness={0.2} metalness={0.8} />
      </mesh>
    </Float>
  );
}

function PortalRing() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.z += delta * 0.5;
  });
  return (
    <mesh ref={ref} position={[0, 0, -3]}>
      <torusGeometry args={[2, 0.05, 16, 100]} />
      <meshStandardMaterial color="#7b2ff7" emissive="#7b2ff7" emissiveIntensity={2} transparent opacity={0.6} />
    </mesh>
  );
}

export default function BackgroundScene() {
  const orbs = useMemo(
    () => [
      { position: [-3, 2, -5] as [number, number, number], color: "#ff6b35" },
      { position: [3, -1, -4] as [number, number, number], color: "#7b2ff7" },
      { position: [0, 3, -6] as [number, number, number], color: "#06d6a0" },
      { position: [-2, -2, -3] as [number, number, number], color: "#118ab2" },
    ],
    []
  );

  return (
    <div className="fixed inset-0 -z-10">
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.5} />
        <Stars radius={100} depth={50} count={2000} factor={4} fade speed={1} />
        {orbs.map((orb, i) => (
          <FloatingOrb key={i} {...orb} speed={0.5 + i * 0.3} />
        ))}
        <PortalRing />
      </Canvas>
    </div>
  );
}
