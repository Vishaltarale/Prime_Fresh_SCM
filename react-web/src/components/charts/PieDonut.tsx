import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { NameValue } from '@shared/types';

// Same fixed-order categorical palette used on the Dashboard (CVD-safe adjacent contrast).
const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];

export function PieDonut({ data, donut = false }: { data: NameValue[]; donut?: boolean }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No data yet.</p>;
  }

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div style={{ position: 'relative' }}>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={donut ? 62 : 0}
            outerRadius={92}
            paddingAngle={data.length > 1 ? 2 : 0}
            strokeWidth={1}
          >
            {data.map((_, i) => <Cell key={i} fill={CATEGORICAL[i % CATEGORICAL.length]} />)}
          </Pie>
          <Tooltip
            contentStyle={{ borderRadius: 8, border: '1px solid var(--color-border)', fontSize: 13 }}
            formatter={(value, name) => [Number(value).toLocaleString(), name]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
      {donut && (
        <div
          style={{
            position: 'absolute',
            top: '44%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text)' }}>{total.toLocaleString()}</div>
          <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>Total</div>
        </div>
      )}
    </div>
  );
}
