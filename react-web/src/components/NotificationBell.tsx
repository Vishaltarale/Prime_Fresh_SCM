import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { AppNotification, NotificationList } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../lib/apiClient';

const POLL_INTERVAL_MS = 30_000;

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'var(--color-danger)',
  warning: 'var(--color-warning)',
  info: 'var(--color-primary)',
};

const CATEGORY_ICON: Record<string, string> = {
  low_stock: '📉',
  po_status: '📝',
  grn_status: '📦',
  payment_status: '💳',
  general: '🔔',
};

function timeAgo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

/** Route a notification click to the relevant screen, if it links to one. */
function targetPath(n: AppNotification): string | null {
  if (n.po_id) return `/purchase-orders/${n.po_id}`;
  if (n.grn_id) return `/grn/${n.grn_id}`;
  if (n.category === 'low_stock') return '/catalog/products';
  return null;
}

export function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<NotificationList>({ results: [], unread_count: 0 });
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    function load() {
      apiClient.get<NotificationList>(API_ENDPOINTS.notifications).then((res) => {
        if (!cancelled) setData(res.data);
      }).catch(() => {});
    }
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  function markRead(n: AppNotification) {
    if (n.is_read) return;
    apiClient.post(API_ENDPOINTS.notificationRead(n.id)).catch(() => {});
    setData((d) => ({
      unread_count: Math.max(0, d.unread_count - 1),
      results: d.results.map((r) => (r.id === n.id ? { ...r, is_read: true } : r)),
    }));
  }

  function markAllRead() {
    apiClient.post(API_ENDPOINTS.notificationsReadAll).catch(() => {});
    setData((d) => ({ unread_count: 0, results: d.results.map((r) => ({ ...r, is_read: true })) }));
  }

  function handleClick(n: AppNotification) {
    markRead(n);
    const path = targetPath(n);
    if (path) navigate(path);
    setOpen(false);
  }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className="btn-app"
        style={bellButtonStyle}
      >
        🔔
        {data.unread_count > 0 && (
          <span style={badgeStyle}>{data.unread_count > 99 ? '99+' : data.unread_count}</span>
        )}
      </button>

      {open && (
        <div className="dropdown-enter" style={panelStyle}>
          <div style={panelHeaderStyle}>
            <span style={{ fontWeight: 700, fontSize: 14 }}>Notifications</span>
            {data.unread_count > 0 && (
              <button onClick={markAllRead} style={markAllStyle}>Mark all read</button>
            )}
          </div>
          <div style={{ maxHeight: 380, overflowY: 'auto' }}>
            {data.results.length === 0 ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: 13 }}>
                No notifications yet.
              </div>
            ) : (
              data.results.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleClick(n)}
                  className="row-hover"
                  style={{
                    display: 'flex', gap: 10, padding: '12px 16px', cursor: 'pointer',
                    borderBottom: '1px solid var(--color-border)',
                    background: n.is_read ? 'transparent' : 'rgba(121, 134, 203, 0.06)',
                  }}
                >
                  <span style={{ fontSize: 18, flexShrink: 0 }}>{CATEGORY_ICON[n.category] ?? '🔔'}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: SEVERITY_COLOR[n.severity], flexShrink: 0 }} />
                      <span style={{ fontWeight: n.is_read ? 500 : 700, fontSize: 13 }}>{n.title}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>{n.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 4 }}>{timeAgo(n.created_at)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const bellButtonStyle: React.CSSProperties = {
  position: 'relative',
  background: 'transparent',
  border: 'none',
  fontSize: 20,
  lineHeight: 1,
  cursor: 'pointer',
  color: '#fff',
  padding: 6,
  borderRadius: 'var(--radius-md)',
};

const badgeStyle: React.CSSProperties = {
  position: 'absolute',
  top: -2,
  right: -2,
  minWidth: 16,
  height: 16,
  padding: '0 3px',
  borderRadius: 'var(--radius-pill)',
  background: 'var(--color-danger)',
  color: '#fff',
  fontSize: 10,
  fontWeight: 700,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  lineHeight: 1,
};

const panelStyle: React.CSSProperties = {
  position: 'absolute',
  top: '100%',
  right: 0,
  marginTop: 8,
  width: 360,
  maxWidth: '90vw',
  background: 'var(--color-surface)',
  color: 'var(--color-text)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-lg)',
  zIndex: 500,
  overflow: 'hidden',
  transformOrigin: 'top right',
};

const panelHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '12px 16px',
  borderBottom: '1px solid var(--color-border)',
};

const markAllStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'var(--color-primary)',
  fontSize: 12,
  fontWeight: 600,
  cursor: 'pointer',
};
