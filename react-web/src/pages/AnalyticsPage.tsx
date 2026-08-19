import { lazy, Suspense, useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LineChart, Line } from 'recharts';
import type { AnalyticsSummary } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { Card } from '../components/Card';
import { Reveal } from '../components/Reveal';
import { PieDonut } from '../components/charts/PieDonut';
import { Candlestick } from '../components/charts/Candlestick';

// Lazy-loaded: three.js/@react-three add ~900kB, and only this one chart
// needs it — code-splitting keeps it out of every other page's bundle.
const Bar3D = lazy(() => import('../components/charts/Bar3D').then((m) => ({ default: m.Bar3D })));

const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <Card>
      <h3 style={{ margin: '0 0 2px', fontSize: 15, fontWeight: 700 }}>{title}</h3>
      {subtitle && <p style={{ margin: '0 0 12px', fontSize: 12, color: 'var(--color-text-secondary)' }}>{subtitle}</p>}
      {!subtitle && <div style={{ marginBottom: 12 }} />}
      {children}
    </Card>
  );
}

function BarCard({ title, subtitle, data, valuePrefix }: { title: string; subtitle?: string; data: Array<{ name: string; value: number }>; valuePrefix?: string }) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      {data.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No data yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="0" stroke="#e1e0d9" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#898781' }} axisLine={{ stroke: '#c3c2b7' }} tickLine={false} interval={0} angle={-15} textAnchor="end" height={50} />
            <YAxis tick={{ fontSize: 12, fill: '#898781' }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: '1px solid var(--color-border)', fontSize: 13 }}
              formatter={(value) => {
                const n = Number(value);
                return [valuePrefix ? `${valuePrefix}${n.toLocaleString()}` : n.toLocaleString(), 'Value'];
              }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
              {data.map((_, i) => <Cell key={i} fill={CATEGORICAL[i % CATEGORICAL.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}

function TrendLine({ data }: { data: Array<{ month: string; close: number }> }) {
  if (data.length === 0) return null;
  return (
    <ResponsiveContainer width="100%" height={100}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <Line type="monotone" dataKey="close" stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 3 }} />
        <XAxis dataKey="month" hide />
        <YAxis hide domain={['dataMin - 1', 'dataMax + 1']} />
        <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid var(--color-border)', fontSize: 12 }} formatter={(v) => [`₹${Number(v).toLocaleString()}`, 'Close']} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<AnalyticsSummary>(API_ENDPOINTS.analytics)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return (
      <div>
        <h1 style={{ fontSize: 24, marginBottom: 20 }}>Analytics</h1>
        <Card>Loading analytics…</Card>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Analytics</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginTop: 0, marginBottom: 24 }}>
        Live aggregates across orders, purchase orders, stock, and payments.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16, marginBottom: 16 }}>
        <Reveal delay={0}>
          <ChartCard title="Order Status" subtitle="Pie — share of orders by current status">
            <PieDonut data={data.order_status_distribution} />
          </ChartCard>
        </Reveal>
        <Reveal delay={60}>
          <ChartCard title="Supplier Payment Status" subtitle="Donut — value owed, by payment state">
            <PieDonut data={data.payment_status_distribution} donut />
          </ChartCard>
        </Reveal>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16, marginBottom: 16 }}>
        <Reveal delay={0}>
          <BarCard title="Stock by Category" data={data.category_stock_distribution} />
        </Reveal>
        <Reveal delay={60}>
          <ChartCard title="Stock by Warehouse — 3D" subtitle="Drag to orbit, scroll to zoom">
            <Suspense fallback={<p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>Loading 3D view…</p>}>
              <Bar3D data={data.warehouse_stock_distribution} />
            </Suspense>
          </ChartCard>
        </Reveal>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 16, marginBottom: 16 }}>
        <Reveal delay={0}>
          <ChartCard title="Sales Trend" subtitle="Candlestick — monthly order-value spread (open/high/low/close)">
            <Candlestick data={data.sales_candles} />
            <div style={{ marginTop: 8 }}>
              <TrendLine data={data.sales_candles} />
            </div>
          </ChartCard>
        </Reveal>
        <Reveal delay={60}>
          <ChartCard title="Purchase Order Value Trend" subtitle="Candlestick — monthly proposed PO value spread">
            <Candlestick data={data.purchase_order_candles} />
            <div style={{ marginTop: 8 }}>
              <TrendLine data={data.purchase_order_candles} />
            </div>
          </ChartCard>
        </Reveal>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16, marginBottom: 16 }}>
        <Reveal delay={0}>
          <BarCard title="Top Products by Stock Value" data={data.top_products_by_value} valuePrefix="₹" />
        </Reveal>
        <Reveal delay={60}>
          <BarCard
            title="Supplier Spend"
            subtitle="Total ₹ paid per supplier — summed from confirmed GRN receipts, not current stock"
            data={data.supplier_spend_distribution}
            valuePrefix="₹"
          />
        </Reveal>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16 }}>
        <Reveal delay={0}>
          <BarCard
            title="Stock Purchased by Supplier"
            subtitle="Total units received per supplier, across all confirmed GRNs"
            data={data.supplier_qty_distribution}
          />
        </Reveal>
      </div>
    </div>
  );
}
