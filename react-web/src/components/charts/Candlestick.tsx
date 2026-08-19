import { useState } from 'react';
import type { Candle } from '@shared/types';

const UP_COLOR = '#16A34A';
const DOWN_COLOR = '#DC2626';
const HEIGHT = 240;
const PADDING = { top: 16, right: 16, bottom: 28, left: 56 };

/**
 * Self-contained OHLC candlestick — recharts has no native candlestick type,
 * and coercing its Bar/Composed API into drawing wick+body pairs from
 * arbitrary (open, high, low, close) values fights the library more than it
 * helps for ~12 points, so this renders plain SVG directly.
 */
export function Candlestick({ data }: { data: Candle[] }) {
  const [hover, setHover] = useState<number | null>(null);

  if (data.length === 0) {
    return <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No data yet.</p>;
  }

  const width = Math.max(data.length * 70, 320);
  const plotWidth = width - PADDING.left - PADDING.right;
  const plotHeight = HEIGHT - PADDING.top - PADDING.bottom;

  const maxHigh = Math.max(...data.map((d) => d.high));
  const minLow = Math.min(...data.map((d) => d.low));
  const span = maxHigh - minLow || 1;
  const domainTop = maxHigh + span * 0.1;
  const domainBottom = Math.max(0, minLow - span * 0.1);
  const domainSpan = domainTop - domainBottom || 1;

  const y = (value: number) => PADDING.top + plotHeight * (1 - (value - domainBottom) / domainSpan);
  const slotWidth = plotWidth / data.length;
  const bodyWidth = Math.min(28, slotWidth * 0.5);

  const ticks = 4;
  const gridValues = Array.from({ length: ticks + 1 }, (_, i) => domainBottom + (domainSpan * i) / ticks);

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg width={width} height={HEIGHT} role="img" aria-label="Candlestick chart">
        {gridValues.map((v, i) => (
          <g key={i}>
            <line x1={PADDING.left} x2={width - PADDING.right} y1={y(v)} y2={y(v)} stroke="var(--color-border)" strokeDasharray="2 3" />
            <text x={PADDING.left - 8} y={y(v)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill="var(--color-text-secondary)">
              {v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v.toFixed(0)}
            </text>
          </g>
        ))}

        {data.map((d, i) => {
          const cx = PADDING.left + slotWidth * i + slotWidth / 2;
          const up = d.close >= d.open;
          const color = up ? UP_COLOR : DOWN_COLOR;
          const bodyTop = y(Math.max(d.open, d.close));
          const bodyBottom = y(Math.min(d.open, d.close));
          const isHover = hover === i;
          return (
            <g
              key={d.month}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              style={{ cursor: 'pointer' }}
            >
              <line x1={cx} x2={cx} y1={y(d.high)} y2={y(d.low)} stroke={color} strokeWidth={isHover ? 2 : 1.5} />
              <rect
                x={cx - bodyWidth / 2}
                y={bodyTop}
                width={bodyWidth}
                height={Math.max(2, bodyBottom - bodyTop)}
                fill={color}
                opacity={isHover ? 1 : 0.85}
                rx={2}
              />
              <text x={cx} y={HEIGHT - 8} textAnchor="middle" fontSize={11} fill="var(--color-text-secondary)">
                {d.month}
              </text>
            </g>
          );
        })}
      </svg>

      {hover !== null && (
        <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', paddingLeft: PADDING.left }}>
          <strong style={{ color: 'var(--color-text)' }}>{data[hover].month}</strong>
          {'  '}Open ₹{data[hover].open.toLocaleString()} · High ₹{data[hover].high.toLocaleString()} · Low ₹{data[hover].low.toLocaleString()} · Close ₹{data[hover].close.toLocaleString()}
          {'  '}({data[hover].count} order{data[hover].count === 1 ? '' : 's'})
        </div>
      )}
    </div>
  );
}
