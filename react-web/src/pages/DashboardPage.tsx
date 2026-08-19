import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { DashboardSummary } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { useAuth } from '../context/AuthContext';
import { Card, StatCard } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';
import { Reveal } from '../components/Reveal';

// Fixed-order categorical palette (validated for CVD-safe adjacent contrast) — see dataviz skill.
const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];

function ChartCard({ title, data, dataKey, nameKey }: { title: string; data: Array<Record<string, string | number>>; dataKey: string; nameKey: string }) {
  return (
    <Card>
      <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 700 }}>{title}</h3>
      {data.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No data yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="0" stroke="#e1e0d9" vertical={false} />
            <XAxis dataKey={nameKey} tick={{ fontSize: 12, fill: '#898781' }} axisLine={{ stroke: '#c3c2b7' }} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#898781' }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: '1px solid var(--color-border)', fontSize: 13 }}
              cursor={{ fill: 'rgba(0,0,0,0.03)' }}
            />
            <Bar dataKey={dataKey} radius={[4, 4, 0, 0]} maxBarSize={24}>
              {data.map((_, i) => <Cell key={i} fill={CATEGORICAL[i % CATEGORICAL.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<DashboardSummary>(API_ENDPOINTS.dashboard)
      .then((res) => setSummary(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Welcome, {user?.full_name}</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginTop: 0, marginBottom: 24 }}>{user?.role}</p>

      {loading || !summary ? (
        <Card>Loading dashboard…</Card>
      ) : (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, overflowX: 'auto', overflowY: 'hidden', paddingBottom: 8, scrollBehavior: 'smooth' }}>
            {[
              { label: 'Orders', value: summary.counts.orders },
              { label: 'Revenue (Completed)', value: `₹${summary.total_revenue.toFixed(2)}`, accent: 'var(--color-success)' },
              { label: 'Products', value: summary.counts.products },
              { label: 'Low Stock', value: summary.counts.low_stock_products, accent: summary.counts.low_stock_products > 0 ? 'var(--color-warning)' : undefined },
              { label: 'Warehouses', value: summary.counts.warehouses },
              { label: 'Suppliers', value: summary.counts.suppliers },
              { label: 'Farmers', value: summary.counts.farmers },
              { label: 'Customers', value: summary.counts.customers },
            ].map((kpi, i) => (
              <Reveal key={kpi.label} delay={i * 60} style={{ flexShrink: 0 }}>
                <StatCard label={kpi.label} value={kpi.value} accent={kpi.accent} style={{ minWidth: 160 }} />
              </Reveal>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16, marginBottom: 24 }}>
            <Reveal delay={0}><ChartCard title="Orders by Status" data={summary.order_status_breakdown} dataKey="count" nameKey="status" /></Reveal>
            <Reveal delay={80}><ChartCard title="Inventory by Category" data={summary.inventory_by_category} dataKey="quantity" nameKey="category" /></Reveal>
            <Reveal delay={160}><ChartCard title="Stock by Warehouse" data={summary.stock_by_warehouse} dataKey="quantity" nameKey="warehouse" /></Reveal>
          </div>

          <Reveal>
            <Card>
              <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 700 }}>Recent Orders</h3>
              {summary.recent_orders.length === 0 ? (
                <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No orders yet.</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                  <thead>
                    <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)', fontSize: 12 }}>
                      <th style={{ padding: 8 }}>Customer</th>
                      <th style={{ padding: 8 }}>Status</th>
                      <th style={{ padding: 8 }}>Total</th>
                      <th style={{ padding: 8 }}>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.recent_orders.map((o) => (
                      <tr key={o.id} className="row-hover" style={{ borderTop: '1px solid var(--color-border)' }}>
                        <td style={{ padding: 8 }}>{o.customer_name}</td>
                        <td style={{ padding: 8 }}><StatusBadge status={o.status} /></td>
                        <td style={{ padding: 8 }}>₹{o.total_amount.toFixed(2)}</td>
                        <td style={{ padding: 8 }}>{o.order_date ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          </Reveal>
        </>
      )}
    </div>
  );
}
