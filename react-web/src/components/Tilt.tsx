import { useRef, useState, type CSSProperties, type ReactNode } from 'react';

interface TiltProps {
  children: ReactNode;
  style?: CSSProperties;
  /** Max rotation in degrees at the edge of the element. */
  maxTilt?: number;
  className?: string;
}

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

const hasHover = () => typeof window !== 'undefined' && window.matchMedia?.('(hover: hover)').matches;

/** Wraps children in a perspective container and tilts them toward the cursor on hover — skipped for touch devices and reduced-motion users. */
export function Tilt({ children, style, maxTilt = 8, className }: TiltProps) {
  const innerRef = useRef<HTMLDivElement>(null);
  const [tilting, setTilting] = useState(false);
  const enabled = hasHover() && !prefersReducedMotion();

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (!enabled || !innerRef.current) return;
    const rect = innerRef.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    const rotateY = (px - 0.5) * maxTilt * 2;
    const rotateX = (0.5 - py) * maxTilt * 2;
    innerRef.current.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(6px) scale(1.015)`;
  }

  function handleMouseLeave() {
    if (!innerRef.current) return;
    setTilting(false);
    innerRef.current.style.transform = 'rotateX(0deg) rotateY(0deg) translateZ(0) scale(1)';
  }

  return (
    <div
      className={`tilt-wrap ${className ?? ''}`}
      style={style}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setTilting(true)}
      onMouseLeave={handleMouseLeave}
    >
      <div ref={innerRef} className={`tilt-inner ${tilting ? 'tilting' : ''}`}>
        {children}
      </div>
    </div>
  );
}
