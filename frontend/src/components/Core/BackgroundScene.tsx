import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Environment } from '@react-three/drei';
import * as THREE from 'three';

// Generate a random sphere of points for the neural network effect
const generateParticles = (count: number, radius: number) => {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const r = radius * Math.cbrt(Math.random());
    const theta = Math.random() * 2 * Math.PI;
    const phi = Math.acos(2 * Math.random() - 1);
    
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = r * Math.cos(phi);
  }
  return positions;
};

const particlePositions = generateParticles(3000, 15);

function NeuralNetworkParticles() {
  const ref = useRef<THREE.Points>(null!);

  useFrame((_state, delta) => {
    ref.current.rotation.x -= delta / 10;
    ref.current.rotation.y -= delta / 15;
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={particlePositions} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#3b82f6"
          size={0.05}
          sizeAttenuation={true}
          depthWrite={false}
          opacity={0.6}
        />
      </Points>
    </group>
  );
}

export default function BackgroundScene() {
  return (
    <div className="absolute inset-0 z-[-1] pointer-events-none">
      <Canvas camera={{ position: [0, 0, 10] }} dpr={[1, 1.5]}>
        <ambientLight intensity={0.5} />
        <NeuralNetworkParticles />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}
