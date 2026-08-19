export interface RingPoint {
  idx: number;
  position: [number, number, number];
  color: string;
}

// Prime Fresh SCM brand palette — purples/indigo with a cyan accent, matching
// --color-primary / --color-primary-dark / --color-accent in src/index.css.
const PALETTE = ['#8B5CF6', '#6D28D9', '#4C1D95', '#A78BFA', '#4F46E5', '#06B6D4'];

function randomColor(): string {
  return PALETTE[Math.floor(Math.random() * PALETTE.length)];
}

function generateRing(count: number, radius: number, spread: number, startIdx: number): RingPoint[] {
  const points: RingPoint[] = [];
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2;
    const r = radius + (Math.random() - 0.5) * spread;
    const x = Math.cos(angle) * r;
    const y = Math.sin(angle) * r;
    const z = (Math.random() - 0.5) * spread;
    points.push({ idx: startIdx + i, position: [x, y, z], color: randomColor() });
  }
  return points;
}

export const pointsInner: RingPoint[] = generateRing(60, 4, 1.4, 0);
export const pointsOuter: RingPoint[] = generateRing(120, 7.5, 2, pointsInner.length);
