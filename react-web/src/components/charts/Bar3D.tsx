import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import type { NameValue } from '@shared/types';

const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];
const MAX_BAR_HEIGHT = 3;

function Bar({ x, height, color, name, value }: { x: number; height: number; color: string; name: string; value: number }) {
  return (
    <group position={[x, 0, 0]}>
      <mesh position={[0, height / 2, 0]}>
        <boxGeometry args={[0.8, height, 0.8]} />
        <meshStandardMaterial color={color} roughness={0.35} metalness={0.1} />
      </mesh>
      <Html position={[0, height + 0.35, 0]} center distanceFactor={10} occlude={false}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#0F172A', whiteSpace: 'nowrap', pointerEvents: 'none' }}>
          {value.toLocaleString()}
        </div>
      </Html>
      <Html position={[0, -0.4, 0]} center distanceFactor={10} occlude={false}>
        <div style={{ fontSize: 11, color: '#64748B', whiteSpace: 'nowrap', maxWidth: 90, textAlign: 'center', pointerEvents: 'none' }}>
          {name}
        </div>
      </Html>
    </group>
  );
}

/** Real, interactive 3D bar chart — drag to orbit, scroll to zoom. */
export function Bar3D({ data }: { data: NameValue[] }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No data yet.</p>;
  }

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const spacing = 1.6;
  const totalWidth = (data.length - 1) * spacing;

  return (
    <div style={{ height: 320, borderRadius: 'var(--radius-md)', overflow: 'hidden', background: 'linear-gradient(180deg, #F8FAFC, #EEF2FF)' }}>
      <Canvas camera={{ position: [totalWidth / 2 + 3, 5, 9], fov: 50 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[5, 8, 5]} intensity={0.8} />
        <pointLight position={[-5, 3, -5]} intensity={0.3} color="#8B5CF6" />
        {data.map((d, i) => (
          <Bar
            key={d.name}
            x={i * spacing - totalWidth / 2}
            height={(d.value / maxValue) * MAX_BAR_HEIGHT}
            color={CATEGORICAL[i % CATEGORICAL.length]}
            name={d.name}
            value={d.value}
          />
        ))}
        <gridHelper args={[totalWidth + 4, 10, '#CBD5E1', '#E2E8F0']} />
        <OrbitControls enablePan={false} target={[0, 1.4, 0]} minDistance={4} maxDistance={18} maxPolarAngle={Math.PI / 2.1} />
      </Canvas>
    </div>
  );
}
