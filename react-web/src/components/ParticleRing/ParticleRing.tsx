import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere } from '@react-three/drei';
import type { Group } from 'three';
import { pointsInner, pointsOuter, type RingPoint } from './utils';

/**
 * Decorative, non-interactive particle-ring background for the auth screens.
 * Sits absolutely behind the form card (pointerEvents: none) and auto-rotates
 * — no OrbitControls, so it never steals clicks/drags from the form.
 */
export function ParticleRing() {
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      <Canvas
        camera={{ position: [10, -7.5, -5], fov: 50 }}
        gl={{ alpha: true, antialias: true }}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={0.6} />
        <pointLight position={[-30, 0, -30]} intensity={12} color="#A78BFA" />
        <pointLight position={[20, 10, 10]} intensity={8} color="#06B6D4" />
        <PointCircle />
      </Canvas>
    </div>
  );
}

function PointCircle() {
  const ref = useRef<Group>(null);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.z = clock.getElapsedTime() * 0.06;
      ref.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.12) * 0.15;
    }
  });

  return (
    <group ref={ref}>
      {pointsInner.map((point) => (
        <Point key={point.idx} position={point.position} color={point.color} />
      ))}
      {pointsOuter.map((point) => (
        <Point key={point.idx} position={point.position} color={point.color} />
      ))}
    </group>
  );
}

function Point({ position, color }: Pick<RingPoint, 'position' | 'color'>) {
  return (
    <Sphere position={position} args={[0.09, 10, 10]}>
      <meshStandardMaterial emissive={color} emissiveIntensity={0.6} roughness={0.4} color={color} />
    </Sphere>
  );
}
